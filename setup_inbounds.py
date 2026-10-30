import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess, time

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# Get existing inbound 1
row = c.execute("SELECT settings, stream_settings FROM inbounds WHERE id=1").fetchone()
settings = json.loads(row[0])
stream_settings_443 = json.loads(row[1])

# Configure Inbound 1 for port 443 with dl.google.com
stream_settings_443["realitySettings"]["target"] = "dl.google.com:443"
stream_settings_443["realitySettings"]["serverNames"] = ["dl.google.com"]

c.execute(\"\"\"
UPDATE inbounds 
SET port=443, 
    remark='VLESS-Reality-443', 
    tag='in-443-tcp', 
    stream_settings=? 
WHERE id=1
\"\"\", (json.dumps(stream_settings_443),))

# Check if inbound 2 exists, if not create backup inbound on 2053
existing_2 = c.execute("SELECT count(*) FROM inbounds WHERE port=2053").fetchone()[0]
if not existing_2:
    stream_settings_2053 = json.loads(row[1])
    stream_settings_2053["realitySettings"]["target"] = "gateway.icloud.com:443"
    stream_settings_2053["realitySettings"]["serverNames"] = ["gateway.icloud.com"]
    c.execute(\"\"\"
    INSERT INTO inbounds (user_id, up, down, total, remark, sub_sort_index, enable, expiry_time, traffic_reset, traffic_reset_day, last_traffic_reset_time, listen, port, protocol, settings, stream_settings, tag, sniffing, share_addr_strategy, disable_flow)
    VALUES (0, 0, 0, 0, 'VLESS-Reality-2053', 2, 1, 0, 'never', 1, 0, '', 2053, 'vless', ?, ?, 'in-2053-tcp', '', 'node', 0)
    \"\"\", (json.dumps(settings), json.dumps(stream_settings_2053)))

conn.commit()

# Restart x-ui
subprocess.run(["systemctl", "restart", "x-ui"])
time.sleep(3)

# Check ports
p = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "443" in line or "2053" in line:
        print(line)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
