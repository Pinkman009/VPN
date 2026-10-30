import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Set user_id = 1 for all inbounds so they belong to igorsvincov@yandex.ru
c.execute("UPDATE inbounds SET user_id=1 WHERE user_id=0")
conn.commit()

print("ALL INBOUNDS NOW:")
for row in c.execute("SELECT id, user_id, port, protocol, remark, enable FROM inbounds").fetchall():
    print(row)

# Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
