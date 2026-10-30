import base64
from run_remote import run_script_on_vps

script = """
import subprocess, base64

res = subprocess.run(['curl', '-k', '-s', '-H', 'Host: 193.233.138.42', 'https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'], stdout=subprocess.PIPE)
decoded = base64.b64decode(res.stdout).decode()
for line in decoded.splitlines():
    print(line)
"""

run_script_on_vps(script)
