import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess, time

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    out = r.stdout.strip()
    err = r.stderr.strip()
    return out + ("\n" + err if err else "")

# Check warp-cli help to find correct flags
print("=== warp-cli registration help ===")
print(run("warp-cli registration new --help"))

print()
print("=== warp-cli --help (top-level) ===")
print(run("warp-cli --help 2>&1 | head -30"))
'''

run_script_on_vps(script)
