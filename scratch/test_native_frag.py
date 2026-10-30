import json
import subprocess
import time
import urllib.request
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
XRAY_PATH = r"c:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

cfg = {
    "log": {"loglevel": "debug"},
    "inbounds": [
        {
            "tag": "http-in",
            "listen": "127.0.0.1",
            "port": 10897,
            "protocol": "http"
        }
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
                            {
                                "id": "04756662-2f98-44ad-a53a-369d29118670",
                                "encryption": "none",
                                "flow": "xtls-rprx-vision"
                            }
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
        },
        {
            "tag": "direct",
            "protocol": "freedom"
        }
    ]
}

with open("test_native_frag.json", "w") as f:
    json.dump(cfg, f, indent=2)

proc = subprocess.Popen([XRAY_PATH, "run", "-c", "test_native_frag.json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.5)

h = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10897', 'https': 'http://127.0.0.1:10897'})
op = urllib.request.build_opener(h)

try:
    req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'Mozilla/5.0'})
    with op.open(req, timeout=8) as r:
        print("NATIVE FRAGMENT RESULT -> IP:", r.read().decode('utf-8'))
except Exception as e:
    print("NATIVE FRAGMENT FAILED ->", e)

proc.terminate()
try:
    stdout, _ = proc.communicate(timeout=2)
    print("XRAY LOGS:")
    for line in stdout.splitlines()[-10:]:
        print(line)
except Exception:
    pass
