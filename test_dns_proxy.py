import subprocess
import json
import time
import socket

# Test UDP DNS query through socks5 proxy 127.0.0.1:10818
# When xray.exe is running

xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
p = subprocess.Popen([xray_bin, 'run', '-c', 'test_xray_cfg.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(2)

print('Xray running PID:', p.pid)

# Test 1: HTTP GET through SOCKS5 (TCP)
import urllib.request
proxy_handler = urllib.request.ProxyHandler({'http': 'socks5h://127.0.0.1:10818', 'https': 'socks5h://127.0.0.1:10818'})
opener = urllib.request.build_opener(proxy_handler)

try:
    with opener.open('https://api.ipify.org', timeout=5) as r:
        print("TCP HTTPS test IP:", r.read().decode())
except Exception as e:
    print("TCP HTTPS test FAILED:", e)

# Test 2: Test DNS resolution through socks5
for domain in ['www.google.com', 'www.youtube.com', 'www.instagram.com', 'ya.ru']:
    try:
        with opener.open(f'https://{domain}', timeout=5) as r:
            print(f"Domain {domain} status: {r.status}")
    except Exception as e:
        print(f"Domain {domain} FAILED: {e}")

p.terminate()
p.wait()
