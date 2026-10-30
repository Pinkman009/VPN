import paramiko, subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

def get_recent_xray_logs():
    stdin, stdout, stderr = client.exec_command('tail -15 /var/log/x-ui/error.log')
    return stdout.read().decode('utf-8').strip()

print("1. Running XRAY client test (the working one)...")
p_xray = subprocess.Popen([r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe', 'run', '-c', 'test_desktop_vless.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(1.5)
subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-x', 'http://127.0.0.1:10898', '--max-time', '3', 'https://api.ipify.org'])
p_xray.kill()
time.sleep(1)

print("\nVPS logs after Xray client:")
print(get_recent_xray_logs())

print("\n" + "="*60 + "\n")

print("2. Running SING-BOX client test (the failing one)...")
p_sb = subprocess.Popen([r'v2rayN\v2rayN-windows-64\bin\sing_box\sing-box.exe', 'run', '-c', 'test_debug_singbox.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(1.5)
subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-x', 'http://127.0.0.1:20880', '--max-time', '3', 'https://api.ipify.org'])
p_sb.kill()
time.sleep(1)

print("\nVPS logs after Sing-box client:")
print(get_recent_xray_logs())

client.close()
