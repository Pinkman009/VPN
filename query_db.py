import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=5)
stdin, stdout, stderr = ssh.exec_command('find /etc /usr/local -name "*x-ui*.db"')
print("DB path:", stdout.read().decode())
stdin, stdout, stderr = ssh.exec_command('cat /usr/local/x-ui/bin/config.json')
print("Active config.json:\n", stdout.read().decode())
ssh.close()

