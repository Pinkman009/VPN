import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Set subURI and subDomain to public IP 193.233.138.42
settings_to_set = {
    "subDomain": "193.233.138.42",
    "subURI": "https://193.233.138.42:2096",
    "subJsonUserAgentRegex": "",
    "subJsonEnable": "false"
}

for k, v in settings_to_set.items():
    c.execute("UPDATE settings SET value=? WHERE key=?", (v, k))
    print(f"Updated {k} -> {v}")

conn.commit()
conn.close()

import subprocess
subprocess.run(["systemctl", "restart", "x-ui"])
print("x-ui restarted")

p = subprocess.run(["curl", "-k", "-s", "-i", "-H", "Host: 193.233.138.42:2096", "-H", "User-Agent: Hiddify/4.1.1", "https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m"], capture_output=True, text=True)
print("SUBSCRIPTION RESPONSE:")
print(p.stdout[:300])


print("\\nUpdated settings:")
for r in c.execute("SELECT key, value FROM settings WHERE key LIKE 'sub%'").fetchall():
    print(f"  {r[0]}: {r[1]}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
