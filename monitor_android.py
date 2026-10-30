"""
Monitor server logs in real-time during Android connection attempt.
Clears old logs, then watches for 60 seconds.
"""
import paramiko, sys, time, select
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

# Step 1: Get current line count so we only show new entries
print("=== Clearing baseline... ===")
stdin, stdout, stderr = client.exec_command('wc -l /var/log/x-ui/error.log /var/log/x-ui/access.log')
baseline = stdout.read().decode('utf-8', errors='replace').strip()
print(baseline)

# Step 2: Tail both logs for new entries
print("\n=== WAITING FOR ANDROID CONNECTION (next 45 seconds)... ===")
print(">>> Please try connecting from Happ on Android NOW <<<\n")

# Use tail -f with timeout
transport = client.get_transport()
channel = transport.open_session()
channel.exec_command('timeout 45 tail -f /var/log/x-ui/error.log /var/log/x-ui/access.log 2>/dev/null')

start = time.time()
buffer = ""
while time.time() - start < 50:
    if channel.recv_ready():
        data = channel.recv(4096).decode('utf-8', errors='replace')
        buffer += data
        # Print new lines as they come
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            # Filter out API noise
            if 'api' not in line.lower() and 'dokodemo' not in line.lower() and line.strip():
                print(line)
    elif channel.exit_status_ready():
        break
    else:
        time.sleep(0.5)

# Get any remaining data
while channel.recv_ready():
    data = channel.recv(4096).decode('utf-8', errors='replace')
    for line in data.split('\n'):
        if 'api' not in line.lower() and 'dokodemo' not in line.lower() and line.strip():
            print(line)

channel.close()
client.close()
print("\n=== MONITORING ENDED ===")
