import subprocess
import json
import time
import urllib.request

with open('debug_config.json') as f:
    cfg = json.load(f)

cfg['outbounds'][0]['streamSettings']['realitySettings']['serverName'] = 'swdist.apple.com'
cfg['outbounds'][0]['streamSettings']['realitySettings']['shortId'] = 'dae45f'
cfg['outbounds'][0]['streamSettings']['realitySettings']['spiderX'] = '/ec2973b76d0d4ce'
cfg['outbounds'][0]['streamSettings']['realitySettings']['fingerprint'] = 'chrome'
cfg['outbounds'][0]['streamSettings']['network'] = 'tcp'
cfg['outbounds'][0]['settings']['vnext'][0]['port'] = 443

with open('test_xray_cfg.json', 'w') as f:
    json.dump(cfg, f, indent=2)

xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
p = subprocess.Popen([xray_bin, 'run', '-c', 'test_xray_cfg.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(2)

print('Xray running PID:', p.pid)
proxy_handler = urllib.request.ProxyHandler({'http': 'socks5h://127.0.0.1:10818', 'https': 'socks5h://127.0.0.1:10818'})
opener = urllib.request.build_opener(proxy_handler)

for test_url in ['https://api.ipify.org', 'https://www.youtube.com', 'https://www.google.com']:
    try:
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=8) as r:
            print(f'SUCCESS {test_url}! Status: {r.status}')
    except Exception as e:
        print(f'FAILED {test_url}! Error: {e}')

p.terminate()
out, err = p.communicate()
print('\nXRAY LOG (last 1500 chars):\n', out.decode('utf-8', errors='replace')[-1500:])
print('\nXRAY ERR (last 1500 chars):\n', err.decode('utf-8', errors='replace')[-1500:])
