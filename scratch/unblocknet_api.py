#!/usr/bin/env python3
"""
unblocknet_api.py - Unblocknet Server API v2 (accounts, anti-abuse, billing, notifications).
Runs on VPS as teletok-api.service (port 2096). Deployed to /usr/local/bin/teletok_server_api.py

Key properties:
- Every user has a personal VLESS client in 3X-UI (created via panel API, no x-ui restarts).
- Device identity = salted hardware fingerprint (MachineGuid / SMBIOS UUID / system disk serial);
  fuzzy match (>= 2 of 3 strong components) survives app reinstall, cache wipes and Windows reinstall.
- Trial is granted once per account AND once per hardware AND max N per IP per week.
- Device limit is enforced server-side (devices are linked to an account only via one-time codes).
- All requests are authorised by a per-device bearer token; client-supplied IDs are never trusted.
- YooMoney webhook: signature check, operation_id de-duplication, amount check, order lookup.
- Owner / admin list and all secrets live only on the server (/etc/teletok/*.env|json, chmod 600).
- E-mail notifications via smtp.yandex.ru through the local Cloudflare WARP SOCKS5 proxy
  (the hosting provider blocks outbound SMTP ports).

Admin CLI:  unblocknet-admin code --owner | code --days 30 | users | stats | ban <id> | unban <id> | mailtest
"""

import os
import sys
import json
import time
import re
import ssl
import socket
import struct
import queue
import sqlite3
import hashlib
import hmac
import secrets
import smtplib
import threading
import subprocess
import tempfile
import traceback
import urllib.parse
import urllib.request
import http.cookiejar
import uuid as uuidlib
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PORT = 2096
DATA_DIR = "/etc/teletok"
DB_FILE = os.path.join(DATA_DIR, "teletok.db")
SECRETS_FILE = os.path.join(DATA_DIR, "secrets.env")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
SERVER_CFG_FILE = os.path.join(DATA_DIR, "server_config.json")
OUTBOX_FILE = os.path.join(DATA_DIR, "outbox.jsonl")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
XUI_DB = "/etc/x-ui/x-ui.db"
XRAY_DIR = "/usr/local/x-ui/bin"
XRAY_BIN = os.path.join(XRAY_DIR, "xray-linux-amd64")
MSK_OFFSET = 3 * 3600
DAY_MS = 86400 * 1000

TRIAL_DAYS = 3
TRIALS_PER_IP_WEEK = 3
UNBIND_COOLDOWN_S = 7 * 86400
CODE_TTL_S = 15 * 60
COMMON_COMPONENT_ACCOUNTS = 5   # a hw component seen on >= N accounts is treated as non-unique

