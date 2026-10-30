import subprocess
import threading
import time
import paramiko

def monitor():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
    cmd = 'timeout 10 tcpdump -nn -i any "host 176.212.204.65" -c 30'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print('VPS TCPDUMP:')
    print(out if out else 'NONE')
    client.close()

t = threading.Thread(target=monitor)
t.start()
time.sleep(2)

print('Sending probe from phone to VPS port 443...')
p = subprocess.run([r'.\platform-tools\adb.exe', '-s', '19ac4fde', 'shell', 'nc -z -w 3 193.233.138.42 443; echo EXIT: $?'], capture_output=True, text=True)
print("Phone probe output:", p.stdout)

t.join()
