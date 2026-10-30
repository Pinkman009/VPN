import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

cmd = """python3 -c "
import sqlite3, json
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
for t in ['client_traffics', 'inbounds', 'clients']:
    try:
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t})').fetchall()]
        print(t, cols)
    except Exception as e:
        print(t, e)

print('--- CLIENT_TRAFFICS ---')
for r in conn.execute('SELECT * FROM client_traffics').fetchall():
    print(r)

print('--- INBOUND 1 & 2 CLIENTS ---')
for r in conn.execute('SELECT id, remark, port, settings, stream_settings FROM inbounds').fetchall():
    s = json.loads(r[3])
    print(f'Inbound {r[0]} ({r[1]}):')
    for c in s.get('clients', []):
        print('  Client:', c.get('id'), c.get('email'), 'subId:', c.get('subId'))
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
