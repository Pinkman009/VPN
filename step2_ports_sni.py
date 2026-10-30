import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json

conn = sqlite3.connect("/etc/x-ui/x-ui.db")
c = conn.cursor()

# === UPDATE INBOUND 1: Port 8880 -> 443, SNI -> dl.google.com ===
row = c.execute("SELECT id, settings, stream_settings FROM inbounds WHERE id=1").fetchone()
ib_id, settings_str, stream_str = row
stream = json.loads(stream_str)

# Change reality settings
reality = stream["realitySettings"]
reality["target"] = "dl.google.com:443"
reality["serverNames"] = ["dl.google.com"]
if "settings" in reality:
    reality["settings"]["serverName"] = ""

stream["realitySettings"] = reality

# Update in DB
c.execute("UPDATE inbounds SET port=443, remark='VLESS-Reality-443', stream_settings=? WHERE id=1",
          (json.dumps(stream),))
print("Inbound 1: port -> 443, SNI -> dl.google.com, target -> dl.google.com:443")

# === UPDATE INBOUND 2: Port 2087 -> 2053, SNI -> www.samsung.com ===
row = c.execute("SELECT id, settings, stream_settings FROM inbounds WHERE id=2").fetchone()
ib_id, settings_str, stream_str = row
stream = json.loads(stream_str)

reality = stream["realitySettings"]
reality["target"] = "www.samsung.com:443"
reality["serverNames"] = ["www.samsung.com"]
if "settings" in reality:
    reality["settings"]["serverName"] = ""

stream["realitySettings"] = reality

c.execute("UPDATE inbounds SET port=2053, remark='VLESS-Reality-2053', stream_settings=? WHERE id=2",
          (json.dumps(stream),))
print("Inbound 2: port -> 2053, SNI -> www.samsung.com, target -> www.samsung.com:443")

conn.commit()
conn.close()

# Restart xray via x-ui
import subprocess
r = subprocess.run("x-ui restart", shell=True, capture_output=True, text=True, timeout=30)
print("x-ui restart:", r.stdout.strip(), r.stderr.strip())

import time
time.sleep(3)

# Verify
r = subprocess.run("ss -tlnp | grep xray", shell=True, capture_output=True, text=True, timeout=10)
print()
print("=== VERIFICATION: xray listening ports ===")
print(r.stdout.strip())

# Verify DB
conn2 = sqlite3.connect("/etc/x-ui/x-ui.db")
c2 = conn2.cursor()
for row in c2.execute("SELECT id, port, remark, stream_settings FROM inbounds WHERE enable=1").fetchall():
    ib_id, port, remark, stream_str = row
    stream = json.loads(stream_str)
    reality = stream.get("realitySettings", {})
    print(f"  ID={ib_id} Port={port} Remark={remark} target={reality.get('target')} serverNames={reality.get('serverNames')}")
conn2.close()
'''

run_script_on_vps(script)
