import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, subprocess, base64

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Update subDomain to empty string so it listens on all domains/IPs without 403
c.execute("UPDATE settings SET value='' WHERE key='subDomain'")
conn.commit()

# Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])

import time
time.sleep(2)

# Test fetching subscription locally
p = subprocess.run(["curl", "-k", "-s", "https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m"], capture_output=True, text=True)
print("Response len:", len(p.stdout))
if len(p.stdout) > 0:
    try:
        decoded = base64.b64decode(p.stdout.strip()).decode('utf-8')
        print("Decoded link:", decoded)
    except Exception as e:
        print("Raw stdout:", p.stdout[:200])
else:
    print("Empty response, stderr:", p.stderr)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
