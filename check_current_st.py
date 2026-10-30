import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
st = json.loads(c.execute("SELECT stream_settings FROM inbounds WHERE id=2").fetchone()[0])
print("StreamSettings:")
print(json.dumps(st, indent=2))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
