import paramiko, json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

s = """
import sqlite3, json
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
for r in c.execute('SELECT id, port, stream_settings FROM inbounds').fetchall():
    print(f'=== Port {r[1]} ===')
    st = json.loads(r[2])
    rs = st.get('realitySettings', {})
    print('  dest:', rs.get('dest'))
    print('  target:', rs.get('target'))
    print('  serverNames:', rs.get('serverNames'))
    print('  shortIds:', rs.get('shortIds'))
    print('  settings:', rs.get('settings'))
"""
stdin, stdout, stderr = client.exec_command(f'python3 -c "{s}"')
print(stdout.read().decode('utf-8'))
client.close()
