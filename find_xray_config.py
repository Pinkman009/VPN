import sys
from run_remote import run_script_on_vps

script = """
import os, subprocess

p = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "xray" in line:
        print(line)

for pth in ["/usr/local/x-ui/bin/config.json", "/etc/x-ui/config.json", "/usr/local/x-ui/config.json", "/usr/local/x-ui/bin/run.sh"]:
    if os.path.exists(pth):
        print("Found:", pth)
        with open(pth, 'r') as f:
            print(f.read()[:1000])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
