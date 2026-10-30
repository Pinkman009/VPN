import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

tmpl_str = c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'").fetchone()[0]
tmpl = json.loads(tmpl_str)

tmpl["log"] = {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "debug"
}

c.execute("UPDATE settings SET value=? WHERE key='xrayTemplateConfig'", (json.dumps(tmpl, indent=2),))
conn.commit()
conn.close()

subprocess.run("mkdir -p /var/log/xray", shell=True)
subprocess.run("touch /var/log/xray/access.log /var/log/xray/error.log", shell=True)
subprocess.run("chmod -R 777 /var/log/xray", shell=True)
subprocess.run("x-ui restart", shell=True)
print("Enabled debug access & error log in Xray!")
'''

run_script_on_vps(script)
