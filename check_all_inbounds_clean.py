import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("=== ALL INBOUNDS IN DB ===")
for row in c.execute("SELECT id, port, protocol, remark, enable, tag FROM inbounds").fetchall():
    print(f"ID={row[0]} Port={row[1]} Proto={row[2]} Remark={row[3]} Enable={row[4]} Tag={row[5]}")

print("\n=== INBOUNDS STREAM SETTINGS ===")
for row in c.execute("SELECT id, port, stream_settings FROM inbounds").fetchall():
    s = json.loads(row[2])
    r = s.get("realitySettings", {})
    print(f"ID={row[0]} Port={row[1]} Target={r.get('target')} SNI={r.get('serverNames')}")
'''

run_script_on_vps(script)
