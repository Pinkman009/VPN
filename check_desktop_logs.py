import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

commands = [
    ('RECENT ACCESS LOG', 'tail -30 /var/log/x-ui/access.log'),
    ('RECENT ERROR LOG', 'tail -30 /var/log/x-ui/error.log'),
]

for title, cmd in commands:
    print(f'=== {title} ===')
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    print()

client.close()
