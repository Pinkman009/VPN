import sys
from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("INBOUND 1 SETTINGS:")
print(c.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()[0])

print("INBOUND 2 SETTINGS:")
print(c.execute("SELECT settings FROM inbounds WHERE id=2").fetchone()[0])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
