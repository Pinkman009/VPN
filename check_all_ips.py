from run_remote import run_script_on_vps

script = """
import re
with open('/var/log/x-ui/access.log') as f:
    lines = f.readlines()

ips = {}
for line in lines:
    m = re.search(r'from (?:tcp:)?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line)
    if m:
        ip = m.group(1)
        ips[ip] = ips.get(ip, 0) + 1

for ip, count in sorted(ips.items(), key=lambda x: x[1], reverse=True):
    print(f'{ip}: {count}')
"""

run_script_on_vps(script)
