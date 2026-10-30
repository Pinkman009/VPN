import subprocess
import json
import time
import urllib.request

with open('debug_config.json') as f:
    cfg = json.load(f)

def run_test(sid, spx):
    cfg['outbounds'][0]['streamSettings']['realitySettings']['serverName'] = 'swdist.apple.com'
    cfg['outbounds'][0]['streamSettings']['realitySettings']['shortId'] = sid
    cfg['outbounds'][0]['streamSettings']['realitySettings']['spiderX'] = spx
    cfg['outbounds'][0]['streamSettings']['realitySettings']['fingerprint'] = 'chrome'
    cfg['outbounds'][0]['streamSettings']['network'] = 'tcp'
    cfg['outbounds'][0]['settings']['vnext'][0]['port'] = 443

    with open('test_temp.json', 'w') as f:
        json.dump(cfg, f, indent=2)

    xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
    p = subprocess.Popen([xray_bin, 'run', '-c', 'test_temp.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    proxy_handler = urllib.request.ProxyHandler({'http': 'socks5h://127.0.0.1:10818', 'https': 'socks5h://127.0.0.1:10818'})
    opener = urllib.request.build_opener(proxy_handler)

    res = False
    try:
        req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=4) as r:
            res = True
            print(f"SUCCESS with sid={sid}, spx={spx}! IP: {r.read().decode()}")
    except Exception as e:
        print(f"FAILED with sid={sid}, spx={spx}! Error: {e}")

    p.terminate()
    p.wait()
    return res

print("--- Test 1: sid='dae45f', spx='/ec2973b76d0d4ce' ---")
run_test('dae45f', '/ec2973b76d0d4ce')

print("\n--- Test 2: sid='dae45f', spx='/5d73cb33b10672d' ---")
run_test('dae45f', '/5d73cb33b10672d')

print("\n--- Test 3: sid='436401f4', spx='/ec2973b76d0d4ce' ---")
run_test('436401f4', '/ec2973b76d0d4ce')

print("\n--- Test 4: sid='436401f4', spx='' ---")
run_test('436401f4', '')
