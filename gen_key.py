import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["/usr/local/x-ui/bin/xray-linux-amd64", "x25519"], capture_output=True, text=True)
print(p.stdout)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
