import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

sftp = client.open_sftp()
sftp.get('/etc/sysctl.d/99-vpn-optimize.conf', 'backup/99-vpn-optimize.conf')
sftp.close()
client.close()
print("Saved backup/99-vpn-optimize.conf")
