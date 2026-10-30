import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["strings", "/usr/local/x-ui/x-ui"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "/panel/" in line or "/login" in line or "webBasePath" in line:
        print(line[:120])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
