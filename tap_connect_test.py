import subprocess
import threading
import time
import paramiko

def monitor():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
    cmd = 'timeout 6 tcpdump -nn -i any "host 176.212.204.65 and (port 443 or port 2053)" -c 30'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print('VPS TCPDUMP:')
    print(out if out else 'NONE')
    client.close()

t = threading.Thread(target=monitor)
t.start()
time.sleep(1)

adb = r'.\platform-tools\adb.exe'
print('Tapping connect button at 540, 1265...')
subprocess.run([adb, '-s', '19ac4fde', 'shell', 'input', 'tap', '540', '1265'])

t.join()
time.sleep(3)
subprocess.run([adb, '-s', '19ac4fde', 'exec-out', 'screencap', '-p'], stdout=open('phone_screen.png', 'wb'))
print('Captured screenshot')
