from run_remote import run_script_on_vps

script = """
import subprocess

out = subprocess.check_output("strings /usr/local/x-ui/x-ui | grep -E 'sub.*403|sub.*Forbidden|subController|Subscription' | head -n 30", shell=True).decode(errors='replace')
print(out)
"""

run_script_on_vps(script)
