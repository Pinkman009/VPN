import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

stdin, stdout, stderr = client.exec_command('/usr/local/x-ui/bin/xray-linux-amd64 x25519 -i "yPkaUKcc-bi4DCT5QgxjLzDTtcaDPEPu2_f_qE35E2s"')
print("Xray x25519 output:")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

client.close()