PLANS = {
    "trial_3d": {"name": "Тестовый (3 дня)", "days": 3, "price": 0, "limit_ip": 3, "desc": "3 дня бесплатно • До 3 устройств"},
    "1m": {"name": "1 месяц", "days": 30, "price": 149, "limit_ip": 3, "desc": "149 ₽/мес • Базовый доступ на 30 дней"},
    "3m": {"name": "3 месяца", "days": 90, "price": 390, "limit_ip": 3, "desc": "130 ₽/мес • Скидка 13% • До 3 устройств"},
    "6m": {"name": "6 месяцев", "days": 180, "price": 690, "limit_ip": 3, "desc": "115 ₽/мес • Скидка 23% • До 3 устройств"},
    "1y": {"name": "1 год", "days": 365, "price": 1190, "limit_ip": 3, "desc": "99 ₽/мес • Скидка 33% • Хит 🔥 • До 3 устройств"},
    "family_1y": {"name": "Семейный (1 год)", "days": 365, "price": 1990, "limit_ip": 6, "desc": "165 ₽/мес • До 6 устройств для всей семьи 👨‍👩‍👧‍👦"},
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Config / secrets
# ---------------------------------------------------------------------------
def load_env():
    res = {}
    try:
        with open(SECRETS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                res[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return res


ENV = load_env()


def env(key, default=""):
    return ENV.get(key) or os.environ.get(key) or default


def load_admins():
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"owner_xui_emails": []}


def load_server_config():
    try:
        with open(SERVER_CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"nodes": {}, "custom_proxy_domains": [], "custom_direct_domains": [], "adblock_domains": [], "adblock_enabled": True}


def save_server_config(cfg):
    tmp = SERVER_CFG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, SERVER_CFG_FILE)


def public_server_config():
    """Server config without any credentials (UUIDs are personal and come from /api/me)."""
    cfg = json.loads(json.dumps(load_server_config()))
    for node in (cfg.get("nodes") or {}).values():
        node.pop("uuid", None)
    return cfg


def now_ms():
    return int(time.time() * 1000)


def fmt_date(ms):
    return time.strftime("%d.%m.%Y", time.gmtime(ms / 1000 + MSK_OFFSET))


def fmt_dt(ts):
    return time.strftime("%d.%m.%Y %H:%M", time.gmtime(ts + MSK_OFFSET)) + " МСК"


def log(*args):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    xui_email TEXT UNIQUE,
    uuid TEXT,
    sub_id TEXT,
    created_at INTEGER NOT NULL,
    expiry_ms INTEGER NOT NULL DEFAULT 0,
    device_limit INTEGER NOT NULL DEFAULT 3,
    plan TEXT,
    trial_used INTEGER NOT NULL DEFAULT 0,
    is_owner INTEGER NOT NULL DEFAULT 0,
    banned INTEGER NOT NULL DEFAULT 0,
    last_unbind_at INTEGER NOT NULL DEFAULT 0,
    note TEXT
);
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE,
    hw_mg TEXT, hw_bios TEXT, hw_disk TEXT, hw_cpu TEXT,
    name TEXT,
    app_version TEXT,
    created_at INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    last_ip TEXT
);
CREATE INDEX IF NOT EXISTS idx_dev_mg ON devices(hw_mg);
CREATE INDEX IF NOT EXISTS idx_dev_bios ON devices(hw_bios);
CREATE INDEX IF NOT EXISTS idx_dev_disk ON devices(hw_disk);
CREATE INDEX IF NOT EXISTS idx_dev_acc ON devices(account_id);
CREATE TABLE IF NOT EXISTS trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    device_id INTEGER,
    hw_mg TEXT, hw_bios TEXT, hw_disk TEXT,
    ip TEXT,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    account_id INTEGER NOT NULL,
    plan_id TEXT NOT NULL,
    price INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    operation_id TEXT
);
CREATE TABLE IF NOT EXISTS payments (
    operation_id TEXT PRIMARY KEY,
    order_id TEXT,
    account_id INTEGER,
    plan_id TEXT,
    amount TEXT,
    withdraw_amount TEXT,
    status TEXT,
    raw TEXT,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS codes (
    code TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    account_id INTEGER,
    days INTEGER,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    used_by_device INTEGER,
    used_at INTEGER
);
"""

DB_LOCK = threading.RLock()


def db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with DB_LOCK:
        conn = db()
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
    try:
        os.chmod(DB_FILE, 0o600)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 3X-UI panel API client (hot-applies users, no x-ui restarts)
# ---------------------------------------------------------------------------
class PanelError(Exception):
    pass


class Panel:
    def __init__(self):
        self.lock = threading.Lock()
        self.opener = None
        self.csrf = None

    @property
    def base(self):
        return env("PANEL_URL").rstrip("/")

    def _raw(self, path, data=None):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": re.match(r"^(https?://[^/]+)", self.base).group(1),
            "Referer": self.base + "/",
        }
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(self.base + path, data=body, headers=headers)
        with self.opener.open(req, timeout=15) as resp:
            return resp.read().decode("utf-8", "replace")

    def _login(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )
        self.csrf = None
        html = self._raw("/")
        m = re.search(r'name="csrf-token" content="([^"]+)"', html)
        self.csrf = m.group(1) if m else None
        res = json.loads(self._raw("/login", {"username": env("PANEL_USER"), "password": env("PANEL_PASS")}))
        if not res.get("success"):
            raise PanelError("panel login failed")
        html = self._raw("/panel/")
        m = re.search(r'name="csrf-token" content="([^"]+)"', html)
        if m:
            self.csrf = m.group(1)

    def call(self, path, data=None):
        with self.lock:
            for attempt in range(2):
                try:
                    if self.opener is None:
                        self._login()
                    txt = self._raw(path, data)
                    return json.loads(txt)
                except (urllib.error.HTTPError, json.JSONDecodeError, PanelError) as e:
                    self.opener = None
                    if attempt == 1:
                        raise PanelError(f"panel call {path} failed: {e}")
                except Exception as e:
                    self.opener = None
                    if attempt == 1:
                        raise PanelError(f"panel call {path} failed: {e}")
        raise PanelError("unreachable")

    def inbound_ids(self):
        return [int(x) for x in env("INBOUND_IDS", "1,2").split(",") if x.strip()]

    def get(self, email):
        res = self.call("/panel/api/clients/get/" + urllib.parse.quote(email))
        if not res.get("success") or not res.get("obj"):
            return None, None
        return res["obj"].get("client"), res["obj"].get("inboundIds") or self.inbound_ids()

    def add(self, email, uuid, sub_id, expiry_ms, limit_ip, comment=""):
        client = {
            "email": email, "uuid": uuid, "subId": sub_id, "flow": "xtls-rprx-vision",
            "enable": True, "expiryTime": int(expiry_ms), "limitIp": int(limit_ip),
            "totalGB": 0, "comment": comment,
        }
        res = self.call("/panel/api/clients/add", {"client": client, "inboundIds": self.inbound_ids()})
        if not res.get("success"):
            raise PanelError("add failed: " + str(res.get("msg")))

    def update(self, email, **fields):
        cur, inbound_ids = self.get(email)
        if not cur:
            raise PanelError("client not found: " + email)
        body = dict(cur)
        body.update(fields)
        body["inboundIds"] = inbound_ids
        res = self.call("/panel/api/clients/update/" + urllib.parse.quote(email), body)
        if not res.get("success"):
            raise PanelError("update failed: " + str(res.get("msg")))

    def restart_xray(self):
        return self.call("/panel/api/server/restartXrayService", {})


PANEL = Panel()


def gen_sub_id():
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(16))


def ensure_xui_client(conn, acc, expiry_ms, limit_ip):
    """Creates or updates the personal 3X-UI client of an account."""
    if acc["is_owner"]:
        return
    if not acc["xui_email"]:
        email = f"u{acc['id']}_{secrets.token_hex(2)}"
        uid = str(uuidlib.uuid4())
        sub_id = gen_sub_id()
        PANEL.add(email, uid, sub_id, expiry_ms, limit_ip, comment=f"unblocknet account {acc['id']}")
        conn.execute("UPDATE accounts SET xui_email=?, uuid=?, sub_id=? WHERE id=?", (email, uid, sub_id, acc["id"]))
    else:
        PANEL.update(acc["xui_email"], expiryTime=int(expiry_ms), limitIp=int(limit_ip), enable=True)


# ---------------------------------------------------------------------------
# Notifications (SMTP over WARP SOCKS5)
# ---------------------------------------------------------------------------
def socks5_connect(host, port, timeout=20):
    px_host, px_port = env("SMTP_SOCKS", "127.0.0.1:40000").split(":")
    s = socket.create_connection((px_host, int(px_port)), timeout=timeout)
    s.sendall(b"\x05\x01\x00")
    if s.recv(2) != b"\x05\x00":
        raise OSError("socks5 auth failed")
    hb = host.encode()
    s.sendall(b"\x05\x01\x00\x03" + bytes([len(hb)]) + hb + struct.pack(">H", port))
    rep = s.recv(4)
    if len(rep) < 2 or rep[1] != 0:
        raise OSError(f"socks5 connect failed: {rep!r}")
    atyp = rep[3]
    if atyp == 1:
        s.recv(6)
    elif atyp == 3:
        s.recv(s.recv(1)[0] + 2)
    elif atyp == 4:
        s.recv(18)
    return s


class WarpSMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        raw = socks5_connect(host, port, timeout or 20)
        return self.context.wrap_socket(raw, server_hostname=host)


def smtp_send(subject, body):
    user, pwd, to = env("SMTP_USER"), env("SMTP_PASS"), env("NOTIFY_EMAIL")
    if not (user and pwd and to):
        raise RuntimeError("SMTP credentials are not configured (SMTP_PASS is empty)")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("Unblocknet", "utf-8")), user))
    msg["To"] = to
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = make_msgid(domain="unblocknet.local")
    with WarpSMTP_SSL(env("SMTP_HOST", "smtp.yandex.ru"), int(env("SMTP_PORT", "465")), timeout=30,
                      context=ssl.create_default_context()) as s:
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())


MAIL_Q = queue.Queue()


def notify(subject, body):
    MAIL_Q.put((subject, body, time.time()))


def _outbox_append(subject, body, ts, err):
    with open(OUTBOX_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"subject": subject, "body": body, "ts": ts, "err": str(err)}, ensure_ascii=False) + "\n")


def mail_worker():
    while True:
        subject, body, ts = MAIL_Q.get()
        err = None
        for attempt in range(3):
            try:
                smtp_send(subject, body)
                log("MAIL SENT:", subject)
                err = None
                break
            except Exception as e:
                err = e
                if "not configured" in str(e):
                    break
                time.sleep(5 * (attempt + 1))
        if err:
            log("MAIL FAILED -> outbox:", subject, err)
            _outbox_append(subject, body, ts, err)


def flush_outbox():
    if not os.path.exists(OUTBOX_FILE) or not env("SMTP_PASS"):
        return
    try:
        with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
            items = [json.loads(l) for l in f if l.strip()]
    except Exception:
        return
    remaining = []
    for it in items:
        try:
            smtp_send(it["subject"] + " (отложено)", it["body"])
        except Exception:
            remaining.append(it)
    with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
        for it in remaining:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f)


def build_stats_text(since_ts):
    conn = db()
    trials = conn.execute("SELECT t.*, a.xui_email FROM trials t JOIN accounts a ON a.id=t.account_id WHERE t.created_at>=? ORDER BY t.created_at",
                          (since_ts,)).fetchall()
    pays = conn.execute("SELECT * FROM payments WHERE created_at>=? AND status='success' ORDER BY created_at", (since_ts,)).fetchall()
    total_active = conn.execute("SELECT COUNT(*) FROM accounts WHERE expiry_ms>? AND banned=0 AND is_owner=0", (now_ms(),)).fetchone()[0]
    total_paid = conn.execute("SELECT COUNT(DISTINCT account_id) FROM payments WHERE status='success'").fetchone()[0]
    month_start = time.time() - 30 * 86400
    month_sum = sum(float(p["withdraw_amount"] or p["amount"] or 0) for p in
                    conn.execute("SELECT * FROM payments WHERE created_at>=? AND status='success'", (month_start,)).fetchall())
    conn.close()
    lines = [f"Новых триалов: {len(trials)}"]
    for t in trials:
        lines.append(f"  • {fmt_dt(t['created_at'])}  аккаунт #{t['account_id']}  IP {t['ip']}")
    lines.append("")
    lines.append(f"Оплат: {len(pays)} на сумму {sum(float(p['withdraw_amount'] or p['amount'] or 0) for p in pays):.0f} ₽")
    for p in pays:
        lines.append(f"  • {fmt_dt(p['created_at'])}  аккаунт #{p['account_id']}  {PLANS.get(p['plan_id'], {}).get('name', p['plan_id'])}  {p['withdraw_amount'] or p['amount']} ₽")
    lines.append("")
    lines.append(f"Активных подписок сейчас: {total_active}")
    lines.append(f"Всего платящих клиентов: {total_paid}")
    lines.append(f"Выручка за 30 дней: {month_sum:.0f} ₽")
    return "\n".join(lines)


def scheduler_worker():
    """Daily digest at 09:00 MSK + outbox retries."""
    last_flush = 0
    while True:
        try:
            st = load_state()
            msk = time.gmtime(time.time() + MSK_OFFSET)
            today = time.strftime("%Y-%m-%d", msk)
            if msk.tm_hour >= 9 and st.get("last_digest") != today:
                since = st.get("last_digest_ts") or (time.time() - 86400)
                notify(f"Unblocknet: сводка за сутки ({today})", build_stats_text(since))
                st["last_digest"] = today
                st["last_digest_ts"] = time.time()
                save_state(st)
            if time.time() - last_flush > 600:
                last_flush = time.time()
                flush_outbox()
        except Exception as e:
            log("scheduler error:", e)
        time.sleep(60)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATE_LIMITS = {
    "register": (30, 3600),
    "trial": (6, 3600),
    "activate": (10, 3600),
    "payment": (30, 3600),
    "link": (20, 3600),
    "me": (600, 3600),
    "unbind": (20, 3600),
    "admin": (60, 3600),
}
_rate = defaultdict(deque)
_rate_lock = threading.Lock()


def rate_ok(ip, action):
    limit, window = RATE_LIMITS.get(action, (120, 3600))
    now = time.time()
    with _rate_lock:
        dq = _rate[(ip, action)]
        while dq and dq[0] < now - window:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------
class ApiError(Exception):
    def __init__(self, code, message, http=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http = http


def hash_token(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def common_components(conn):
    """Hardware hashes that appear on many different accounts (junk BIOS UUIDs, cloned images)."""
    res = set()
    for col in ("hw_mg", "hw_bios", "hw_disk"):
        for row in conn.execute(f"SELECT {col} AS h, COUNT(DISTINCT account_id) AS n FROM devices WHERE {col}!='' GROUP BY {col} HAVING n>=?",
                                (COMMON_COMPONENT_ACCOUNTS,)):
            res.add(row["h"])
    return res


def hw_matches(a, b, common):
    n = 0
    for col in ("hw_mg", "hw_bios", "hw_disk"):
        va, vb = a.get(col) or "", b[col] or ""
        if va and va == vb and va not in common:
            n += 1
    return n


def find_device_by_hw(conn, hw):
    common = common_components(conn)
    cands = conn.execute(
        "SELECT * FROM devices WHERE (hw_mg=? AND hw_mg!='') OR (hw_bios=? AND hw_bios!='') OR (hw_disk=? AND hw_disk!='')",
        (hw["hw_mg"], hw["hw_bios"], hw["hw_disk"])).fetchall()
    best, best_n = None, 0
    for d in cands:
        n = hw_matches(hw, d, common)
        if n >= 2 and (n > best_n or (n == best_n and d["last_seen"] > best["last_seen"])):
            best, best_n = d, n
    return best


def parse_hw(payload):
    hw_in = payload.get("hw") or {}
    hw = {}
    for key, col in (("mg", "hw_mg"), ("bios", "hw_bios"), ("disk", "hw_disk"), ("cpu", "hw_cpu")):
        v = str(hw_in.get(key) or "").lower()
        hw[col] = v if HEX64.match(v) else ""
    if sum(1 for c in ("hw_mg", "hw_bios", "hw_disk") if hw[c]) < 2:
        raise ApiError("bad_hw", "Не удалось определить устройство. Обновите приложение.", 400)
    return hw


def get_account(conn, acc_id):
    return conn.execute("SELECT * FROM accounts WHERE id=?", (acc_id,)).fetchone()


def subscription_info(acc):
    nm = now_ms()
    if acc["is_owner"]:
        return {"is_active": True, "is_unlimited": True, "days_left": 9999, "expiry_time": 0,
                "expiry_date": "Безлимитно", "limit_ip": 0, "plan": "owner", "status": "active"}
    exp = acc["expiry_ms"] or 0
    active = bool(acc["xui_email"]) and exp > nm and not acc["banned"]
    return {
        "is_active": active,
        "is_unlimited": False,
        "days_left": max(0, int((exp - nm) / DAY_MS + 0.999)) if exp > nm else 0,
        "expiry_time": exp,
        "expiry_date": fmt_date(exp) if exp else "--",
        "limit_ip": acc["device_limit"],
        "plan": acc["plan"] or "",
        "status": "active" if active else ("banned" if acc["banned"] else "expired"),
    }


def personal_node(acc):
    if not acc["uuid"]:
        return None
    cfg = load_server_config()
    nodes = cfg.get("nodes") or {}
    base = nodes.get("443-ff") or next(iter(nodes.values()), {})
    return {
        "uuid": acc["uuid"],
        "flow": base.get("flow", "xtls-rprx-vision"),
        "pbk": base.get("pbk", ""),
        "sid": base.get("sid", ""),
        "vps_host": base.get("vps_host", ""),
    }


def me_payload(conn, acc, device_id):
    sub = subscription_info(acc)
    devices = []
    for d in conn.execute("SELECT * FROM devices WHERE account_id=? ORDER BY created_at", (acc["id"],)):
        devices.append({"id": d["id"], "name": d["name"] or "Компьютер", "created": fmt_date(d["created_at"] * 1000),
                        "last_seen": fmt_dt(d["last_seen"]), "is_current": d["id"] == device_id})
    trial_available = (not acc["trial_used"]) and not sub["is_active"] and not acc["is_owner"]
    unbind_at = (acc["last_unbind_at"] or 0) + UNBIND_COOLDOWN_S
    res = {
        "status": "ok",
        "account_id": acc["id"],
        "is_owner": bool(acc["is_owner"]),
        "subscription": dict(sub, trial_available=trial_available, trial_used=bool(acc["trial_used"])),
        "devices": devices,
        "device_limit": 0 if acc["is_owner"] else acc["device_limit"],
        "can_unbind": bool(acc["is_owner"]) or time.time() >= unbind_at,
        "unbind_available_at": "" if acc["is_owner"] or time.time() >= unbind_at else fmt_dt(unbind_at),
        "plans": PLANS,
        "node": personal_node(acc) if sub["is_active"] else None,
        "sub_url": "",
    }
    if sub["is_active"] and acc["sub_id"] and env("SUB_BASE"):
        res["sub_url"] = env("SUB_BASE").rstrip("/") + "/" + acc["sub_id"]
    return res


def owner_account(conn):
    return conn.execute("SELECT * FROM accounts WHERE is_owner=1 ORDER BY id LIMIT 1").fetchone()


def do_register(payload, ip):
    hw = parse_hw(payload)
    name = str(payload.get("name") or "")[:40]
    version = str(payload.get("version") or "")[:20]
    tok = secrets.token_urlsafe(32)
    ts = int(time.time())
    with DB_LOCK:
        conn = db()
        try:
            dev = find_device_by_hw(conn, hw)
            if dev:
                conn.execute("UPDATE devices SET token_hash=?, hw_mg=COALESCE(NULLIF(?,''),hw_mg), hw_bios=COALESCE(NULLIF(?,''),hw_bios), "
                             "hw_disk=COALESCE(NULLIF(?,''),hw_disk), hw_cpu=?, name=?, app_version=?, last_seen=?, last_ip=? WHERE id=?",
                             (hash_token(tok), hw["hw_mg"], hw["hw_bios"], hw["hw_disk"], hw["hw_cpu"], name, version, ts, ip, dev["id"]))
                device_id, acc_id = dev["id"], dev["account_id"]
                log(f"REGISTER existing device #{device_id} account #{acc_id} ip={ip}")
            else:
                cur = conn.execute("INSERT INTO accounts (created_at, device_limit) VALUES (?, 3)", (ts,))
                acc_id = cur.lastrowid
                cur = conn.execute("INSERT INTO devices (account_id, token_hash, hw_mg, hw_bios, hw_disk, hw_cpu, name, app_version, created_at, last_seen, last_ip) "
                                   "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                   (acc_id, hash_token(tok), hw["hw_mg"], hw["hw_bios"], hw["hw_disk"], hw["hw_cpu"], name, version, ts, ts, ip))
                device_id = cur.lastrowid
                log(f"REGISTER new device #{device_id} account #{acc_id} ip={ip}")
            conn.commit()
            acc = get_account(conn, acc_id)
            res = me_payload(conn, acc, device_id)
            res["token"] = tok
            return res
        finally:
            conn.close()


def auth_device(conn, headers):
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise ApiError("unauthorized", "Требуется авторизация устройства", 401)
    dev = conn.execute("SELECT * FROM devices WHERE token_hash=?", (hash_token(auth[7:].strip()),)).fetchone()
    if not dev:
        raise ApiError("unauthorized", "Устройство не найдено, требуется повторная регистрация", 401)
    acc = get_account(conn, dev["account_id"])
    if not acc:
        raise ApiError("unauthorized", "Аккаунт не найден", 401)
    if acc["banned"]:
        raise ApiError("banned", "Аккаунт заблокирован за нарушение правил", 403)
    return dev, acc


def touch_device(conn, dev, ip):
    ts = int(time.time())
    if ts - (dev["last_seen"] or 0) > 60 or dev["last_ip"] != ip:
        conn.execute("UPDATE devices SET last_seen=?, last_ip=? WHERE id=?", (ts, ip, dev["id"]))
        conn.commit()


def do_trial(dev, acc, ip):
    with DB_LOCK:
        conn = db()
        try:
            acc = get_account(conn, acc["id"])
            if acc["is_owner"]:
                return me_payload(conn, acc, dev["id"])
            if subscription_info(acc)["is_active"]:
                raise ApiError("already_active", "Подписка уже активна", 400)
            if acc["trial_used"]:
                raise ApiError("trial_used", "Пробный период уже был использован. Выберите тариф во вкладке «Тарифы».", 403)
            common = common_components(conn)
            hw = {"hw_mg": dev["hw_mg"], "hw_bios": dev["hw_bios"], "hw_disk": dev["hw_disk"]}
            for t in conn.execute("SELECT * FROM trials WHERE device_id=? OR (hw_mg=? AND hw_mg!='') OR (hw_bios=? AND hw_bios!='') OR (hw_disk=? AND hw_disk!='')",
                                  (dev["id"], dev["hw_mg"], dev["hw_bios"], dev["hw_disk"])):
                if t["device_id"] == dev["id"] or hw_matches(hw, t, common) >= 2:
                    conn.execute("UPDATE accounts SET trial_used=1 WHERE id=?", (acc["id"],))
                    conn.commit()
                    raise ApiError("trial_used_hw", "Пробный период уже использован на этом компьютере. Выберите тариф во вкладке «Тарифы».", 403)
            week = int(time.time()) - 7 * 86400
            n_ip = conn.execute("SELECT COUNT(*) FROM trials WHERE ip=? AND created_at>=?", (ip, week)).fetchone()[0]
            if n_ip >= TRIALS_PER_IP_WEEK:
                raise ApiError("trial_ip_limit", "С вашей сети уже активировано слишком много пробных периодов. Выберите тариф.", 429)

            expiry = now_ms() + TRIAL_DAYS * DAY_MS
            ensure_xui_client(conn, acc, expiry, PLANS["trial_3d"]["limit_ip"])
            conn.execute("UPDATE accounts SET trial_used=1, expiry_ms=?, plan='trial_3d', device_limit=MAX(device_limit, 3) WHERE id=?",
                         (expiry, acc["id"]))
            conn.execute("INSERT INTO trials (account_id, device_id, hw_mg, hw_bios, hw_disk, ip, created_at) VALUES (?,?,?,?,?,?,?)",
                         (acc["id"], dev["id"], dev["hw_mg"], dev["hw_bios"], dev["hw_disk"], ip, int(time.time())))
            conn.commit()
            log(f"TRIAL granted account #{acc['id']} device #{dev['id']} ip={ip}")
            acc = get_account(conn, acc["id"])
            res = me_payload(conn, acc, dev["id"])
            res["message"] = f"Пробный период активирован до {fmt_date(expiry)}"
            return res
        finally:
            conn.close()


def do_payment_create(dev, acc, payload):
    plan_id = str(payload.get("plan_id") or "").strip()
    if plan_id not in PLANS or plan_id == "trial_3d":
        raise ApiError("bad_plan", "Неизвестный тариф", 400)
    if acc["is_owner"]:
        raise ApiError("owner", "У вас безлимитный доступ, оплата не требуется", 400)
    plan = PLANS[plan_id]
    order_id = secrets.token_hex(8)
    with DB_LOCK:
        conn = db()
        conn.execute("INSERT INTO orders (id, account_id, plan_id, price, created_at) VALUES (?,?,?,?,?)",
                     (order_id, acc["id"], plan_id, plan["price"], int(time.time())))
        conn.commit()
        conn.close()
    params = {
        "receiver": env("YOOMONEY_WALLET"),
        "quickpay-form": "shop",
        "targets": f"Unblocknet: {plan['name']}",
        "paymentType": "AC",
        "sum": str(plan["price"]),
        "label": "ub:" + order_id,
    }
    return {"status": "ok", "order_id": order_id, "plan": plan,
            "payment_url": "https://yoomoney.ru/quickpay/confirm?" + urllib.parse.urlencode(params)}


def do_webhook(data):
    fields = ["notification_type", "operation_id", "amount", "currency", "datetime", "sender", "codepro"]
    sig_str = "&".join(data.get(k, "") for k in fields) + "&" + env("YOOMONEY_SECRET") + "&" + data.get("label", "")
    calc = hashlib.sha1(sig_str.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(calc.lower(), data.get("sha1_hash", "").lower()):
        log("WEBHOOK: bad signature")
        return 400
    op_id = data.get("operation_id", "")
    label = data.get("label", "")
    if data.get("test_notification") == "true":
        log("WEBHOOK: test notification OK")
        return 200
    if data.get("unaccepted") == "true" or data.get("codepro") == "true":
        log(f"WEBHOOK: payment on hold op={op_id}")
        notify("Unblocknet: платёж ожидает подтверждения", f"Операция {op_id}, сумма {data.get('amount')} ₽, метка {label}.\nПримите перевод в кошельке ЮMoney.")
        return 200

    with DB_LOCK:
        conn = db()
        try:
            if conn.execute("SELECT 1 FROM payments WHERE operation_id=?", (op_id,)).fetchone():
                log(f"WEBHOOK: duplicate op={op_id}")
                return 200
            order = None
            if label.startswith("ub:"):
                order = conn.execute("SELECT * FROM orders WHERE id=?", (label[3:],)).fetchone()
            raw = json.dumps(data, ensure_ascii=False)
            if not order:
                conn.execute("INSERT INTO payments (operation_id, order_id, amount, withdraw_amount, status, raw, created_at) VALUES (?,?,?,?,?,?,?)",
                             (op_id, label, data.get("amount"), data.get("withdraw_amount"), "no_order", raw, int(time.time())))
                conn.commit()
                notify("Unblocknet: ⚠️ платёж без заказа",
                       f"Пришёл платёж, который не удалось сопоставить с заказом.\nОперация: {op_id}\nСумма: {data.get('amount')} ₽\nМетка: {label}\n"
                       f"Отправитель: {data.get('sender')}\nПроверьте вручную.")
                return 200
            plan = PLANS.get(order["plan_id"], {})
            try:
                paid = float(data.get("withdraw_amount") or 0) or float(data.get("amount") or 0) / 0.97
            except ValueError:
                paid = 0.0
            acc = get_account(conn, order["account_id"])
            if paid + 0.5 < order["price"]:
                conn.execute("INSERT INTO payments (operation_id, order_id, account_id, plan_id, amount, withdraw_amount, status, raw, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                             (op_id, order["id"], order["account_id"], order["plan_id"], data.get("amount"), data.get("withdraw_amount"), "underpaid", raw, int(time.time())))
                conn.execute("UPDATE orders SET status='underpaid', operation_id=? WHERE id=?", (op_id, order["id"]))
                conn.commit()
                notify("Unblocknet: ⚠️ недоплата",
                       f"Аккаунт #{order['account_id']}, тариф {plan.get('name')}: ожидалось {order['price']} ₽, оплачено {paid:.2f} ₽.\nОперация {op_id}. Подписка НЕ продлена.")
                return 200

            base = max(now_ms(), acc["expiry_ms"] or 0)
            new_exp = base + plan.get("days", 30) * DAY_MS
            limit = max(acc["device_limit"] or 3, plan.get("limit_ip", 3))
            ensure_xui_client(conn, acc, new_exp, limit)
            conn.execute("UPDATE accounts SET expiry_ms=?, device_limit=?, plan=? WHERE id=?", (new_exp, limit, order["plan_id"], acc["id"]))
            conn.execute("UPDATE orders SET status='paid', operation_id=? WHERE id=?", (op_id, order["id"]))
            conn.execute("INSERT INTO payments (operation_id, order_id, account_id, plan_id, amount, withdraw_amount, status, raw, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                         (op_id, order["id"], acc["id"], order["plan_id"], data.get("amount"), data.get("withdraw_amount"), "success", raw, int(time.time())))
            conn.commit()
            n_dev = conn.execute("SELECT COUNT(*) FROM devices WHERE account_id=?", (acc["id"],)).fetchone()[0]
            first = conn.execute("SELECT COUNT(*) FROM payments WHERE account_id=? AND status='success'", (acc["id"],)).fetchone()[0] == 1
            day_ago = time.time() - 86400
            today_sum = sum(float(p["withdraw_amount"] or p["amount"] or 0) for p in
                            conn.execute("SELECT * FROM payments WHERE status='success' AND created_at>=?", (day_ago,)))
            log(f"PAYMENT ok account #{acc['id']} plan={order['plan_id']} op={op_id} until {fmt_date(new_exp)}")
            notify(
                f"Unblocknet: 💰 {'новый клиент' if first else 'продление'} — {plan.get('name')} ({order['price']} ₽)",
                "\n".join([
                    f"{'🎉 Новый платящий клиент!' if first else '🔁 Клиент продлил подписку.'}",
                    "",
                    f"Аккаунт: #{acc['id']}",
                    f"Тариф: {plan.get('name')}",
                    f"Оплачено: {data.get('withdraw_amount') or data.get('amount')} ₽ (зачислено {data.get('amount')} ₽)",
                    f"Подписка до: {fmt_date(new_exp)}",
                    f"Лимит устройств: {limit}, привязано: {n_dev}",
                    f"Операция ЮMoney: {op_id}",
                    f"Время: {fmt_dt(time.time())}",
                    "",
                    f"Выручка за последние 24 часа: {today_sum:.0f} ₽",
                ]))
            return 200
        finally:
            conn.close()


def gen_code(conn, kind, account_id=None, days=None, ttl=CODE_TTL_S):
    for _ in range(20):
        code = "".join(secrets.choice("0123456789") for _ in range(8))
        if not conn.execute("SELECT 1 FROM codes WHERE code=?", (code,)).fetchone():
            ts = int(time.time())
            conn.execute("INSERT INTO codes (code, kind, account_id, days, created_at, expires_at) VALUES (?,?,?,?,?,?)",
                         (code, kind, account_id, days, ts, ts + ttl))
            conn.commit()
            return code
    raise RuntimeError("code generation failed")


def do_link_create(dev, acc):
    sub = subscription_info(acc)
    if not sub["is_active"]:
        raise ApiError("inactive", "Подключать дополнительные устройства можно при активной подписке", 403)
    with DB_LOCK:
        conn = db()
        try:
            n = conn.execute("SELECT COUNT(*) FROM devices WHERE account_id=?", (acc["id"],)).fetchone()[0]
            if not acc["is_owner"] and n >= acc["device_limit"]:
                raise ApiError("device_limit", f"Достигнут лимит устройств ({acc['device_limit']}). Отвяжите одно из устройств или выберите Семейный тариф.", 403)
            code = gen_code(conn, "link", account_id=acc["id"])
            return {"status": "ok", "code": code, "expires_in_min": CODE_TTL_S // 60}
        finally:
            conn.close()


def do_activate(dev, acc, payload):
    code = re.sub(r"\D", "", str(payload.get("code") or ""))
    if len(code) != 8:
        raise ApiError("bad_code", "Код должен состоять из 8 цифр", 400)
    with DB_LOCK:
        conn = db()
        try:
            row = conn.execute("SELECT * FROM codes WHERE code=? AND used_at IS NULL AND expires_at>?", (code, int(time.time()))).fetchone()
            if not row:
                raise ApiError("bad_code", "Код неверный или истёк", 404)
            msg = ""
            if row["kind"] == "owner":
                owner = owner_account(conn)
                if not owner:
                    raise ApiError("no_owner", "Аккаунт владельца не настроен", 500)
                conn.execute("UPDATE devices SET account_id=? WHERE id=?", (owner["id"], dev["id"]))
                target_id, msg = owner["id"], "Устройство привязано к аккаунту владельца. Безлимитный доступ активирован."
            elif row["kind"] == "link":
                target = get_account(conn, row["account_id"])
                if not target or target["banned"]:
                    raise ApiError("bad_code", "Код недействителен", 404)
                if target["id"] == acc["id"]:
                    raise ApiError("same", "Это устройство уже привязано к этому аккаунту", 400)
                n = conn.execute("SELECT COUNT(*) FROM devices WHERE account_id=?", (target["id"],)).fetchone()[0]
                if not target["is_owner"] and n >= target["device_limit"]:
                    raise ApiError("device_limit", f"На аккаунте уже максимум устройств ({target['device_limit']})", 403)
                conn.execute("UPDATE devices SET account_id=? WHERE id=?", (target["id"], dev["id"]))
                target_id, msg = target["id"], "Устройство подключено к аккаунту."
            elif row["kind"] == "days":
                days = int(row["days"] or 0)
                base = max(now_ms(), acc["expiry_ms"] or 0)
                new_exp = base + days * DAY_MS
                ensure_xui_client(conn, acc, new_exp, max(acc["device_limit"], 3))
                conn.execute("UPDATE accounts SET expiry_ms=?, plan=COALESCE(plan,'promo') WHERE id=?", (new_exp, acc["id"]))
                target_id, msg = acc["id"], f"Подарочный код активирован: +{days} дн. (до {fmt_date(new_exp)})"
            else:
                raise ApiError("bad_code", "Код недействителен", 404)
            conn.execute("UPDATE codes SET used_at=?, used_by_device=? WHERE code=?", (int(time.time()), dev["id"], code))
            conn.commit()
            log(f"CODE {row['kind']} used by device #{dev['id']} -> account #{target_id}")
            res = me_payload(conn, get_account(conn, target_id), dev["id"])
            res["message"] = msg
            return res
        finally:
            conn.close()


def do_unbind(dev, acc, payload):
    try:
        target_id = int(payload.get("device_id"))
    except (TypeError, ValueError):
        raise ApiError("bad_device", "Неверное устройство", 400)
    with DB_LOCK:
        conn = db()
        try:
            acc = get_account(conn, acc["id"])
            target = conn.execute("SELECT * FROM devices WHERE id=? AND account_id=?", (target_id, acc["id"])).fetchone()
            if not target:
                raise ApiError("bad_device", "Устройство не найдено", 404)
            if target_id == dev["id"]:
                raise ApiError("self", "Нельзя отвязать текущее устройство", 400)
            if not acc["is_owner"] and time.time() < (acc["last_unbind_at"] or 0) + UNBIND_COOLDOWN_S:
                raise ApiError("cooldown", "Отвязывать устройства можно не чаще 1 раза в 7 дней", 429)
            conn.execute("DELETE FROM devices WHERE id=?", (target_id,))
            conn.execute("UPDATE accounts SET last_unbind_at=? WHERE id=?", (int(time.time()), acc["id"]))
            conn.commit()
            log(f"UNBIND device #{target_id} from account #{acc['id']}")
            res = me_payload(conn, get_account(conn, acc["id"]), dev["id"])
            res["message"] = "Устройство отвязано"
            return res
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Admin: server routing (domains / adblock) with geosite validation
# ---------------------------------------------------------------------------
_geosite_cache = {}


def geosite_ok(entry):
    if entry in _geosite_cache:
        return _geosite_cache[entry]
    cfg = {"log": {"loglevel": "none"}, "outbounds": [{"protocol": "freedom", "tag": "d"}, {"protocol": "blackhole", "tag": "b"}],
           "routing": {"rules": [{"type": "field", "outboundTag": "b", "domain": [entry]}]}}
    p = os.path.join(tempfile.gettempdir(), "ub_geosite_test.json")
    with open(p, "w") as f:
        json.dump(cfg, f)
    ok = subprocess.run([XRAY_BIN, "-test", "-c", p], capture_output=True, text=True, cwd=XRAY_DIR).returncode == 0
    _geosite_cache[entry] = ok
    return ok


def apply_server_routing(server_cfg):
    proxy = [f"domain:{d.strip()}" for d in server_cfg.get("custom_proxy_domains", []) if d.strip()]
    ads = []
    if server_cfg.get("adblock_enabled", True):
        ads = [g for g in ["geosite:category-ads-all"] if geosite_ok(g)]
        ads += [f"domain:{d.strip()}" for d in server_cfg.get("adblock_domains", []) if d.strip() and "/" not in d]
    abuse = [g for g in ("geosite:category-public-tracker", "geosite:bittorrent", "geosite:cryptominers") if geosite_ok(g)]
    rules = [
        {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
        {"type": "field", "outboundTag": "blocked", "ip": ["geoip:private"]},
        {"type": "field", "outboundTag": "blocked", "protocol": ["bittorrent"]},
        {"type": "field", "outboundTag": "blocked", "port": "25,465,587,3333,4444,8333,14444", "network": "tcp,udp"},
        {"type": "field", "outboundTag": "blocked", "port": "443", "network": "udp"},
    ]
    if abuse:
        rules.append({"type": "field", "outboundTag": "blocked", "domain": abuse})
    if ads:
        rules.append({"type": "field", "outboundTag": "blocked", "domain": ads})
    if proxy:
        rules.append({"type": "field", "outboundTag": "warp", "domain": proxy})
    conn = sqlite3.connect(XUI_DB, timeout=15)
    c = conn.cursor()
    row = c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'").fetchone()
    if not row:
        conn.close()
        return False
    t = json.loads(row[0])
    t.setdefault("routing", {})["rules"] = rules
    c.execute("UPDATE settings SET value=? WHERE key='xrayTemplateConfig'", (json.dumps(t),))
    conn.commit()
    conn.close()
    try:
        PANEL.restart_xray()
    except Exception as e:
        log("restart_xray via panel failed:", e)
        subprocess.run(["systemctl", "restart", "x-ui"])
    return True


def require_admin(handler, conn):
    tok = handler.headers.get("X-Admin-Token", "")
    if tok and env("ADMIN_TOKEN") and hmac.compare_digest(tok, env("ADMIN_TOKEN")):
        return True
    dev, acc = auth_device(conn, handler.headers)
    if acc["is_owner"]:
        return True
    raise ApiError("forbidden", "Недостаточно прав", 403)


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "Unblocknet-API/2"
    sys_version = ""

    def log_message(self, fmt, *args):
        pass

    @property
    def ip(self):
        return self.client_address[0]

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, code=200):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self, limit=16384):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n > limit:
            raise ApiError("too_large", "Слишком большой запрос", 413)
        return self.rfile.read(n).decode("utf-8", "replace") if n else ""

    def _json_body(self):
        raw = self._read_body()
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            raise ApiError("bad_json", "Некорректный JSON", 400)

    def _limit(self, action):
        if not rate_ok(self.ip, action):
            raise ApiError("rate_limited", "Слишком много запросов, попробуйте позже", 429)

    def _authed(self, action):
        self._limit(action)
        conn = db()
        try:
            dev, acc = auth_device(conn, self.headers)
            touch_device(conn, dev, self.ip)
            return dev, acc
        finally:
            conn.close()

    def _dispatch(self, method):
        path = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        try:
            if method == "GET":
                if path == "/api/health":
                    return self._send_json({"status": "healthy", "service": "unblocknet-api", "version": 2})
                if path == "/api/config":
                    return self._send_json({"status": "ok", "config": public_server_config(), "plans": PLANS})
                if path == "/api/plans":
                    return self._send_json({"status": "ok", "plans": PLANS})
                if path == "/api/me":
                    dev, acc = self._authed("me")
                    conn = db()
                    try:
                        return self._send_json(me_payload(conn, get_account(conn, acc["id"]), dev["id"]))
                    finally:
                        conn.close()
                if path == "/api/subscription/status":
                    # legacy clients (shared key) -> ask to update
                    return self._send_json({"status": "ok", "plans": PLANS, "subscription": {
                        "is_active": False, "status": "update_required", "days_left": 0, "expiry_date": "--",
                        "message": "Обновите приложение Unblocknet до последней версии"}})
                return self._send_json({"error": "not found"}, 404)

            # POST
            if path == "/api/payment/yoomoney/webhook":
                raw = self._read_body(65536)
                data = {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}
                code = do_webhook(data)
                return self._send_text("OK" if code == 200 else "Invalid signature", code)
            if path == "/api/register":
                self._limit("register")
                return self._send_json(do_register(self._json_body(), self.ip))
            if path in ("/api/trial", "/api/subscription/trial"):
                if self.headers.get("Authorization", "").startswith("Bearer "):
                    dev, acc = self._authed("trial")
                    return self._send_json(do_trial(dev, acc, self.ip))
                raise ApiError("update_required", "Обновите приложение Unblocknet до последней версии", 426)
            if path == "/api/payment/create":
                dev, acc = self._authed("payment")
                return self._send_json(do_payment_create(dev, acc, self._json_body()))
            if path == "/api/link/create":
                dev, acc = self._authed("link")
                return self._send_json(do_link_create(dev, acc))
            if path == "/api/activate":
                dev, acc = self._authed("activate")
                return self._send_json(do_activate(dev, acc, self._json_body()))
            if path == "/api/devices/unbind":
                dev, acc = self._authed("unbind")
                return self._send_json(do_unbind(dev, acc, self._json_body()))
            if path in ("/api/domains/add", "/api/adblock/toggle"):
                self._limit("admin")
                conn = db()
                try:
                    require_admin(self, conn)
                finally:
                    conn.close()
                payload = self._json_body()
                cfg = load_server_config()
                if path == "/api/domains/add":
                    domain = re.sub(r"[^a-z0-9.\-]", "", str(payload.get("domain", "")).strip().lower())
                    if not domain or "." not in domain:
                        raise ApiError("bad_domain", "Некорректный домен", 400)
                    key = "custom_proxy_domains" if payload.get("mode", "proxy") == "proxy" else "custom_direct_domains"
                    if domain not in cfg.setdefault(key, []):
                        cfg[key].append(domain)
                        save_server_config(cfg)
                        if key == "custom_proxy_domains":
                            threading.Thread(target=apply_server_routing, args=(cfg,), daemon=True).start()
                    return self._send_json({"status": "ok", "message": f"Домен {domain} добавлен", "domain": domain})
                enabled = bool(payload.get("enabled", not cfg.get("adblock_enabled", True)))
                cfg["adblock_enabled"] = enabled
                save_server_config(cfg)
                threading.Thread(target=apply_server_routing, args=(cfg,), daemon=True).start()
                return self._send_json({"status": "ok", "adblock_enabled": enabled})
            return self._send_json({"error": "endpoint not found"}, 404)
        except ApiError as e:
            return self._send_json({"status": "error", "error": e.code, "message": e.message}, e.http)
        except PanelError as e:
            log("PANEL ERROR:", e)
            return self._send_json({"status": "error", "error": "panel", "message": "Сервер временно недоступен, попробуйте через минуту"}, 503)
        except Exception as e:
            log("INTERNAL ERROR:", e, traceback.format_exc())
            try:
                return self._send_json({"status": "error", "error": "internal", "message": "Внутренняя ошибка сервера"}, 500)
            except Exception:
                pass

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


# ---------------------------------------------------------------------------
# Admin CLI
# ---------------------------------------------------------------------------
def cli(argv):
    init_db()
    cmd = argv[0] if argv else "help"
    conn = db()
    if cmd == "code":
        if "--owner" in argv:
            code = gen_code(conn, "owner", ttl=CODE_TTL_S)
            print(f"Код владельца: {code}  (действует {CODE_TTL_S // 60} минут, одноразовый)")
        elif "--days" in argv:
            days = int(argv[argv.index("--days") + 1])
            ttl = 30 * 86400
            code = gen_code(conn, "days", days=days, ttl=ttl)
            print(f"Подарочный код на {days} дн.: {code}  (действует 30 дней, одноразовый)")
        else:
            print("usage: code --owner | code --days N")
    elif cmd == "users":
        for a in conn.execute("SELECT a.*, (SELECT COUNT(*) FROM devices d WHERE d.account_id=a.id) AS n FROM accounts a ORDER BY a.id"):
            sub = subscription_info(a)
            print(f"#{a['id']:<5} {'OWNER ' if a['is_owner'] else ''}{'BANNED ' if a['banned'] else ''}"
                  f"{sub['status']:<8} до {sub['expiry_date']:<11} план={a['plan'] or '-':<10} устройств {a['n']}/{a['device_limit']} "
                  f"триал={'да' if a['trial_used'] else 'нет'} xui={a['xui_email'] or '-'}")
    elif cmd == "stats":
        print(build_stats_text(time.time() - 86400))
    elif cmd in ("ban", "unban"):
        acc_id = int(argv[1])
        acc = get_account(conn, acc_id)
        conn.execute("UPDATE accounts SET banned=? WHERE id=?", (1 if cmd == "ban" else 0, acc_id))
        conn.commit()
        if acc and acc["xui_email"] and not acc["is_owner"]:
            PANEL.update(acc["xui_email"], enable=(cmd == "unban"))
        print(f"account #{acc_id} {cmd}ned")
    elif cmd == "mailtest":
        smtp_send("Unblocknet: тестовое письмо", "Уведомления Unblocknet настроены и работают.\n\n" + build_stats_text(time.time() - 86400))
        print("mail sent")
    else:
        print(__doc__)
    conn.close()


def run():
    init_db()
    threading.Thread(target=mail_worker, daemon=True).start()
    threading.Thread(target=scheduler_worker, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    log(f"Unblocknet API v2 listening on :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        cli(sys.argv[2:])
    else:
        run()
