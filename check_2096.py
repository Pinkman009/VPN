from run_remote import run_script_on_vps

script = """
import subprocess
print('=== UFW STATUS ===')
print(subprocess.run(['ufw', 'status'], capture_output=True, text=True).stdout)

print('=== RECENT 2096 ACCESS IN NGINX / X-UI ===')
print(subprocess.run('grep 2096 /var/log/x-ui/access.log | tail -n 20', shell=True, capture_output=True, text=True).stdout)

print('=== LISTENING 2096 ===')
print(subprocess.run('ss -tulpn | grep 2096', shell=True, capture_output=True, text=True).stdout)
"""

run_script_on_vps(script)
