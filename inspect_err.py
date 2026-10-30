from run_remote import run_script_on_vps

script = """
import subprocess
print(subprocess.run(['grep', 'processed invalid connection', '/var/log/x-ui/error.log'], capture_output=True, text=True).stdout[-2000:])
"""

run_script_on_vps(script)
