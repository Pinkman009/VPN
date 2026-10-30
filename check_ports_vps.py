from run_remote import run_script_on_vps

script = """
import subprocess
print(subprocess.run(['ss', '-tulpn'], capture_output=True, text=True).stdout)
"""

run_script_on_vps(script)
