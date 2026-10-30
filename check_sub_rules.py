from run_remote import run_script_on_vps

script = """
import subprocess
print(subprocess.run(['grep', '-rn', 'subJsonRoutingRules', '/usr/local/x-ui/'], capture_output=True, text=True).stdout)
print(subprocess.run(['grep', '-rn', 'subClashRules', '/usr/local/x-ui/'], capture_output=True, text=True).stdout)
"""

run_script_on_vps(script)
