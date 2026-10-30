import sys
import json
from run_remote import run_script_on_vps

script = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
row = c.execute("SELECT id, port, protocol, settings, stream_settings, remark FROM inbounds WHERE id=1").fetchone()
print("ID:", row[0])
print("PORT:", row[1])
print("PROTO:", row[2])
print("SETTINGS:", json.dumps(json.loads(row[3]), indent=2))
print("STREAM_SETTINGS:", json.dumps(json.loads(row[4]), indent=2))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
