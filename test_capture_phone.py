import subprocess
import threading
import time
import paramiko

def monitor_vps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
    
    # Run tcpdump on port 443 and 2053 for 8 seconds
    cmd = 'timeout 6 tcpdump -nn -i any "port 443 or port 2053" -c 50'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("=== VPS TCPDUMP OUTPUT ===")
    print(out if out else "[No packets captured on port 443 / 2053]")
    if err:
        print("[STDERR]:", err)
    client.close()

t = threading.Thread(target=monitor_vps)
t.start()
time.sleep(1)

# Tap the lightning button on phone at (890, 1960)
print("Tapping lightning bolt at (890, 1960)...")
subprocess.run([r'.\platform-tools\adb.exe', '-s', '19ac4fde', 'shell', 'input', 'tap', '890', '1960'])

t.join()
