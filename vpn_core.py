"""
vpn_core.py - Core engine for Teletok VPN Windows Client.
Handles Xray process, in-process TLS fragmentation relay,
Windows system proxy settings, and split-tunnel routing rules.
"""

import os
import sys
import json
import time
import socket
import ctypes
import threading
import subprocess
import winreg
import atexit

import tempfile

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR

# Dedicated user settings dir in %LOCALAPPDATA% to keep single .exe completely clean
USER_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", APP_DIR), "Unblocknet")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Locate xray.exe across potential bundled / portable locations
def get_xray_path():
    candidates = [
        os.path.join(BUNDLE_DIR, "xray.exe"),
        os.path.join(APP_DIR, "xray.exe"),
        os.path.join(USER_DATA_DIR, "bin", "xray.exe"),
        os.path.join(APP_DIR, "v2rayN", "v2rayN-windows-64", "bin", "Xray", "xray.exe"),
        os.path.join(BUNDLE_DIR, "v2rayN", "v2rayN-windows-64", "bin", "Xray", "xray.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

XRAY_PATH = get_xray_path()

SETTINGS_FILE = os.path.join(USER_DATA_DIR, "vpn_client_settings.json")
TOKEN_FILE = os.path.join(USER_DATA_DIR, "device_token.dat")
RUNTIME_CONFIG = os.path.join(tempfile.gettempdir(), "unblocknet_runtime_config.json")

# WinINet API for instant proxy refresh
INTERNET_OPTION_REFRESH = 37
INTERNET_OPTION_SETTINGS_CHANGED = 39

try:
    wininet = ctypes.windll.wininet
except Exception:
    wininet = None

def notify_proxy_change():
    """Notifies Windows subsystem and browsers that proxy settings changed."""
    if wininet:
        try:
            wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception:
            pass

def flush_dns_cache():
    """Instantly flushes Windows system DNS resolver cache."""
    try:
        if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'dnsapi'):
            ctypes.windll.dnsapi.DnsFlushResolverCache()
    except Exception:
        pass
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.run(["ipconfig", "/flushdns"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    except Exception:
        pass

def free_vpn_ports():
    """Terminates any orphaned or zombie xray processes holding ports 10897/10898."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "xray.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

def self_heal_network():
    """
    Self-heals network and socket state:
    1. Kills orphaned proxy core instances and frees ports 10897/10898.
    2. Flushes Windows DNS cache.
    3. Flushes and refreshes WinINet proxy state across browsers.
    """
    free_vpn_ports()
    flush_dns_cache()
    notify_proxy_change()

# Default nodes (personal UUID is injected dynamically from server per user)
NODES = {
    "443-ff": {
        "name": "Финляндия 443 (Firefox)",
        "desc": "Порт 443 (Cloudflare SNI + Firefox FP)",
        "vps_host": "193.233.138.42",
        "vps_port": 443,
        "sni": "speed.cloudflare.com",
        "fingerprint": "firefox",
        "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
        "sid": "dae45f",
        "uuid": "",
        "flow": "xtls-rprx-vision"
    },
    "2053-sf": {
        "name": "Финляндия 2053 (Safari)",
        "desc": "Порт 2053 (Azure SNI + Safari FP)",
        "vps_host": "193.233.138.42",
        "vps_port": 2053,
        "sni": "azure.microsoft.com",
        "fingerprint": "safari",
        "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
        "sid": "dae45f",
        "uuid": "",
        "flow": "xtls-rprx-vision"
    },
    "2053": {
        "name": "Финляндия 2053 (Авто)",
        "desc": "Основной высокоскоростной узел 2053",
        "vps_host": "193.233.138.42",
        "vps_port": 2053,
        "sni": "azure.microsoft.com",
        "fingerprint": "safari",
        "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
        "sid": "dae45f",
        "uuid": "",
        "flow": "xtls-rprx-vision"
    },
    "443-frag": {
        "name": "Финляндия 443 (Авто)",
        "desc": "Резервный узел 443",
        "vps_host": "193.233.138.42",
        "vps_port": 443,
        "sni": "speed.cloudflare.com",
        "fingerprint": "firefox",
        "pbk": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
        "sid": "dae45f",
        "uuid": "",
        "flow": "xtls-rprx-vision"
    }
}

DEFAULT_SETTINGS = {
    "selected_node": "2053",
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
    "custom_proxy_domains": [
        # --- Нейросети и искусственный интеллект ---
        "chatgpt.com",
        "openai.com",
        "oaistatic.com",
        "oaiusercontent.com",
        "claude.ai",
        "anthropic.com",
        "perplexity.ai",
        "gemini.google.com",
        "aistudio.google.com",
        "generativelanguage.googleapis.com",
        "bard.google.com",
        "midjourney.com",
        "copilot.microsoft.com",
        "cursor.com",
        "cursor.sh",
        "elevenlabs.io",
        "poe.com",
        "groq.com",
        "huggingface.co",
        "runwayml.com",
        "suno.ai",
        "suno.com",
        "mistral.ai",
        "cohere.com",
        "stability.ai",
        "deepl.com",
        
        # --- Зарубежные сервисы с ограничениями для РФ ---
        "spotify.com",
        "scdn.co",
        "notion.so",
        "notion.site",
        "canva.com",
        "figma.com",
        "docker.com",
        "docker.io",
        "atlassian.com",
        "trello.com",
        "jira.com",
        "miro.com",
        "slack.com",
        "netflix.com",
        "nflxvideo.net",
        "intel.com",
        "dell.com",
        "autodesk.com",
        
        # --- Google и Cloudflare инфраструктура ---
        "google.com",
        "googleapis.com",
        "gstatic.com",
        "googleusercontent.com",
        "cloudflare.com",
        "challenges.cloudflare.com",
        
        # --- Соцсети, стриминги и коммуникации ---
        "youtube.com",
        "googlevideo.com",
        "ytimg.com",
        "youtu.be",
        "instagram.com",
        "cdninstagram.com",
        "facebook.com",
        "fbcdn.net",
        "threads.net",
        "meta.com",
        "x.com",
        "twitter.com",
        "t.co",
        "twimg.com",
        "discord.com",
        "discord.gg",
        "discordapp.com",
        "discordapp.net",
        "linkedin.com",
        "licdn.com",
        "reddit.com",
        "redditmedia.com",
        "telegram.org",
        "t.me"
    ],
    "autostart": False,
    "autoconnect": True,
    "adblock_enabled": True,
    "webrtc_protect": True
}

SERVER_API_URL = "http://193.233.138.42:2096"
REG_KEY_UNBLOCKNET = r"Software\Unblocknet"

def get_device_hwid():
    """Gathers 4-component hardware fingerprint with multi-level fallbacks, returns hex sha256 hashes."""
    import hashlib
    hw = {"mg": "", "bios": "", "disk": "", "cpu": ""}

    # 1. MachineGuid from Windows Registry
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            mg, _ = winreg.QueryValueEx(k, "MachineGuid")
            if mg:
                hw["mg"] = hashlib.sha256(mg.strip().lower().encode()).hexdigest()
    except Exception:
        pass

    # 2. BIOS UUID, Disk Serial, CPU ID via PowerShell CIM
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    ps_cmd = (
        "$b = (Get-CimInstance Win32_ComputerSystemProduct -ErrorAction SilentlyContinue).UUID; "
        "$d = (Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue | Select-Object -First 1).SerialNumber; "
        "$c = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1).ProcessorId; "
        "\"$b`n$d`n$c\""
    )
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                             capture_output=True, text=True, timeout=5, creationflags=flags).stdout
        parts = [l.strip() for l in out.splitlines() if l.strip()]
        if len(parts) >= 1 and parts[0] and parts[0] not in ("00000000-0000-0000-0000-000000000000", "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"):
            hw["bios"] = hashlib.sha256(parts[0].lower().encode()).hexdigest()
        if len(parts) >= 2 and parts[1] and parts[1] != "00000000":
            hw["disk"] = hashlib.sha256(parts[1].lower().encode()).hexdigest()
        if len(parts) >= 3 and parts[2]:
            hw["cpu"] = hashlib.sha256(parts[2].lower().encode()).hexdigest()
    except Exception:
        pass

    # Fallback for BIOS UUID from Registry if CIM failed
    if not hw["bios"]:
        for reg_sub in [r"HARDWARE\DESCRIPTION\System\BIOS", r"SYSTEM\HardwareConfig\Current"]:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_sub, 0, winreg.KEY_READ) as k:
                    val = ""
                    for key_name in ["SystemManufacturer", "BaseBoardProduct", "BIOSSerialNumber"]:
                        try:
                            v, _ = winreg.QueryValueEx(k, key_name)
                            if v:
                                val += str(v).strip()
                        except Exception:
                            pass
                    if val:
                        hw["bios"] = hashlib.sha256(val.lower().encode()).hexdigest()
                        break
            except Exception:
                pass

    # Fallback for Disk Serial: Volume Serial Number of C:\
    if not hw["disk"]:
        try:
            vol_serial = ctypes.c_ulong()
            if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'kernel32'):
                if ctypes.windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p("C:\\"), None, 0, ctypes.byref(vol_serial), None, None, None, 0):
                    if vol_serial.value:
                        hw["disk"] = hashlib.sha256(f"vol_{vol_serial.value}".encode()).hexdigest()
        except Exception:
            pass

    # Fallback for CPU if missing: CPU ProcessorNameString
    if not hw["cpu"]:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", 0, winreg.KEY_READ) as k:
                pname, _ = winreg.QueryValueEx(k, "ProcessorNameString")
                if pname:
                    hw["cpu"] = hashlib.sha256(pname.strip().lower().encode()).hexdigest()
        except Exception:
            pass

    # Absolute fallback: Primary MAC Address
    if sum(1 for c in ("mg", "bios", "disk") if hw[c]) < 2:
        try:
            import uuid as _uuid
            mac = hex(_uuid.getnode())[2:]
            if not hw["bios"]:
                hw["bios"] = hashlib.sha256(f"mac_bios_{mac}".encode()).hexdigest()
            elif not hw["disk"]:
                hw["disk"] = hashlib.sha256(f"mac_disk_{mac}".encode()).hexdigest()
        except Exception:
            pass

    return hw

def get_stored_device_token():
    """Reads device token from file or registry."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                t = f.read().strip()
                if t:
                    return t
        except Exception:
            pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_UNBLOCKNET, 0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, "DeviceToken")
            if val:
                return str(val).strip()
    except Exception:
        pass
    return None

def save_stored_device_token(token):
    """Saves device token locally to file and registry."""
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token.strip())
    except Exception:
        pass
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_UNBLOCKNET) as k:
            winreg.SetValueEx(k, "DeviceToken", 0, winreg.REG_SZ, token.strip())
    except Exception:
        pass

