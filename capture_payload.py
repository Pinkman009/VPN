from run_remote import run_script_on_vps

script = """
import subprocess
p = subprocess.run(['tcpdump', '-nn', '-X', '-s', '1500', '-c', '6', '-i', 'any', 'host', '92.62.63.152 and port 443 and tcp[tcpflags] & tcp-push != 0'], capture_output=True, text=True, timeout=10)
print(p.stdout)
"""

run_script_on_vps(script)
