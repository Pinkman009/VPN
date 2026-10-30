import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["systemctl", "status", "x-ui", "--no-pager"], capture_output=True, text=True)
print(p.stdout)
print(p.stderr)

p2 = subprocess.run(["curl", "-k", "-v", "https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m"], capture_output=True, text=True)
print("CURL STDOUT:", p2.stdout)
print("CURL STDERR:", p2.stderr)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
