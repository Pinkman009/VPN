import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() + (" " + r.stderr.strip() if r.stderr.strip() else "")
    except Exception as e:
        return f"ERROR: {e}"

print("=== Setting up UFW firewall rules ===")
# Set defaults
print(run("ufw default deny incoming"))
print(run("ufw default allow outgoing"))

# Allow SSH first!
print(run("ufw allow 22/tcp comment 'SSH'"))

# Allow VPN ports
print(run("ufw allow 443/tcp comment 'VLESS Reality 443'"))
print(run("ufw allow 2053/tcp comment 'VLESS Reality 2053'"))

# Allow Subscription port
print(run("ufw allow 2096/tcp comment 'Subscription 2096'"))

# Allow 3X-UI Panel port
print(run("ufw allow 8443/tcp comment '3X-UI Panel 8443'"))

# Enable firewall
print(run("ufw --force enable"))

print("\n=== UFW STATUS ===")
print(run("ufw status verbose"))
'''

run_script_on_vps(script)
