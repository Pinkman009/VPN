import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

cmd = """python3 -c "
import sqlite3
conn = sqlite3.connect('/etc/teletok/teletok.db')
for t in ['users', 'devices']:
    cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t})').fetchall()]
    print(t, cols)
for r in conn.execute('SELECT * FROM users LIMIT 3').fetchall():
    print('User:', r)
for r in conn.execute('SELECT * FROM devices LIMIT 5').fetchall():
    print('Device:', r)
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
