import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return r.stdout.strip()[:200]
    except Exception as e:
        return f"ERROR: {e}"

targets = [
    "dl.google.com",
    "swdist.apple.com",
    "gateway.icloud.com",
    "www.microsoft.com",
    "www.samsung.com"
]

for t in targets:
    res = run(f"curl -s --connect-timeout 3 -o /dev/null -w '%{{http_code}} %{{time_total}}s' https://{t}")
    print(f"{t}: {res}")
'''

run_script_on_vps(script)
