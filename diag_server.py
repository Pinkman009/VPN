import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["systemctl", "status", "x-ui", "--no-pager"], capture_output=True, text=True)
print(p.stdout)
print(p.stderr)

p2 = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
for line in p2.stdout.splitlines():
    if "443" in line or "2053" in line or "xray" in line:
        print(line)

p3 = subprocess.run(["journalctl", "-u", "x-ui", "-n", "30", "--no-pager"], capture_output=True, text=True)
print("=== LOGS ===")
print(p3.stdout)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
