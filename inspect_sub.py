import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj')

cmd = """python3 -c "
import sqlite3
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
for row in c.execute('SELECT key, value FROM settings WHERE key LIKE \\"%sub%\\"'):
    print(row)
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
ssh.close()
