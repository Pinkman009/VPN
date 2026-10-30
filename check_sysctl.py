import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

stdin, stdout, stderr = client.exec_command('grep -E "bbr|fq|fastopen|rmem|wmem|mtu" /etc/sysctl.conf /etc/sysctl.d/* 2>/dev/null')
print(stdout.read().decode('utf-8', errors='replace').strip())

client.close()
