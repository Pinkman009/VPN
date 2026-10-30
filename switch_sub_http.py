import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

c.execute("UPDATE settings SET value='' WHERE key='subCertFile'")
c.execute("UPDATE settings SET value='' WHERE key='subKeyFile'")
c.execute("UPDATE settings SET value='http://193.233.138.42:2096' WHERE key='subURI'")
conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True)
print("Updated sub to HTTP (no certificate validation issues on phones)!")
'''

run_script_on_vps(script)
