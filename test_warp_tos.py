import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() + (" " + r.stderr.strip() if r.stderr.strip() else "")
    except Exception as e:
        return f"ERROR: {e}"

print("=== Test 1: warp-cli --accept-tos registration new ===")
print(run("warp-cli --accept-tos registration new"))

print("\n=== Test 2: warp-cli --accept-tos mode proxy ===")
print(run("warp-cli --accept-tos mode proxy"))

print("\n=== Test 3: warp-cli --accept-tos proxy port 40000 ===")
print(run("warp-cli --accept-tos proxy port 40000"))

print("\n=== Test 4: warp-cli --accept-tos connect ===")
print(run("warp-cli --accept-tos connect"))

print("\n=== Test 5: status ===")
print(run("warp-cli --accept-tos status"))
'''

run_script_on_vps(script)
