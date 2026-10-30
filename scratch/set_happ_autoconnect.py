import paramiko
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', 22, 'root', 'xXM3yS7biwUj', timeout=10)

cmd = """python3 -c "
import sqlite3
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
conn.execute(\"UPDATE settings SET value='true' WHERE key='subHappAutoConnect'\")
conn.commit()
print('Updated subHappAutoConnect to true')
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.exec_command('systemctl restart x-ui')
ssh.close()
