import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

cmd = """python3 - << 'EOF'
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
c.execute("SELECT id, port, protocol, settings FROM inbounds")
for row in c.fetchall():
    print(f"--- Inbound ID: {row[0]}, Port: {row[1]}, Protocol: {row[2]} ---")
    s = json.loads(row[3])
    for cl in s.get('clients', []):
        print("  Client:", cl.get('email'), "UUID:", cl.get('id'), "limitIp:", cl.get('limitIp'), "expiryTime:", cl.get('expiryTime'), "enable:", cl.get('enable'))
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])
conn.close()
EOF
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())
ssh.close()
