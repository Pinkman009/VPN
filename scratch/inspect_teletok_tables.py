import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_db.py', 'w') as f:
    f.write('''
import sqlite3

conn = sqlite3.connect('/etc/teletok/teletok.db')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)
for t in tables:
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
    print(t, cols)

try:
    for r in conn.execute("SELECT * FROM accounts").fetchall():
        print("Account:", r)
except Exception as e:
    print(e)
''')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/inspect_db.py')
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
