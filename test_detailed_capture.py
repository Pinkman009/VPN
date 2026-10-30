import subprocess
import threading
import time
import paramiko

def monitor_vps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
    
    # Detailed tcpdump showing payload
    cmd = 'timeout 8 tcpdump -nn -vv -X -i any "host 176.212.204.65 and (port 443 or port 2053)" -c 30'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    print("=== VPS DETAILED TCPDUMP ===")
    print(out if out else "[No packets]")
    client.close()

t = threading.Thread(target=monitor_vps)
t.start()
time.sleep(1)

# Tap Connect in Hiddify on phone
print("Tapping connect on phone...")
subprocess.run([r'.\platform-tools\adb.exe', '-s', '19ac4fde', 'shell', 'input', 'tap', '500', '1250'])

t.join()
