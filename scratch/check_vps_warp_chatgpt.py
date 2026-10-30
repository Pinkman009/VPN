import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

cmd = 'curl -v -s -x socks5h://127.0.0.1:40000 https://chatgpt.com --connect-timeout 5 -m 8'
stdin, stdout, stderr = client.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8')[:300])
print("STDERR:", stderr.read().decode('utf-8'))

client.close()
