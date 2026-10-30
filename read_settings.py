import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

remote_script_content = """import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("=== SETTINGS TABLE ===")
rows = c.execute("SELECT key, value FROM settings").fetchall()
for r in rows:
    print(f"{r[0]}: {r[1]}")
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

sftp = client.open_sftp()
with sftp.file('/tmp/read_settings.py', 'w') as f:
    f.write(remote_script_content)
sftp.close()

stdin, stdout, stderr = client.exec_command('python3 /tmp/read_settings.py')
print(stdout.read().decode('utf-8', errors='replace'))
client.close()
