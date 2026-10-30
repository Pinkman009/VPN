from run_remote import run_script_on_vps

script = """
import sqlite3
import subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
c.execute("UPDATE settings SET value='193.233.138.42' WHERE key='subDomain'")
c.execute("UPDATE settings SET value='https://193.233.138.42:2096' WHERE key='subURI'")
c.execute("UPDATE settings SET value='/root/cert/ip/fullchain.pem' WHERE key='subCertFile'")
c.execute("UPDATE settings SET value='/root/cert/ip/privkey.pem' WHERE key='subKeyFile'")
conn.commit()
conn.close()

subprocess.run(['systemctl', 'restart', 'x-ui'], check=True)
print('x-ui restarted with HTTPS and subDomain=193.233.138.42')
"""

if __name__ == '__main__':
    run_script_on_vps(script)
