import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

print("=== ACCESS LOG ===")
print(run("tail -n 50 /var/log/xray/access.log"))

print("\n=== ERROR LOG ===")
print(run("tail -n 50 /var/log/xray/error.log"))
'''

run_script_on_vps(script)
