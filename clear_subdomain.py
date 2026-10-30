from run_remote import run_script_on_vps

script = """
import sqlite3, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
c.execute("UPDATE settings SET value = '' WHERE key = 'subDomain'")
conn.commit()
conn.close()

subprocess.run(['systemctl', 'restart', 'x-ui'])
print("Updated subDomain to empty and restarted x-ui")
"""

run_script_on_vps(script)
