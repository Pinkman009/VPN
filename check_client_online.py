import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, time, datetime

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("CURRENT TIME (UTC):", datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

for row in c.execute("SELECT id, inbound_id, email, last_online, last_sub_fetch, up, down FROM client_traffics").fetchall():
    cid, iid, email, lo, lsf, up, down = row
    lo_dt = datetime.datetime.utcfromtimestamp(lo/1000).strftime('%Y-%m-%d %H:%M:%S') if lo else "Never"
    lsf_dt = datetime.datetime.utcfromtimestamp(lsf/1000).strftime('%Y-%m-%d %H:%M:%S') if lsf else "Never"
    print(f"Client {email} (Inbound {iid}):")
    print(f"  Last Online:    {lo_dt} (timestamp: {lo})")
    print(f"  Last Sub Fetch: {lsf_dt} (timestamp: {lsf})")
    print(f"  Traffic Up/Down: {up} / {down}")
'''

run_script_on_vps(script)
