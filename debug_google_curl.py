import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
p = subprocess.Popen([xray_bin, 'run', '-c', 'test_exact_node1.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
time.sleep(1.5)

print("Running curl to https://www.google.com with verbose output:")
res = subprocess.run(['curl.exe', '-x', 'socks5h://127.0.0.1:10899', '-v', '--max-time', '10', 'https://www.google.com'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print("CURL STDOUT:", res.stdout[:500])
print("CURL STDERR:", res.stderr)

p.terminate()
out, err = p.communicate()
print("\nXRAY LOGS:")
print(out[-2000:])
print(err[-2000:])
