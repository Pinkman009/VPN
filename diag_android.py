import paramiko, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

# Get the full xray config - raw JSON
print('=== FULL XRAY CONFIG (inbound 443 streamSettings) ===')
stdin, stdout, stderr = client.exec_command('cat /usr/local/x-ui/bin/config.json')
config = json.loads(stdout.read().decode('utf-8', errors='replace'))

for ib in config.get('inbounds', []):
    if ib.get('port') in [443, 2053]:
        print(f'\n--- Port {ib["port"]} ---')
        ss = ib.get('streamSettings', {})
        print(json.dumps(ss, indent=2))

# Also get 3x-ui database version of the config (may differ)
print('\n\n=== 3X-UI DB stream_settings for port 443 ===')
stdin, stdout, stderr = client.exec_command("python3 -c \"\nimport sqlite3, json\nconn = sqlite3.connect('/etc/x-ui/x-ui.db')\nc = conn.cursor()\nfor row in c.execute('SELECT stream_settings FROM inbounds WHERE port=443'):\n    d = json.loads(row[0])\n    print(json.dumps(d, indent=2))\n\"")
print(stdout.read().decode('utf-8', errors='replace').strip())

print('\n\n=== 3X-UI DB stream_settings for port 2053 ===')
stdin, stdout, stderr = client.exec_command("python3 -c \"\nimport sqlite3, json\nconn = sqlite3.connect('/etc/x-ui/x-ui.db')\nc = conn.cursor()\nfor row in c.execute('SELECT stream_settings FROM inbounds WHERE port=2053'):\n    d = json.loads(row[0])\n    print(json.dumps(d, indent=2))\n\"")
print(stdout.read().decode('utf-8', errors='replace').strip())

# Get Happ version info
print('\n\n=== CHECK LATEST ERRORS BY TIME ===')
stdin, stdout, stderr = client.exec_command('tail -5 /var/log/x-ui/error.log')
print(stdout.read().decode('utf-8', errors='replace').strip())

client.close()
print('\n=== DONE ===')
