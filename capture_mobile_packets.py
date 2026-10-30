import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()

print("Capturing 10 packets from 92.62.63.152 (timeout 6s)...")
try:
    res = subprocess.run("timeout 6 tcpdump -nn -i any 'host 92.62.63.152' -c 15", shell=True, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
except Exception as e:
    print("Error:", e)
'''

run_script_on_vps(script)
