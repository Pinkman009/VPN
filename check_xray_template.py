import sqlite3, json
from run_remote import run_script_on_vps

script = """
import sqlite3, json
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
row = c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'").fetchone()
if row:
    cfg = json.loads(row[0])
    print('xrayTemplateConfig keys:', list(cfg.keys()))
    print('routing:', json.dumps(cfg.get('routing'), indent=2))
    print('dns:', json.dumps(cfg.get('dns'), indent=2))
    print('outbounds:', json.dumps(cfg.get('outbounds'), indent=2))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
