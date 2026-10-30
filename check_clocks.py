import datetime
import paramiko

local_time = datetime.datetime.now(datetime.timezone.utc)
print('Local Windows UTC time:', local_time.isoformat())

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

stdin, stdout, stderr = client.exec_command('date -u +"%Y-%m-%dT%H:%M:%S%z"')
server_str = stdout.read().decode('utf-8').strip()
print('VPS Server UTC time:   ', server_str)

client.close()
