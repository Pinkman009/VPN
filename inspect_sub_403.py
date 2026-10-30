from run_remote import run_script_on_vps

script = """
import subprocess

out = subprocess.check_output('journalctl -u x-ui -n 50 --no-pager', shell=True).decode(errors='replace')
print(out)
"""

run_script_on_vps(script)
