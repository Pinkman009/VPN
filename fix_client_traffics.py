import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("CLIENT TRAFFICS ROWS:")
for r in c.execute("SELECT * FROM client_traffics").fetchall():
    print(r)

# Duplicate client for inbound 2 if not exists
exists = c.execute("SELECT count(*) FROM client_traffics WHERE inbound_id=2").fetchone()[0]
if not exists:
    row = c.execute("SELECT inbound_id, enable, email, up, down, expiry_time, total, reset FROM client_traffics WHERE inbound_id=1").fetchone()
    c.execute(\"\"\"
    INSERT INTO client_traffics (inbound_id, enable, email, up, down, expiry_time, total, reset)
    VALUES (2, ?, ?, 0, 0, 0, 0, 0)
    \"\"\", (row[1], row[2]))
    conn.commit()
    print("Inserted client_traffics for inbound 2!")

subprocess.run(["systemctl", "restart", "x-ui"])

import time, json
time.sleep(2)

with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)
for ib in cfg.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        print(f"Port {ib['port']} clients count: {len(ib.get('settings', {}).get('clients', []))}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
