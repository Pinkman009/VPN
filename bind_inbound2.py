import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess, time

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# 1. Add client 1 to inbound 2 in client_inbounds
exists = c.execute("SELECT count(*) FROM client_inbounds WHERE client_id=1 AND inbound_id=2").fetchone()[0]
if not exists:
    c.execute("INSERT INTO client_inbounds (client_id, inbound_id, flow_override, created_at) VALUES (1, 2, 'xtls-rprx-vision', 1789850075593)")
    conn.commit()
    print("Added client 1 to inbound 2 in client_inbounds!")

# 2. Clean up rogue row 2 in client_traffics
c.execute("DELETE FROM client_traffics WHERE inbound_id=2")
conn.commit()

# 3. Ensure inbound 2 settings has identical email '79500490409' as client 1
in1 = c.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()[0]
c.execute("UPDATE inbounds SET settings=? WHERE id=2", (in1,))
conn.commit()

# 4. Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])
time.sleep(3)

# 5. Check active config.json
with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)

for ib in cfg.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        clients = ib.get('settings', {}).get('clients', [])
        print(f"Port {ib['port']} clients count: {len(clients)}")
        for cl in clients:
            print(f"   id: {cl.get('id')}, email: {cl.get('email')}, flow: {cl.get('flow')}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