def _api_request(endpoint, data=None, token=None, timeout=5):
    """Low-level direct HTTP request to VPS API (bypassing any local proxy)."""
    import urllib.request
    url = f"{SERVER_API_URL}{endpoint}"
    headers = {
        "User-Agent": "Unblocknet-Client/2.5",
        "Accept": "application/json"
    }
    cur_token = token or get_stored_device_token()
    if cur_token:
        headers["Authorization"] = f"Bearer {cur_token}"

    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            return err_data
        except Exception:
            return {"status": "error", "error": f"http_{e.code}", "message": str(e)}
    except Exception as e:
        return {"status": "error", "error": "network_error", "message": str(e)}

def sync_identity(force_register=False):
    """
    Syncs with server: registers device if needed, fetches subscription,
    active device limit, personal VLESS node and owner status.
    """
    token = get_stored_device_token()
    if not token or force_register:
        hw = get_device_hwid()
        import platform
        name = platform.node() or "Windows-PC"
        res = _api_request("/api/register", data={"hw": hw, "name": name, "version": "2.5"}, timeout=6)
        if res.get("status") == "ok" and res.get("token"):
            token = res["token"]
            save_stored_device_token(token)
            return res
        return res

    res = _api_request("/api/me", token=token, timeout=5)
    # If token was invalidated or deleted on server, re-register seamlessly
    if res.get("error") in ("unauthorized", "banned") and not force_register:
        return sync_identity(force_register=True)
    return res

