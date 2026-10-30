from run_remote import run_script_on_vps

script = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Check all settings with 'sub' or 'rule'
for k, v in c.execute("SELECT key, value FROM settings WHERE key LIKE 'sub%'").fetchall():
    print(f'{k}: {v[:100] if v else \"\"}')
"""

run_script_on_vps(script)
