import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

remote_code = '''cat << 'EOF' > /tmp/update_routing.py
import json, os, subprocess, sqlite3

CONFIG_JSON = "/usr/local/x-ui/bin/config.json"
DATA_FILE = "/etc/teletok/server_config.json"
DB_PATH = "/etc/x-ui/x-ui.db"
XRAY_BIN = "/usr/local/x-ui/bin/xray-linux-amd64"

# 1. Update /etc/teletok/server_config.json
with open(DATA_FILE, "r", encoding="utf-8") as f:
    cfg = json.load(f)

# Google services must NOT be routed through Cloudflare WARP!
google_domains = {"aistudio.google.com", "gemini.google.com", "generativelanguage.googleapis.com"}
cfg["custom_proxy_domains"] = [d for d in cfg.get("custom_proxy_domains", []) if d not in google_domains]

# Clean adblock domains (remove paths with slashes)
cfg["adblock_domains"] = [d for d in cfg.get("adblock_domains", []) if "/" not in d]

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

# 2. Update x-ui config.json
with open(CONFIG_JSON, "r", encoding="utf-8") as f:
    xcfg = json.load(f)

warp_domains = [f"domain:{d.strip()}" for d in cfg["custom_proxy_domains"] if d.strip()]
adblock_domains = ["geosite:category-ads-all"] + [f"domain:{d.strip()}" for d in cfg["adblock_domains"] if d.strip()]

rules = [
    {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
    {"type": "field", "outboundTag": "blocked", "ip": ["geoip:private"]},
    {"type": "field", "outboundTag": "blocked", "protocol": ["bittorrent"]},
    {"type": "field", "outboundTag": "blocked", "port": "443", "network": "udp"},
    {"type": "field", "outboundTag": "blocked", "domain": adblock_domains},
    {"type": "field", "outboundTag": "warp", "domain": warp_domains}
]

xcfg["routing"]["rules"] = rules

with open(CONFIG_JSON, "w", encoding="utf-8") as f:
    json.dump(xcfg, f, indent=2, ensure_ascii=False)

# Update SQLite template
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'")
    row = c.fetchone()
    if row:
        t = json.loads(row[0])
        t["routing"]["rules"] = rules
        c.execute("UPDATE settings SET value=? WHERE key='xrayTemplateConfig'", (json.dumps(t),))
        conn.commit()
    conn.close()

# Test and reload
res = subprocess.run([XRAY_BIN, "-test", "-c", CONFIG_JSON], capture_output=True, text=True)
if res.returncode == 0:
    subprocess.run(["systemctl", "restart", "x-ui"], check=True)
    subprocess.run(["systemctl", "restart", "teletok-api"], check=True)
    print("SUCCESS: VPS updated and services restarted!")
else:
    print("CONFIG TEST FAILED:", res.stderr)
EOF
python3 /tmp/update_routing.py
'''

stdin, stdout, stderr = ssh.exec_command(remote_code)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
