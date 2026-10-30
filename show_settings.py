import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["/usr/local/x-ui/x-ui", "setting", "-show"], capture_output=True, text=True)
print(p.stdout)
print(p.stderr)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
