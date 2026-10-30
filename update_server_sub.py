from run_remote import run_script_on_vps

script = """
import sqlite3
import subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
c.execute("UPDATE settings SET value='193.233.138.42' WHERE key='subDomain'")
c.execute("UPDATE settings SET value='true' WHERE key='subJsonEnable'")
c.execute("UPDATE settings SET value='true' WHERE key='subClashEnable'")
c.execute("UPDATE settings SET value='' WHERE key='subCertFile'")
c.execute("UPDATE settings SET value='' WHERE key='subKeyFile'")
c.execute("UPDATE settings SET value='http://193.233.138.42:2096' WHERE key='subURI'")
conn.commit()
conn.close()

subprocess.run(['systemctl', 'restart', 'x-ui'], check=True)
print('x-ui restarted successfully')
"""

if __name__ == '__main__':
    run_script_on_vps(script)
