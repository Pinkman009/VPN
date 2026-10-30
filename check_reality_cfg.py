import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

stdin, stdout, stderr = client.exec_command('grep -A 25 "realitySettings" /usr/local/x-ui/bin/config.json')
print(stdout.read().decode('utf-8'))
client.close()
