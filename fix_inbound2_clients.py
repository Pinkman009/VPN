import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess, time

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

in2 = c.execute("SELECT settings FROM inbounds WHERE id=2").fetchone()[0]
cfg2 = json.loads(in2)
cfg2['clients'][0]['email'] = '79500490409-2053'

c.execute("UPDATE inbounds SET settings=? WHERE id=2", (json.dumps(cfg2),))
conn.commit()

subprocess.run(['systemctl', 'restart', 'x-ui'])
time.sleep(2)

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
