import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

c.execute("UPDATE settings SET value='true' WHERE key='subEnableRouting'")
if c.rowcount == 0:
    c.execute("INSERT INTO settings (key, value) VALUES ('subEnableRouting', 'true')")

conn.commit()

print("subEnableRouting is now:", c.execute("SELECT value FROM settings WHERE key='subEnableRouting'").fetchone()[0])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
