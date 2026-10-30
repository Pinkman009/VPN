import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("=== ALL SUBSCRIPTION SETTINGS ===")
for k, v in c.execute("SELECT key, value FROM settings WHERE key LIKE '%sub%'").fetchall():
    print(f"  {k}: {v}")
'''

run_script_on_vps(script)
