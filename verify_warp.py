import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess, time

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() + (" " + r.stderr.strip() if r.stderr.strip() else "")
    except Exception as e:
        return f"ERROR: {e}"

time.sleep(3)
print("=== WARP STATUS ===")
print(run("warp-cli --accept-tos status"))

print("\n=== SYSTEMCTL STATUS / ENABLE ===")
print(run("systemctl enable warp-svc"))

print("\n=== SOCKS5 TEST via 127.0.0.1:40000 ===")
print(run("curl -x socks5h://127.0.0.1:40000 -s --max-time 10 https://cloudflare.com/cdn-cgi/trace | head -15"))

print("\n=== IP COMPARISON ===")
print("VPS direct IP:", run("curl -s --max-time 10 https://api.ipify.org"))
print("WARP proxy IP:", run("curl -x socks5h://127.0.0.1:40000 -s --max-time 10 https://api.ipify.org"))
'''

run_script_on_vps(script)
