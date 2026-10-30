import subprocess
from run_remote import run_script_on_vps

script = """
import subprocess
ps = subprocess.getoutput("ps aux")
for line in ps.splitlines():
    if "x-ui" in line or "xray" in line:
        print(line)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
