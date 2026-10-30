import subprocess
import json
import time
import urllib.request

with open('debug_config.json') as f:
    cfg = json.load(f)

# Test with the EXACT settings from the subscription link
cfg['outbounds'][0]['streamSettings']['realitySettings']['serverName'] = 'swdist.apple.com'
cfg['outbounds'][0]['streamSettings']['realitySettings']['shortId'] = '436401f4'
cfg['outbounds'][0]['streamSettings']['realitySettings']['spiderX'] = '/5d73cb33b10672d'
cfg['outbounds'][0]['streamSettings']['realitySettings']['fingerprint'] = 'chrome'
cfg['outbounds'][0]['streamSettings']['network'] = 'tcp'
cfg['outbounds'][0]['settings']['vnext'][0]['port'] = 443

with open('test_xray_exact_sub.json', 'w') as f:
    json.dump(cfg, f, indent=2)

xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
p = subprocess.Popen([xray_bin, 'run', '-c', 'test_xray_exact_sub.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(2)

proxy_handler = urllib.request.ProxyHandler({'http': 'socks5h://127.0.0.1:10818', 'https': 'socks5h://127.0.0.1:10818'})
opener = urllib.request.build_opener(proxy_handler)

try:
    req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'Mozilla/5.0'})
    with opener.open(req, timeout=5) as r:
        print(f'STATUS: {r.status}, IP: {r.read().decode()}')
except Exception as e:
    print(f'TEST FAILED: {e}')

p.terminate()
out, err = p.communicate()
print('XRAY LOG:\n', out.decode('utf-8', errors='replace')[-1000:])
