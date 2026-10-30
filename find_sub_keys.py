import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["strings", "/usr/local/x-ui/x-ui"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "subURI" in line or "subDomain" in line or "subPort" in line or "subEnable" in line or "subUpdates" in line:
        print(line)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
