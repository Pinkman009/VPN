import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Update Inbound 1 spiderX to match the user's phone exactly: /ec2973b76d0d4ce
st = json.loads(c.execute("SELECT stream_settings FROM inbounds WHERE id=1").fetchone()[0])
st["realitySettings"]["settings"]["spiderX"] = "/ec2973b76d0d4ce"

c.execute("UPDATE inbounds SET stream_settings=? WHERE id=1", (json.dumps(st),))
conn.commit()

# Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])
print("Server spiderX updated to /ec2973b76d0d4ce successfully!")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
