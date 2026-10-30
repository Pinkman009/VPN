import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

c.execute("UPDATE settings SET value='/root/cert/ip/fullchain.pem' WHERE key='subCertFile'")
c.execute("UPDATE settings SET value='/root/cert/ip/privkey.pem' WHERE key='subKeyFile'")
c.execute("UPDATE settings SET value='https://193.233.138.42:2096' WHERE key='subURI'")
c.execute("UPDATE settings SET value='193.233.138.42' WHERE key='subDomain'")

conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True)
print("Configured HTTPS with official Let's Encrypt certificate on port 2096!")
'''

run_script_on_vps(script)
