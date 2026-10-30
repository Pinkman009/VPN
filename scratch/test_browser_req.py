import subprocess
import time
import sys
import threading

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

XRAY_BIN = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
CONFIG = 'vpn_client_runtime.json'

# Update config loglevel to debug temporarily
import json
with open(CONFIG, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg['log']['loglevel'] = 'debug'
with open('scratch/debug_runtime.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2)

p = subprocess.Popen([XRAY_BIN, 'run', '-c', 'scratch/debug_runtime.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

def reader():
    for line in iter(p.stdout.readline, ''):
        print(line, end='', flush=True)

t = threading.Thread(target=reader, daemon=True)
t.start()

time.sleep(2)
print("--- SENDING CURL REQUEST THROUGH 127.0.0.1:10897 ---")
res = subprocess.run(['curl.exe', '-v', '--proxy', 'http://127.0.0.1:10897', '--max-time', '6', 'https://www.instagram.com'], capture_output=True, text=True, errors='replace')
print("CURL STDERR (first 500 chars):", res.stderr[:500])
time.sleep(2)
p.terminate()
