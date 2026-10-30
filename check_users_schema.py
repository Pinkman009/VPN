import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("USERS SCHEMA:")
for col in c.execute("PRAGMA table_info(users)").fetchall():
    print(col)

print("\\nUSERS ROWS:")
for row in c.execute("SELECT * FROM users").fetchall():
    print(row)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