def fetch_server_config(timeout=3):
    """Downloads public nodes, routing and adblock lists from VPS API."""
    res = _api_request("/api/config", timeout=timeout)
    if res.get("status") == "ok" and "config" in res:
        return res["config"]
    return None

def fetch_subscription_status(client_id=None, timeout=4):
    """Fetches user profile, active subscription and pricing plans."""
    res = sync_identity()
    if res.get("status") == "ok":
        sub = res.get("subscription", {})
        sub["is_owner"] = res.get("is_owner", False)
        return sub, res.get("plans")
    return None, None

def create_payment_order(plan_id, client_id=None, timeout=5):
    """Requests a new YooMoney payment order and URL from VPS API."""
    res = _api_request("/api/payment/create", data={"plan_id": plan_id}, timeout=timeout)
    if res.get("status") == "ok":
        return True, res.get("payment_url"), res.get("order_id"), res.get("plan")
    return False, res.get("message", "Ошибка создания заказа"), None, None

def activate_trial_period(client_id=None, timeout=5):
    """Activates 3-day free trial on the server."""
    res = _api_request("/api/trial", data={}, timeout=timeout)
    if res.get("status") == "ok":
        # Update local node UUID if granted
        if res.get("node") and res["node"].get("uuid"):
            settings = load_settings()
            settings["client_uuid"] = res["node"]["uuid"]
            save_settings(settings)
        return True, res.get("message", "Пробный период активирован!")
    return False, res.get("message", "Не удалось активировать пробный период")

