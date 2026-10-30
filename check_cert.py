import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["openssl", "x509", "-in", "/root/cert/ip/fullchain.pem", "-noout", "-text"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "Subject:" in line or "DNS:" in line or "IP Address:" in line:
        print(line)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
