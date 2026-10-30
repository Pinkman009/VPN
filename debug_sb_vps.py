import paramiko, subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

# Check error log before
stdin, stdout, stderr = client.exec_command('tail -1 /var/log/x-ui/error.log')
print("Last error before:", stdout.read().decode('utf-8').strip())

# Start sing-box
print("Starting sing-box...")
sb = r'v2rayN\v2rayN-windows-64\bin\sing_box\sing-box.exe'
p = subprocess.Popen([sb, 'run', '-c', 'test_sb_trace.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(1)

# Make 1 request
print("Sending request through sing-box...")
subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '--max-time', '3', '-x', 'http://127.0.0.1:20880', 'https://www.google.com'])

p.kill()
time.sleep(1)

# Check logs on VPS
stdin, stdout, stderr = client.exec_command('tail -8 /var/log/x-ui/error.log')
print("\nServer error log:")
print(stdout.read().decode('utf-8').strip())

stdin, stdout, stderr = client.exec_command('tail -8 /var/log/x-ui/access.log')
print("\nServer access log:")
print(stdout.read().decode('utf-8').strip())

client.close()
