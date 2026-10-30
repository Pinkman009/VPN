import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
for row in c.execute("SELECT id, port, stream_settings FROM inbounds").fetchall():
    print(f"=== INBOUND id={row[0]} port={row[1]} ===")
    st = json.loads(row[2])
    print(json.dumps(st.get("realitySettings", {}), indent=2))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