def request_owner_email_code(email, timeout=6):
    """Requests a 6-digit confirmation code sent to owner email."""
    res = _api_request("/api/auth/email/request", data={"email": email}, timeout=timeout)
    if res.get("status") == "ok":
        return True, res.get("message", f"Код отправлен на {email}")
    return False, res.get("message", "Ошибка отправки кода")

def activate_code(code, timeout=6):
    """Activates an 8-digit promo, 6-digit OTP, or developer email / master key."""
    res = _api_request("/api/activate", data={"code": code.strip()}, timeout=timeout)
    if res.get("status") == "ok":
        if res.get("node") and res["node"].get("uuid"):
            settings = load_settings()
            settings["client_uuid"] = res["node"]["uuid"]
            save_settings(settings)
        return True, res.get("message", "Код успешно активирован!"), res
    return False, res.get("message", "Код или email недействителен"), None

def send_diagnostic_report(title="Отчет об ошибке клиента", detail="Пользователь запросил проверку"):
    """Collects recent client logs, system info and sends an issue to GitHub via VPS API."""
    import platform
    xray_log_tail = ""
    xray_log_path = os.path.join(USER_DATA_DIR, "xray.log")
    try:
        if os.path.exists(xray_log_path):
            with open(xray_log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                xray_log_tail = "".join(lines[-40:])
    except Exception:
        pass

    try:
        from vpn_updater import CURRENT_VERSION
        app_ver = CURRENT_VERSION
    except Exception:
        app_ver = "2.6.1"

    payload = {
        "title": str(title)[:140],
        "detail": str(detail)[:3500],
        "xray_log": xray_log_tail[:7000],
        "app_version": app_ver,
        "os_info": f"{platform.system()} {platform.release()} (Build {platform.version()})",
        "device_name": platform.node() or "Windows-PC"
    }

    res = _api_request("/api/report_error", data=payload, timeout=8)
    if res.get("status") == "ok":
        return True, res.get("issue_url", "Отчет отправлен разработчику")
    return False, res.get("message", "Не удалось отправить отчет")

def sync_add_domain_to_server(domain, mode="proxy", timeout=4):
    res = _api_request("/api/domains/add", data={"domain": domain, "mode": mode}, timeout=timeout)
    return res.get("status") == "ok", res.get("message", "Синхронизировано")

def toggle_server_adblock(enabled, timeout=4):
    res = _api_request("/api/adblock/toggle", data={"enabled": enabled}, timeout=timeout)
    return res.get("status") == "ok", res.get("adblock_enabled", enabled)

def load_settings():
    res = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res.update(data)
        except Exception:
            pass

    # Try fetching fresh settings from VPS API
    server_cfg = fetch_server_config(timeout=2.5)
    if server_cfg:
        if "custom_proxy_domains" in server_cfg:
            for d in server_cfg["custom_proxy_domains"]:
                if d not in res.get("custom_proxy_domains", []):
                    res["custom_proxy_domains"].append(d)
        if "custom_direct_domains" in server_cfg:
            for d in server_cfg["custom_direct_domains"]:
                if d not in res.get("custom_direct_domains", []):
                    res["custom_direct_domains"].append(d)
        if "adblock_enabled" in server_cfg:
            res["adblock_enabled"] = server_cfg["adblock_enabled"]
        if "adblock_domains" in server_cfg:
            res["adblock_domains"] = server_cfg["adblock_domains"]
        save_settings(res)

    return res

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving settings:", e)


# ---------------------------------------------------------------------------
# TLS ClientHello Fragmentation Relay (in-process)
# ---------------------------------------------------------------------------
class FragmentRelay:
    def __init__(self, targets):
        self.targets = targets  # {local_port: (remote_host, remote_port)}
        self.running = False
        self.sockets = []

    def frag_send(self, sock, data):
        i = 0
        for off in range(0, min(len(data), 24), 4):
            sock.sendall(data[off:off + 4])
            time.sleep(0.008)
            i = off + 4
        if data[i:]:
            sock.sendall(data[i:])

    def pump(self, src, dst, first_frag):
        first = True
        try:
            while self.running:
                d = src.recv(65536)
                if not d:
                    break
                if first and first_frag:
                    first = False
                    self.frag_send(dst, d)
                else:
                    dst.sendall(d)
        except OSError:
            pass
        finally:
            try:
                dst.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    def handle(self, conn, target):
        try:
            dst = socket.create_connection(target, timeout=10)
        except OSError:
            try:
                conn.close()
            except OSError:
                pass
            return
        t = threading.Thread(target=self.pump, args=(conn, dst, True), daemon=True)
        t.start()
        self.pump(dst, conn, False)
        for s in (conn, dst):
            try:
                s.close()
            except OSError:
                pass

    def serve(self, listener, target):
        listener.settimeout(1.0)
        while self.running:
            try:
                conn, _ = listener.accept()
                threading.Thread(target=self.handle, args=(conn, target), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def start(self):
        self.running = True
        self.sockets = []
        for port, target in self.targets.items():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', port))
                s.listen(128)
                self.sockets.append(s)
                t = threading.Thread(target=self.serve, args=(s, target), daemon=True)
                t.start()
            except OSError as e:
                print(f"Relay port {port} error: {e}")

    def stop(self):
        self.running = False
        for s in self.sockets:
            try:
                s.close()
            except OSError:
                pass
        self.sockets.clear()


# ---------------------------------------------------------------------------
# Windows System Proxy Controller
# ---------------------------------------------------------------------------
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

def set_windows_proxy(enable=True, proxy_server="127.0.0.1:10897", bypass="<local>;localhost;127.*;192.168.*;10.*"):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, bypass)
        else:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        notify_proxy_change()
        return True
    except Exception as e:
        print("Error changing Windows proxy:", e)
        return False

def get_windows_proxy_status():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
        winreg.CloseKey(key)
        return bool(enable), str(server)
    except Exception:
        return False, ""


# ---------------------------------------------------------------------------
# VPN Engine Controller
# ---------------------------------------------------------------------------
class VpnEngine:
    def __init__(self):
        self.settings = load_settings()
        self.xray_proc = None
        self.relay = None
        self.is_connected = False
        self._lock = threading.Lock()
        
        # Cleanup proxy on process exit
        atexit.register(self.disconnect)

    def generate_xray_config(self, node_key):
        nodes_dict = self.settings.get("nodes", {})
        node = nodes_dict.get(node_key) or NODES.get(node_key) or list(NODES.values())[0]
        
        # Merge built-in rules with user custom rules
        direct_domains = [
            "geosite:category-ru",
            "geosite:private",
            "regexp:.*\\.ru$",
            "regexp:.*\\.su$",
            "regexp:.*\\.xn--p1ai$"
        ]
        for d in self.settings.get("custom_direct_domains", []):
            d = d.strip()
            if d and d not in direct_domains:
                direct_domains.append(f"domain:{d}")

        target_host = node.get("vps_host", "193.233.138.42")

        # DPI of RU ISPs selectively drops some uTLS fingerprints (chrome/edge/ios/android/randomized).
        # firefox & safari pass reliably on both ports -> 4 channels + auto-failover balancer.
        # Determine personal client UUID from server identity
        active_uuid = self.settings.get("client_uuid") or node.get("uuid")
        if not active_uuid:
            try:
                id_res = sync_identity()
                if id_res.get("node") and id_res["node"].get("uuid"):
                    active_uuid = id_res["node"]["uuid"]
                    self.settings["client_uuid"] = active_uuid
                    save_settings(self.settings)
            except Exception:
                pass
        if not active_uuid:
            active_uuid = "04756662-2f98-44ad-a53a-369d29118670"

        channels = [
            ("p-443-ff", 443, "speed.cloudflare.com", "firefox"),
            ("p-2053-sf", 2053, "azure.microsoft.com", "safari"),
            ("p-2053-ff", 2053, "azure.microsoft.com", "firefox"),
            ("p-443-sf", 443, "speed.cloudflare.com", "safari"),
        ]
        proxy_outbounds = []
        for tag, port, sni, fp in channels:
            proxy_outbounds.append({
                "tag": tag,
                "protocol": "vless",
                "settings": {"vnext": [{
                    "address": target_host,
                    "port": port,
                    "users": [{"id": active_uuid, "encryption": "none", "flow": node["flow"]}]
                }]},
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "serverName": sni,
                        "fingerprint": fp,
                        "publicKey": node["pbk"],
                        "shortId": node["sid"],
                        "spiderX": "/"
                    }
                }
            })

        adblock_list = ["geosite:category-ads-all"]
        if self.settings.get("adblock_domains"):
            for ad in self.settings.get("adblock_domains", []):
                ad = ad.strip()
                if ad:
                    adblock_list.append(f"domain:{ad}")

        routing_rules = [
            {
                "type": "field",
                "outboundTag": "block",
                "port": "443",
                "network": "udp"
            },
            {
                "type": "field",
                "outboundTag": "block",
                "ip": ["::/0"]
            }
        ]

        if self.settings.get("adblock_enabled", True):
            routing_rules.append({
                "type": "field",
                "outboundTag": "block",
                "domain": adblock_list
            })

        routing_rules.extend([
            {
                "type": "field",
                "outboundTag": "direct",
                "domain": direct_domains
            },
            {
                "type": "field",
                "outboundTag": "direct",
                "ip": [
                    "10.0.0.0/8",
                    "172.16.0.0/12",
                    "192.168.0.0/16",
                    "127.0.0.0/8"
                ]
            },
            {
                "type": "field",
                "balancerTag": "auto",
                "network": "tcp,udp"
            }
        ])

        cfg = {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "tag": "http-in",
                    "listen": "127.0.0.1",
                    "port": 10897,
                    "protocol": "http",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls", "quic"],
                        "routeOnly": True
                    }
                },
                {
                    "tag": "socks-in",
                    "listen": "127.0.0.1",
                    "port": 10898,
                    "protocol": "socks",
                    "settings": {
                        "auth": "noauth",
                        "udp": True
                    },
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls", "quic"],
                        "routeOnly": True
                    }
                }
            ],
            "observatory": {
                "subjectSelector": ["p-"],
                "probeURL": "https://www.gstatic.com/generate_204",
                "probeInterval": "30s",
                "enableConcurrency": True
            },
            "outbounds": proxy_outbounds + [
                {
                    "tag": "direct",
                    "protocol": "freedom",
                    "settings": {
                        "domainStrategy": "UseIPv4"
                    }
                },
                {
                    "tag": "block",
                    "protocol": "blackhole"
                }
            ],
            "routing": {
                "domainStrategy": "AsIs",
                "rules": routing_rules,
                "balancers": [
                    {
                        "tag": "auto",
                        "selector": ["p-"],
                        "strategy": {"type": "leastPing"},
                        "fallbackTag": "p-443-ff"
                    }
                ]
            }
        }

        with open(RUNTIME_CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return RUNTIME_CONFIG

    def connect(self, node_key=None):
        with self._lock:
            if self.is_connected:
                self._disconnect_unlocked()

            if not node_key:
                node_key = self.settings.get("selected_node", "443-frag")

            # 0. Free ports and clean stale DNS/proxy cache before connecting
            self_heal_network()
            time.sleep(0.2)

            # 1. Write dynamic Xray runtime config
            config_file = self.generate_xray_config(node_key)

            # 2. Spawn local Xray core
            xray_path = get_xray_path()
            if not os.path.exists(xray_path):
                raise FileNotFoundError(f"xray.exe не найден по пути: {xray_path}")

            xray_log_path = os.path.join(USER_DATA_DIR, "xray.log")
            try:
                xray_log_file = open(xray_log_path, "w", encoding="utf-8")
            except Exception:
                xray_log_file = subprocess.DEVNULL

            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            # Ensure asset location contains geosite.dat / geoip.dat
            asset_dir = BUNDLE_DIR
            if not os.path.exists(os.path.join(asset_dir, "geosite.dat")):
                for cand in [APP_DIR, os.path.join(APP_DIR, "v2rayN", "v2rayN-windows-64", "bin", "Xray"), os.path.join(USER_DATA_DIR, "bin")]:
                    if os.path.exists(os.path.join(cand, "geosite.dat")):
                        asset_dir = cand
                        break

            env = os.environ.copy()
            env["xray.location.asset"] = asset_dir
            env["XRAY_LOCATION_ASSET"] = asset_dir

            self.xray_proc = subprocess.Popen(
                [xray_path, "run", "-c", config_file],
                stdout=xray_log_file,
                stderr=subprocess.STDOUT,
                cwd=asset_dir,
                env=env,
                creationflags=creationflags
            )

            # Wait for Xray to bind and start listening on port 10897
            port_ready = False
            start_wait = time.time()
            while time.time() - start_wait < 5.0:
                if self.xray_proc.poll() is not None:
                    break
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    s.connect(("127.0.0.1", 10897))
                    s.close()
                    port_ready = True
                    break
                except Exception:
                    time.sleep(0.2)

            if not port_ready:
                ret = self.xray_proc.poll()
                err_detail = ""
                try:
                    if os.path.exists(xray_log_path):
                        with open(xray_log_path, "r", encoding="utf-8", errors="ignore") as lf:
                            err_detail = lf.read().strip()
                except Exception:
                    pass
                self._disconnect_unlocked()
                err_msg = f"Xray не смог запуститься на порту 10897 (код: {ret})"
                if err_detail:
                    last_lines = " | ".join(err_detail.splitlines()[-3:])
                    err_msg += f": {last_lines}"
                raise RuntimeError(err_msg)

            # 3. Enable Windows System Proxy
            set_windows_proxy(True)

            # 4. Flush DNS and refresh system proxy cache
            flush_dns_cache()
            notify_proxy_change()

            self.is_connected = True
            self.settings["selected_node"] = node_key
            save_settings(self.settings)
            return True

    def _disconnect_unlocked(self):
        # 1. Turn off Windows system proxy first
        set_windows_proxy(False)

        # 2. Kill xray process
        if self.xray_proc:
            try:
                self.xray_proc.terminate()
                self.xray_proc.wait(timeout=2.0)
            except Exception:
                try:
                    self.xray_proc.kill()
                except Exception:
                    pass
            self.xray_proc = None

        # 3. Guarantee ports are free and caches are cleared
        free_vpn_ports()
        flush_dns_cache()
        notify_proxy_change()

        self.is_connected = False

    def disconnect(self):
        with self._lock:
            self._disconnect_unlocked()
            return True

    def get_status(self):
        with self._lock:
            if not self.is_connected:
                return {"connected": False, "node": self.settings.get("selected_node")}
            # Verify process is still alive
            if self.xray_proc and self.xray_proc.poll() is not None:
                self._disconnect_unlocked()
                return {"connected": False, "node": self.settings.get("selected_node")}
            return {
                "connected": True,
                "node": self.settings.get("selected_node"),
                "node_info": NODES.get(self.settings.get("selected_node"))
            }

    def add_direct_domain(self, domain):
        domain = domain.strip().lower()
        if domain and domain not in self.settings["custom_direct_domains"]:
            self.settings["custom_direct_domains"].append(domain)
            save_settings(self.settings)
            threading.Thread(target=sync_add_domain_to_server, args=(domain, "direct"), daemon=True).start()
            if self.is_connected:
                # Reload connection to apply routing rule
                self.connect(self.settings["selected_node"])

    def remove_direct_domain(self, domain):
        if domain in self.settings["custom_direct_domains"]:
            self.settings["custom_direct_domains"].remove(domain)
            save_settings(self.settings)
            if self.is_connected:
                self.connect(self.settings["selected_node"])

    def add_proxy_domain(self, domain):
        domain = domain.strip().lower()
        if domain and domain not in self.settings["custom_proxy_domains"]:
            self.settings["custom_proxy_domains"].append(domain)
            save_settings(self.settings)
            threading.Thread(target=sync_add_domain_to_server, args=(domain, "proxy"), daemon=True).start()
            if self.is_connected:
                self.connect(self.settings["selected_node"])

    def remove_proxy_domain(self, domain):
        if domain in self.settings["custom_proxy_domains"]:
            self.settings["custom_proxy_domains"].remove(domain)
            save_settings(self.settings)
            if self.is_connected:
                self.connect(self.settings["selected_node"])


def apply_webrtc_protection():
    """
    Sets WebRtcIPHandlingPolicy = disable_non_proxied_udp in Chrome and Edge
    User Data Preferences to eliminate WebRTC STUN UDP leaks.
    """
    results = {}
    localapp = os.environ.get('LOCALAPPDATA', '')
    if not localapp:
        return results

    targets = {
        'Chrome': os.path.join(localapp, 'Google', 'Chrome', 'User Data', 'Default', 'Preferences'),
        'Edge': os.path.join(localapp, 'Microsoft', 'Edge', 'User Data', 'Default', 'Preferences')
    }

    for name, pref_path in targets.items():
        if os.path.exists(pref_path):
            try:
                with open(pref_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    continue
                if 'webrtc' not in data or not isinstance(data['webrtc'], dict):
                    data['webrtc'] = {}
                data['webrtc']['ip_handling_policy'] = 'disable_non_proxied_udp'
                with open(pref_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                results[name] = True
            except Exception as e:
                results[name] = False
        else:
            results[name] = None
    return results
