import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

py_code = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
for row in c.execute('SELECT id, remark, port, protocol, stream_settings FROM inbounds').fetchall():
    print('ID:', row[0], 'Remark:', row[1], 'Port:', row[2], 'Protocol:', row[3])
    stream = json.loads(row[4])
    reality = stream.get('realitySettings', {})
    print('  SNI:', reality.get('serverNames'), 'shortIds:', reality.get('shortIds'))
"""

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{py_code}"')
print("=== INBOUNDS ===")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
ssh.close()
