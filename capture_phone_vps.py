from run_remote import run_script_on_vps

script = """
import subprocess
# Run tcpdump on port 443 and 2053 for 5 seconds
p = subprocess.run(['tcpdump', '-nn', '-c', '20', '-i', 'any', 'host', '92.62.63.152 and (port 443 or port 2053)'], capture_output=True, text=True, timeout=10)
print(p.stdout)
"""

run_script_on_vps(script)
