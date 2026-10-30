import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["journalctl", "-u", "x-ui", "-n", "30", "--no-pager"], capture_output=True, text=True)
print(p.stdout)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
