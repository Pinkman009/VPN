import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("USERS TABLE:")
try:
    for row in c.execute("SELECT id, username, password, login_secret FROM users").fetchall():
        print(f"ID={row[0]}, USERNAME={row[1]}")
except Exception as e:
    print("Error:", e)

print("\\nALL INBOUNDS:")
try:
    for row in c.execute("SELECT id, user_id, port, protocol, remark, enable FROM inbounds").fetchall():
        print(row)
except Exception as e:
    print("Error:", e)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
