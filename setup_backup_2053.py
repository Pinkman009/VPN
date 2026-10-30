import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Get client from inbound 1
row = c.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()[0]
s = json.loads(row)
client = s["clients"][0].copy()
client["email"] = "79500490409-2053"

s2 = {
    "clients": [client],
    "decryption": "none"
}

c.execute("UPDATE inbounds SET settings=? WHERE id=2", (json.dumps(s2),))

# Insert into client_traffics
exists = c.execute("SELECT count(*) FROM client_traffics WHERE email='79500490409-2053'").fetchone()[0]
if not exists:
    c.execute(\"\"\"
    INSERT INTO client_traffics (inbound_id, enable, email, up, down, expiry_time, total, reset)
    VALUES (2, 1, '79500490409-2053', 0, 0, 0, 0, 0)
    \"\"\")

conn.commit()
subprocess.run(["systemctl", "restart", "x-ui"])

import time
time.sleep(2)

with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)
for ib in cfg.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        print(f"Port {ib['port']} protocol={ib['protocol']} clients={len(ib.get('settings', {}).get('clients', []))}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
