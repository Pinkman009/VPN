import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Get settings from Inbound 1
s1 = c.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()[0]

# Put exact same settings into Inbound 2
c.execute("UPDATE inbounds SET settings=? WHERE id=2", (s1,))
conn.commit()

# Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])

import time
time.sleep(2)

# Check config.json
with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)
for ib in cfg.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        print(f"Port {ib['port']} clients count: {len(ib.get('settings', {}).get('clients', []))}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
