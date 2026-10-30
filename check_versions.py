import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from run_remote import run_script_on_vps

script = """
import os, subprocess

print("X-UI binary version:")
p = subprocess.run(["/usr/local/x-ui/x-ui", "v"], capture_output=True, text=True)
print(p.stdout, p.stderr)

print("Xray version:")
p = subprocess.run(["/usr/local/x-ui/bin/xray-linux-amd64", "version"], capture_output=True, text=True)
print(p.stdout, p.stderr)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
