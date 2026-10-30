"""
teletok_server_api.py - Server Synchronization & Billing API for Teletok Connect.
Runs on VPS (193.233.138.42:2096).
Handles:
- Config distribution for zero-setup PC clients (GET /api/config)
- Dynamic domain additions and sync (POST /api/domains/add)
- Ad-blocking rules deployment for YouTube, Rutube, and VK Video
- YooMoney P2P Webhook and payment verification (POST /api/payment/yoomoney/webhook)
- Payment link creation (POST /api/payment/create)
- Subscription status check (GET /api/subscription/status)
- 3-day trial activation (POST /api/subscription/trial)
- Anti-abuse routing: BitTorrent, SMTP spam, cryptomining, phishing block
- Multi-device restriction: limitIp = 3
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import urllib.parse
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 2096
DATA_DIR = "/etc/teletok"
DATA_FILE = os.path.join(DATA_DIR, "server_config.json")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.json")
DB_PATH = "/etc/x-ui/x-ui.db"
XRAY_BIN = "/usr/local/x-ui/bin/xray-linux-amd64"
CONFIG_JSON = "/usr/local/x-ui/bin/config.json"

YOOMONEY_WALLET = "410011134916951"
YOOMONEY_SECRET = "m7l2Z5/tbSSOSEArC2P4gmOS"

PLANS = {
    "trial_3d": {"name": "Тестовый (3 дня)", "days": 3, "price": 0, "limit_ip": 3, "desc": "3 дня бесплатно • До 3 устройств"},
    "1m": {"name": "1 месяц", "days": 30, "price": 149, "limit_ip": 3, "desc": "149 ₽/мес • Базовый доступ на 30 дней"},
    "3m": {"name": "3 месяца", "days": 90, "price": 390, "limit_ip": 3, "desc": "130 ₽/мес • Скидка 13% • До 3 устройств"},
    "6m": {"name": "6 месяцев", "days": 180, "price": 690, "limit_ip": 3, "desc": "115 ₽/мес • Скидка 23% • До 3 устройств"},
    "1y": {"name": "1 год", "days": 365, "price": 1190, "limit_ip": 3, "desc": "99 ₽/мес • Скидка 33% • Хит 🔥 • До 3 устройств"},
    "family_1y": {"name": "Семейный (1 год)", "days": 365, "price": 1990, "limit_ip": 6, "desc": "165 ₽/мес • До 6 устройств для всей семьи 👨‍👩‍👧‍👦"}
}

DEFAULT_SERVER_CONFIG = {
    "version": 3,
    "nodes": {
        "443-ff": {
            "name": "Финляндия 443 (Firefox)",
            "vps_host": "193.233.138.42",
            "vps_port": 443,
            "sni": "speed.cloudflare.com",
            "fingerprint": "firefox",
            "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
            "sid": "dae45f",
            "uuid": "04756662-2f98-44ad-a53a-369d29118670",
            "flow": "xtls-rprx-vision"
        },
        "2053-sf": {
            "name": "Финляндия 2053 (Safari)",
            "vps_host": "193.233.138.42",
            "vps_port": 2053,
            "sni": "azure.microsoft.com",
            "fingerprint": "safari",
            "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
            "sid": "dae45f",
            "uuid": "04756662-2f98-44ad-a53a-369d29118670",
            "flow": "xtls-rprx-vision"
        },
        "2053-ff": {
            "name": "Финляндия 2053 (Firefox)",
            "vps_host": "193.233.138.42",
            "vps_port": 2053,
            "sni": "azure.microsoft.com",
            "fingerprint": "firefox",
            "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
            "sid": "dae45f",
            "uuid": "04756662-2f98-44ad-a53a-369d29118670",
            "flow": "xtls-rprx-vision"
        },
        "443-sf": {
            "name": "Финляндия 443 (Safari)",
            "vps_host": "193.233.138.42",
            "vps_port": 443,
            "sni": "speed.cloudflare.com",
            "fingerprint": "safari",
            "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
            "sid": "dae45f",
            "uuid": "04756662-2f98-44ad-a53a-369d29118670",
            "flow": "xtls-rprx-vision"
        }
    },
    "custom_proxy_domains": [
        "chatgpt.com",
        "openai.com",
        "oaistatic.com",
        "oaiusercontent.com",
        "claude.ai",
        "anthropic.com",
        "aistudio.google.com",
        "gemini.google.com",
        "generativelanguage.googleapis.com",
        "perplexity.ai",
        "suno.ai",
        "suno.com",
        "runwayml.com",
        "midjourney.com",
        "spotify.com",
        "notion.so",
        "canva.com"
    ],
    "custom_direct_domains": [
        "yandex.ru",
        "gosuslugi.ru",
        "sberbank.ru",
        "tinkoff.ru",
        "t-bank.ru",
        "vk.com",
        "ozon.ru",
        "wildberries.ru",
        "kinopoisk.ru"
    ],
    "adblock_domains": [
        "googleads.g.doubleclick.net",
        "pagead2.googlesyndication.com",
        "adservice.google.com",
        "video-stats.l.google.com",
        "ad.doubleclick.net",
        "ads.vk.com",
        "ad.mail.ru",
        "top-fwz1.mail.ru",
        "target.my.com",
        "an.yandex.ru",
        "mc.yandex.ru",
        "yandex.ru/ads",
        "rutube.ru/api/ad",
        "ad.adriver.ru",
        "content.adriver.ru"
    ],
    "adblock_enabled": True
}

def load_server_config():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_SERVER_CONFIG, f, indent=2, ensure_ascii=False)
    return DEFAULT_SERVER_CONFIG

def save_server_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_payments_log():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_payment_log(payment_entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    logs = load_payments_log()
    logs.append(payment_entry)
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def apply_to_xray_and_db(server_cfg):
    """
    Applies custom domains, adblock rules, and robust anti-abuse filters:
    - protocol bittorrent blocked
    - geosite:bittorrent blocked
    - geosite:cryptominers blocked
    - geosite:malware / phishing blocked
    - SMTP outgoing ports (25, 465, 587) blocked
    - Mining ports (3333, 4444, 8333, 14444) blocked
    - Enforces limitIp: 3 in SQLite for all clients
    """
    try:
        # 1. Update /usr/local/x-ui/bin/config.json
        if os.path.exists(CONFIG_JSON):
            with open(CONFIG_JSON, "r", encoding="utf-8") as f:
                xcfg = json.load(f)
            
            warp_domains = []
            for d in server_cfg.get("custom_proxy_domains", []):
                d = d.strip()
                if d:
                    warp_domains.append(f"domain:{d}")
            
            adblock_domains = []
            if server_cfg.get("adblock_enabled", True):
                adblock_domains.append("geosite:category-ads-all")
                for d in server_cfg.get("adblock_domains", []):
                    d = d.strip()
                    if d:
                        adblock_domains.append(f"domain:{d}")

            abuse_domains = [
                "geosite:bittorrent",
                "geosite:cryptominers",
                "geosite:malware",
                "geosite:phishing"
            ]

            rules = [
                {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
                {"type": "field", "outboundTag": "blocked", "ip": ["geoip:private"]},
                # 1. Torrent protocol block
                {"type": "field", "outboundTag": "blocked", "protocol": ["bittorrent"]},
                # 2. Torrent, miner, malware domains block
                {"type": "field", "outboundTag": "blocked", "domain": abuse_domains},
                # 3. Spam & Mining ports block (SMTP 25, 465, 587 + miner ports)
                {
                    "type": "field",
                    "outboundTag": "blocked",
                    "port": "25,465,587,3333,4444,8333,14444",
                    "network": "tcp,udp"
                },
                # 4. UDP 443 QUIC block
                {"type": "field", "outboundTag": "blocked", "port": "443", "network": "udp"}
            ]

            if adblock_domains:
                rules.append({
                    "type": "field",
                    "outboundTag": "blocked",
                    "domain": adblock_domains
                })

            if warp_domains:
                rules.append({
                    "type": "field",
                    "outboundTag": "warp",
                    "domain": warp_domains
                })

            xcfg["routing"]["rules"] = rules

            with open(CONFIG_JSON, "w", encoding="utf-8") as f:
                json.dump(xcfg, f, indent=2, ensure_ascii=False)

            # Test & restart x-ui
            res = subprocess.run([XRAY_BIN, "-test", "-c", CONFIG_JSON], capture_output=True, text=True)
            if res.returncode == 0:
                subprocess.run(["systemctl", "restart", "x-ui"], check=True)
                print("x-ui restarted with anti-abuse routing successfully.", flush=True)

        # 2. Sync into SQLite settings template & enforce limitIp = 3
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'")
            row = c.fetchone()
            if row:
                t = json.loads(row[0])
                t["routing"]["rules"] = rules
                c.execute("UPDATE settings SET value=? WHERE key='xrayTemplateConfig'", (json.dumps(t),))

            # Enforce minimum limitIp = 3 on all inbounds, preserve higher family limits
            c.execute("SELECT id, settings FROM inbounds")
            inbounds = c.fetchall()
            for in_id, in_settings in inbounds:
                s = json.loads(in_settings)
                modified = False
                for cl in s.get("clients", []):
                    if not cl.get("limitIp") or cl.get("limitIp") < 3:
                        cl["limitIp"] = 3
                        modified = True
                if modified:
                    c.execute("UPDATE inbounds SET settings=? WHERE id=?", (json.dumps(s), in_id))

            conn.commit()
            conn.close()

        return True
    except Exception as e:
        print(f"Error applying config: {e}", flush=True)
        return False

def get_client_subscription(client_id="79500490409"):
    """Fetches subscription info for a given client UUID or email."""
    if not os.path.exists(DB_PATH):
        return {"status": "active", "days_remaining": 999, "expiry_time": 0}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT settings FROM inbounds LIMIT 1")
    row = c.fetchone()
    conn.close()

    if not row:
        return {"status": "unknown", "days_remaining": 0}

    s = json.loads(row[0])
    target_client = None
    for cl in s.get("clients", []):
        if cl.get("id") == client_id or cl.get("email") == client_id:
            target_client = cl
            break

    if not target_client:
        return {"status": "not_found", "days_remaining": 0}

    expiry_ms = target_client.get("expiryTime", 0)
    now_ms = int(time.time() * 1000)

    if expiry_ms == 0:
        return {
            "status": "active",
            "is_unlimited": True,
            "days_remaining": 999,
            "expiry_date": "Безлимитно",
            "limit_ip": target_client.get("limitIp", 3)
        }

    days_rem = max(0, int((expiry_ms - now_ms) / (86400 * 1000)))
    is_active = expiry_ms > now_ms and target_client.get("enable", True)
    
    # Format readable date
    exp_date_str = time.strftime("%d.%m.%Y", time.localtime(expiry_ms / 1000))

    return {
        "status": "active" if is_active else "expired",
        "is_unlimited": False,
        "days_remaining": days_rem,
        "expiry_ms": expiry_ms,
        "expiry_date": exp_date_str,
        "limit_ip": target_client.get("limitIp", 3)
    }

def extend_client_subscription(client_id, days_to_add, set_limit_ip=None):
    """
    Extends client expiryTime by days_to_add in SQLite and reloads Xray.
    If current subscription is active, adds to existing expiryTime.
    If expired, sets now + days_to_add.
    Optionally updates limitIp (e.g. 6 devices for family plan).
    """
    if not os.path.exists(DB_PATH):
        return False, "Database not found"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, settings FROM inbounds")
    rows = c.fetchall()

    now_ms = int(time.time() * 1000)
    add_ms = days_to_add * 86400 * 1000
    new_expiry_ms = None

    for in_id, in_settings in rows:
        s = json.loads(in_settings)
        for cl in s.get("clients", []):
            if cl.get("id") == client_id or cl.get("email") == client_id:
                cur_exp = cl.get("expiryTime", 0)
                if cur_exp > now_ms:
                    cl["expiryTime"] = cur_exp + add_ms
                else:
                    cl["expiryTime"] = now_ms + add_ms
                cl["enable"] = True
                if set_limit_ip:
                    cl["limitIp"] = set_limit_ip
                new_expiry_ms = cl["expiryTime"]
                break
        c.execute("UPDATE inbounds SET settings=? WHERE id=?", (json.dumps(s), in_id))

    conn.commit()
    conn.close()

    # Restart x-ui service in background
    try:
        subprocess.Popen(["systemctl", "restart", "x-ui"])
    except Exception:
        pass
    exp_date = time.strftime("%d.%m.%Y", time.localtime(new_expiry_ms / 1000)) if new_expiry_ms else "Unknown"
    return True, f"Продлено до {exp_date}"

class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ("/api/config", "/api/config/"):
            cfg = load_server_config()
            self._send_json({"status": "ok", "config": cfg, "plans": PLANS})
        elif path == "/api/health":
            self._send_json({"status": "healthy", "service": "teletok-server-api", "yoomoney_ready": True})
        elif path == "/api/subscription/status":
            client_id = query.get("client_id", ["79500490409"])[0]
            sub = get_client_subscription(client_id)
            self._send_json({"status": "ok", "subscription": sub, "plans": PLANS})
        elif path == "/api/plans":
            self._send_json({"status": "ok", "plans": PLANS})
        else:
            self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/payment/create":
            # Generates YooMoney payment URL and order
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                self._send_json({"error": "invalid json"}, code=400)
                return

            client_id = payload.get("client_id", "79500490409").strip()
            plan_id = payload.get("plan_id", "1m").strip()
            if plan_id not in PLANS or plan_id == "trial_3d":
                self._send_json({"error": "invalid plan"}, code=400)
                return

            plan = PLANS[plan_id]
            order_id = f"tt::{plan_id}::{client_id}::{int(time.time())}"
            target_desc = f"Подписка Teletok VPN ({plan['name']})"

            # Build YooMoney QuickPay URL
            params = {
                "receiver": YOOMONEY_WALLET,
                "quickpay-form": "shop",
                "targets": target_desc,
                "paymentType": "AC",  # Bank card by default
                "sum": str(plan["price"]),
                "label": order_id
            }
            payment_url = f"https://yoomoney.ru/quickpay/confirm?{urllib.parse.urlencode(params)}"

            self._send_json({
                "status": "ok",
                "order_id": order_id,
                "plan": plan,
                "payment_url": payment_url
            })

        elif path == "/api/subscription/trial":
            # Activate 3-day trial
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                payload = {}

            client_id = payload.get("client_id", "79500490409")
            ok, msg = extend_client_subscription(client_id, 3)
            sub = get_client_subscription(client_id)
            self._send_json({
                "status": "ok" if ok else "error",
                "message": msg,
                "subscription": sub
            })

        elif path == "/api/payment/yoomoney/webhook":
            # YooMoney HTTP notification receiver
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(length).decode("utf-8")
                params = urllib.parse.parse_qs(raw_body)
                data = {k: v[0] for k, v in params.items()}
            except Exception as e:
                print("Webhook parse error:", e, flush=True)
                self.send_response(400)
                self.end_headers()
                return

            notification_type = data.get("notification_type", "")
            operation_id = data.get("operation_id", "")
            amount = data.get("amount", "")
            currency = data.get("currency", "")
            datetime_val = data.get("datetime", "")
            sender = data.get("sender", "")
            codepro = data.get("codepro", "")
            label = data.get("label", "")
            sha1_hash = data.get("sha1_hash", "")
            unaccepted = data.get("unaccepted", "false")

            # Signature verification:
            # SHA1(notification_type&operation_id&amount&currency&datetime&sender&codepro&notification_secret&label)
            sig_str = f"{notification_type}&{operation_id}&{amount}&{currency}&{datetime_val}&{sender}&{codepro}&{YOOMONEY_SECRET}&{label}"
            calc_hash = hashlib.sha1(sig_str.encode("utf-8")).hexdigest()

            if calc_hash.lower() != sha1_hash.lower():
                print(f"WEBHOOK HASH MISMATCH! Calculated: {calc_hash}, Received: {sha1_hash}", flush=True)
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid signature")
                return

            if unaccepted == "true":
                print("Payment unaccepted / on hold", flush=True)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            print(f"VALID YOOMONEY PAYMENT RECEIVED: {amount} RUB for label: {label}", flush=True)

            # Determine plan and client from label: format "tt::{plan}::{client_id}::{timestamp}"
            plan_id = "1m"
            client_id = "79500490409"
            if "::" in label:
                parts = label.split("::")
                if len(parts) >= 3 and parts[0] == "tt":
                    plan_id = parts[1]
                    client_id = parts[2]
            elif "_" in label:
                parts = label.split("_")
                if len(parts) >= 3 and parts[0] == "tt":
                    plan_id = parts[1]
                    client_id = parts[2]

            plan_info = PLANS.get(plan_id, {})
            days_to_add = plan_info.get("days", 30)
            target_limit_ip = plan_info.get("limit_ip", 3)
            ok, msg = extend_client_subscription(client_id, days_to_add, set_limit_ip=target_limit_ip)

            # Save to payments history
            save_payment_log({
                "operation_id": operation_id,
                "amount": amount,
                "client_id": client_id,
                "plan_id": plan_id,
                "days_added": days_to_add,
                "label": label,
                "datetime": datetime_val,
                "status": "success" if ok else "error",
                "message": msg
            })

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "2")
            self.end_headers()
            try:
                self.wfile.write(b"OK")
                self.wfile.flush()
            except Exception:
                pass

            # Restart x-ui in background thread so webhook response returns instantly
            import threading
            threading.Thread(target=lambda: subprocess.run(["systemctl", "restart", "x-ui"]), daemon=True).start()

        elif path == "/api/domains/add":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                self._send_json({"error": "invalid json"}, code=400)
                return

            domain = payload.get("domain", "").strip().lower()
            mode = payload.get("mode", "proxy")

            if not domain:
                self._send_json({"error": "empty domain"}, code=400)
                return

            cfg = load_server_config()
            list_key = "custom_proxy_domains" if mode == "proxy" else "custom_direct_domains"
            if domain not in cfg[list_key]:
                cfg[list_key].append(domain)
                save_server_config(cfg)
                apply_to_xray_and_db(cfg)

            self._send_json({
                "status": "ok",
                "message": f"Домен {domain} добавлен",
                "domain": domain
            })

        elif path == "/api/adblock/toggle":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                payload = {}

            cfg = load_server_config()
            enabled = payload.get("enabled", not cfg.get("adblock_enabled", True))
            cfg["adblock_enabled"] = enabled
            save_server_config(cfg)
            apply_to_xray_and_db(cfg)

            self._send_json({"status": "ok", "adblock_enabled": enabled})
        else:
            self._send_json({"error": "endpoint not found"}, code=404)

def run():
    print("Initializing Teletok Server API with Billing & Anti-Abuse...", flush=True)
    cfg = load_server_config()
    apply_to_xray_and_db(cfg)
    server = HTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"Teletok Server API running on port {PORT}...", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    run()
