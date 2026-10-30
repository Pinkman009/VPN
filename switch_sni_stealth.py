import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess, time

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Inbound 1: swdist.apple.com:443
r1 = c.execute("SELECT stream_settings FROM inbounds WHERE id=1").fetchone()[0]
ss1 = json.loads(r1)
ss1["realitySettings"]["target"] = "swdist.apple.com:443"
ss1["realitySettings"]["serverNames"] = ["swdist.apple.com"]
c.execute("UPDATE inbounds SET stream_settings=? WHERE id=1", (json.dumps(ss1),))

# Inbound 2: www.samsung.com:443 (on port 2053)
r2 = c.execute("SELECT stream_settings FROM inbounds WHERE id=2").fetchone()[0]
ss2 = json.loads(r2)
ss2["realitySettings"]["target"] = "www.samsung.com:443"
ss2["realitySettings"]["serverNames"] = ["www.samsung.com"]
c.execute("UPDATE inbounds SET stream_settings=? WHERE id=2", (json.dumps(ss2),))

conn.commit()

subprocess.run(["systemctl", "restart", "x-ui"])
time.sleep(3)

with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)

for ib in cfg.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        rs = ib.get('streamSettings', {}).get('realitySettings', {})
        print(f"Port {ib['port']}: target={rs.get('target')}, serverNames={rs.get('serverNames')}, clients={len(ib.get('settings', {}).get('clients', []))}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
