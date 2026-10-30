import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Check Inbound 1 settings
s_str, st_str = c.execute("SELECT settings, stream_settings FROM inbounds WHERE id=1").fetchone()
s = json.loads(s_str)
st = json.loads(st_str)

if "testseed" in s:
    del s["testseed"]

# Clean spiderX in realitySettings
if "spiderX" in st.get("realitySettings", {}).get("settings", {}):
    st["realitySettings"]["settings"]["spiderX"] = ""

c.execute("UPDATE inbounds SET settings=?, stream_settings=? WHERE id=1", (json.dumps(s), json.dumps(st)))
conn.commit()

subprocess.run(["systemctl", "restart", "x-ui"])
print("Cleaned Inbound 1 successfully!")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
