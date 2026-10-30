import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

print("=== RECENT ACCESS LOG (last 20 lines) ===")
stdin, stdout, stderr = client.exec_command('tail -20 /var/log/x-ui/access.log')
print(stdout.read().decode('utf-8'))

print("=== RECENT ERROR LOG (last 20 lines) ===")
stdin, stdout, stderr = client.exec_command('tail -20 /var/log/x-ui/error.log')
print(stdout.read().decode('utf-8'))

client.close()
