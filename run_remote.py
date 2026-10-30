import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_script_on_vps(script_code):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
    
    sftp = client.open_sftp()
    with sftp.file('/tmp/task_script.py', 'w') as f:
        f.write(script_code)
    sftp.close()
    
    stdin, stdout, stderr = client.exec_command('python3 /tmp/task_script.py')
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("STDERR:", err)
    client.close()

if __name__ == '__main__':
    remote_code = """import sqlite3
import json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

print("ALL SETTINGS:")
for k, v in c.execute("SELECT key, value FROM settings").fetchall():
    print(f"  {k}: {v}")

print("\\nALL INBOUNDS:")
for row in c.execute("SELECT id, port, protocol, remark, enable, settings, stream_settings, tag FROM inbounds").fetchall():
    print(f"ID={row[0]} Port={row[1]} Proto={row[2]} Remark={row[3]} Enable={row[4]} Tag={row[7]}")
"""
    run_script_on_vps(remote_code)
