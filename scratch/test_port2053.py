import json
import subprocess
import time
import urllib.request
import os

XRAY_PATH = r"c:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

cfg = {
    "log": {"loglevel": "warning"},
    "dns": {
        "servers": ["77.88.8.8", "8.8.8.8"],
        "queryStrategy": "UseIPv4"
    },
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
                        "port": 2053,
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
                    "serverName": "azure.microsoft.com",
                    "fingerprint": "chrome",
                    "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
                    "shortId": "dae45f",
                    "spiderX": "/"
                }
            }
        },
        {
            "tag": "direct",
            "protocol": "freedom"
        }
    ]
}

with open("test_port2053.json", "w") as f:
    json.dump(cfg, f, indent=2)

proc = subprocess.Popen([XRAY_PATH, "run", "-c", "test_port2053.json"])
time.sleep(1.5)

h = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10897', 'https': 'http://127.0.0.1:10897'})
op = urllib.request.build_opener(h)

test_targets = [
    ('IP Check', 'https://api.ipify.org'),
    ('Google AI Studio', 'https://aistudio.google.com/'),
    ('YouTube', 'https://www.youtube.com/generate_204'),
    ('OpenAI API', 'https://api.openai.com/v1/models'),
    ('Claude API', 'https://api.anthropic.com/v1/messages')
]

for name, url in test_targets:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
        with op.open(req, timeout=8) as resp:
            print(f"[{name}] SUCCESS -> Status {resp.status} in {round((time.time()-t0)*1000)}ms")
    except urllib.error.HTTPError as he:
        print(f"[{name}] HTTP RESPONSE -> Status {he.code} in {round((time.time()-t0)*1000)}ms")
    except Exception as e:
        print(f"[{name}] FAILED -> {e}")

proc.terminate()
proc.wait()
print("Done.")
