from run_remote import run_script_on_vps

script = """
import sqlite3, subprocess

# 1. Update UFW to allow port 80
subprocess.run("ufw allow 80/tcp", shell=True)

# 2. Update 3X-UI settings to port 80 HTTP
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

c.execute("UPDATE settings SET value='80' WHERE key='subPort'")
c.execute("UPDATE settings SET value='' WHERE key='subCertFile'")
c.execute("UPDATE settings SET value='' WHERE key='subKeyFile'")
c.execute("UPDATE settings SET value='http://193.233.138.42:80' WHERE key='subURI'")

conn.commit()
conn.close()

# 3. Restart x-ui
subprocess.run("x-ui restart", shell=True)

print("Switched Subscriptions to Port 80 HTTP (Standard Web Port, Unblockable, Zero SSL issues)!")
"""

run_script_on_vps(script)
