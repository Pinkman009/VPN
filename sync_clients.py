import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess, time

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

in1 = c.execute("SELECT settings FROM inbounds WHERE id=1").fetchone()[0]
c.execute("UPDATE inbounds SET settings=? WHERE port=2053", (in1,))
conn.commit()

subprocess.run(["systemctl", "restart", "x-ui"])
time.sleep(2)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
