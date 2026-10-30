import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

# Check error.log for 49714
print("Error log line:")
print(subprocess.run("grep 49714 /var/log/x-ui/error.log", shell=True, capture_output=True, text=True).stdout)

# Check recent connections to port 443 vs 2053
print("Conntrack or ss:")
print(subprocess.run("ss -tn '( dport = :443 or dport = :2053 )'", shell=True, capture_output=True, text=True).stdout)
'''

run_script_on_vps(script)
