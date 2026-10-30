import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess, os, json

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() + (" " + r.stderr.strip() if r.stderr.strip() else "")
    except:
        return "ERROR"

print("=== 1. BBR STATUS ===")
print("Current congestion:", run("sysctl net.ipv4.tcp_congestion_control"))
print("Available:", run("sysctl net.ipv4.tcp_available_congestion_control"))
print("Default qdisc:", run("sysctl net.core.default_qdisc"))

print()
print("=== 2. KEY SYSCTL VALUES ===")
keys = [
    "net.core.somaxconn", "net.ipv4.tcp_fastopen", "net.ipv4.tcp_max_syn_backlog",
    "net.core.rmem_max", "net.core.wmem_max", "net.ipv4.tcp_rmem", "net.ipv4.tcp_wmem",
    "net.ipv4.tcp_mtu_probing", "net.ipv4.tcp_slow_start_after_idle"
]
for key in keys:
    print("  " + run("sysctl " + key))

print()
print("=== 3. LISTENING PORTS ===")
print(run("ss -tlnp"))

print()
print("=== 4. WARP STATUS ===")
print("warp-cli:", run("which warp-cli 2>/dev/null || echo NOT_INSTALLED"))
print("warp svc:", run("systemctl is-active warp-svc 2>/dev/null || echo NOT_RUNNING"))

print()
print("=== 5. FIREWALL ===")
print(run("ufw status 2>/dev/null || echo ufw_not_found"))

print()
print("=== 6. KERNEL ===")
print(run("uname -r"))

print()
print("=== 7. XRAY TEMPLATE FROM DB ===")
import sqlite3
conn = sqlite3.connect("/etc/x-ui/x-ui.db")
c = conn.cursor()
tmpl = c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'").fetchone()
if tmpl:
    print(tmpl[0][:4000])
else:
    print("NO TEMPLATE FOUND")

print()
print("=== 8. INBOUNDS DETAIL ===")
for row in c.execute("SELECT id, port, protocol, remark, stream_settings FROM inbounds WHERE enable=1").fetchall():
    ib_id, port, proto, remark, stream_str = row
    stream = json.loads(stream_str)
    reality = stream.get("realitySettings", {})
    print(f"  ID={ib_id} Port={port} Proto={proto} Remark={remark}")
    print(f"    network={stream.get('network')}")
    print(f"    security={stream.get('security')}")
    print(f"    target={reality.get('target')}")
    print(f"    serverNames={reality.get('serverNames')}")
conn.close()
'''

run_script_on_vps(script)
