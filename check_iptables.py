import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

print("=== UFW STATUS ===")
print(run("ufw status"))

print("\n=== RECENT UFW BLOCKS FROM DMESG ===")
print(run("dmesg | grep -i ufw | tail -15"))

print("\n=== RECENT SYSLOG UFW BLOCKS ===")
print(run("grep -i ufw /var/log/syslog | tail -15 2>/dev/null || echo no syslog"))

print("\n=== DISABLE UFW TEMPORARILY TO TEST IF UFW WAS BLOCKING ===")
print(run("ufw disable"))
'''

run_script_on_vps(script)
