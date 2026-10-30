import paramiko
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

cmd = """python3 -c "
import sqlite3, json
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
for r in conn.execute('SELECT id, remark, port, stream_settings FROM inbounds').fetchall():
    print('=== Inbound', r[0], r[1], 'port', r[2], '===')
    ss = json.loads(r[3])
    rs = ss.get('realitySettings', {})
    print(json.dumps(rs, indent=2))
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
