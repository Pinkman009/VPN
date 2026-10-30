import json
import subprocess
import time
import urllib.request

XRAY_PATH = r"c:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

cfg = {
    "log": {"loglevel": "debug"},
    "inbounds": [
        {"tag": "http-in", "listen": "127.0.0.1", "port": 10897, "protocol": "http"}
    ],
    "outbounds": [
        {
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": "193.233.138.42",
                        "port": 443,
                        "users": [
                            {"id": "04756662-2f98-44ad-a53a-369d29118670", "encryption": "none", "flow": "xtls-rprx-vision"}
                        ]
                    }
                ]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": "speed.cloudflare.com",
                    "fingerprint": "chrome",
                    "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
                    "shortId": "dae45f",
                    "spiderX": "/"
                },
                "sockopt": {
                    "dialerProxy": "fragment"
                }
            }
        },
        {
            "tag": "fragment",
            "protocol": "freedom",
            "settings": {
                "fragment": {
                    "packets": "1-3",
                    "length": "10-20",
                    "interval": "10-20"
                }
            }
        }
    ]
}

with open("test_aistudio.json", "w") as f:
    json.dump(cfg, f, indent=2)

proc = subprocess.Popen([XRAY_PATH, "run", "-c", "test_aistudio.json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.5)

h = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10897', 'https': 'http://127.0.0.1:10897'})
op = urllib.request.build_opener(h)

urls = [
    'https://aistudio.google.com/',
    'https://www.youtube.com/',
    'https://chatgpt.com/'
]

for u in urls:
    try:
        t0 = time.time()
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
        with op.open(req, timeout=12) as r:
            print(f"URL: {u} -> SUCCESS {r.status} in {round((time.time()-t0)*1000)}ms")
    except urllib.error.HTTPError as he:
        print(f"URL: {u} -> HTTP ERROR {he.code} in {round((time.time()-t0)*1000)}ms")
    except Exception as e:
        print(f"URL: {u} -> ERROR: {e}")

proc.terminate()
try:
    stdout, _ = proc.communicate(timeout=2)
    for line in stdout.splitlines()[-15:]:
        print("XRAY:", line)
except Exception:
    pass
