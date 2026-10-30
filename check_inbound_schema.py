import sys
from run_remote import run_script_on_vps

script = """
import sqlite3
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
print("INBOUNDS TABLE INFO:")
for col in c.execute("PRAGMA table_info(inbounds)").fetchall():
    print(col)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
