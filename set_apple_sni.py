import sqlite3, json, subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json, subprocess

conn = sqlite3.connect("/etc/x-ui/x-ui.db")
c = conn.cursor()

row = c.execute("SELECT id, stream_settings FROM inbounds WHERE id=1").fetchone()
ib_id, stream_str = row
stream = json.loads(stream_str)

reality = stream["realitySettings"]
reality["target"] = "swdist.apple.com:443"
reality["serverNames"] = ["swdist.apple.com"]
if "settings" in reality:
    reality["settings"]["serverName"] = ""

stream["realitySettings"] = reality

c.execute("UPDATE inbounds SET stream_settings=? WHERE id=1", (json.dumps(stream),))
conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True, capture_output=True, text=True)
print("Updated Inbound 1 to swdist.apple.com")
'''

run_script_on_vps(script)
