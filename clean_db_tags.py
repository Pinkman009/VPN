import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Update tags
c.execute("UPDATE inbounds SET tag='in-443-tcp' WHERE id=1")
c.execute("UPDATE inbounds SET tag='in-2053-tcp' WHERE id=2")

# Check if there are any other disabled inbounds and delete them if any
c.execute("DELETE FROM inbounds WHERE enable=0")

conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True)
print("Updated tags and cleaned up database!")
'''

run_script_on_vps(script)
