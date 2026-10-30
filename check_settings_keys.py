import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
print("=== CLIENTS TABLE ===")
for r in c.execute("SELECT * FROM clients").fetchall():
    print(r)
print("=== CLIENT_INBOUNDS ===")
for r in c.execute("SELECT * FROM client_inbounds").fetchall():
    print(r)


"""

if __name__ == '__main__':
    run_script_on_vps(script)
