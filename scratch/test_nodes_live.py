import subprocess
import time
import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')
XRAY = r"C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

test_cases = [
    ("Node 1 (443, speed.cloudflare.com, fp=chrome)", 443, "speed.cloudflare.com", "chrome"),
    ("Node 1 (443, speed.cloudflare.com, fp=firefox)", 443, "speed.cloudflare.com", "firefox"),
    ("Node 2 (2053, azure.microsoft.com, fp=chrome)", 2053, "azure.microsoft.com", "chrome"),
    ("Node 2 (2053, azure.microsoft.com, fp=safari)", 2053, "azure.microsoft.com", "safari"),
]

port = 17500
for name, vps_port, sni, fp in test_cases:
    port += 1
    cfg = {
        "log": {"loglevel": "none"},
        "inbounds": [{"listen": "127.0.0.1", "port": port, "protocol": "http"}],
        "outbounds": [{
            "protocol": "vless",
            "settings": {"vnext": [{"address": "193.233.138.42", "port": vps_port, "users": [{"id": "04756662-2f98-44ad-a53a-369d29118670", "encryption": "none", "flow": "xtls-rprx-vision"}]}]},
            "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": {"serverName": sni, "fingerprint": fp, "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE", "shortId": "dae45f", "spiderX": "/"}}
        }]
    }
    fn = f"scratch/test_{vps_port}_{fp}.json"
    with open(fn, "w") as f:
        json.dump(cfg, f)
    p = subprocess.Popen([XRAY, "run", "-c", fn], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": f"http://127.0.0.1:{port}"}))
    latencies = []
    for _ in range(2):
        t0 = time.time()
        try:
            req = urllib.request.Request("https://cp.cloudflare.com/generate_204", headers={"User-Agent": "Happ/3.2.0"})
            with opener.open(req, timeout=5) as r:
                latencies.append(round((time.time() - t0) * 1000))
        except Exception as e:
            latencies.append(f"ERR: {e}")
    p.terminate()
    print(f"{name} -> {latencies}")
