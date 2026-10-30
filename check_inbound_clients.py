import sys
from run_remote import run_script_on_vps

script = """
import sqlite3
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
print("CLIENT_TRAFFICS:")
for r in c.execute("SELECT * FROM client_traffics").fetchall():
    print(r)
print("INBOUNDS:")
for r in c.execute("SELECT id, port, protocol, settings FROM inbounds").fetchall():
    print(r[0], r[1], r[2], r[3])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
