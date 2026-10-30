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
        },
        {
            "tag": "block",
            "protocol": "blackhole"
        }
    ],
    "routing": {
        "domainStrategy": "AsIs",
        "rules": [
            {
                "type": "field",
                "outboundTag": "block",
                "port": "443",
                "network": "udp"
            },
            {
                "type": "field",
                "outboundTag": "direct",
                "ip": ["geoip:private"]
            },
            {
                "type": "field",
                "outboundTag": "direct",
                "domain": [
                    "geosite:category-ru",
                    "regexp:.*\\.ru$",
                    "regexp:.*\\.su$",
                    "regexp:.*\\.xn--p1ai$"
                ]
            },
            {
                "type": "field",
                "outboundTag": "proxy",
                "network": "tcp,udp"
            }
        ]
    }
}

with open("test_full_architecture.json", "w") as f:
    json.dump(cfg, f, indent=2)

proc = subprocess.Popen([XRAY_PATH, "run", "-c", "test_full_architecture.json"])
time.sleep(1.5)

h = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10897', 'https': 'http://127.0.0.1:10897'})
op = urllib.request.build_opener(h)

test_targets = [
    ('IP Check', 'https://api.ipify.org'),
    ('Google AI Studio', 'https://aistudio.google.com/'),
    ('YouTube', 'https://www.youtube.com/generate_204'),
    ('OpenAI API', 'https://api.openai.com/v1/models'),
    ('Claude API', 'https://api.anthropic.com/v1/messages'),
    ('Sberbank (RU Direct)', 'https://www.sberbank.ru/')
]

for name, url in test_targets:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
        with op.open(req, timeout=10) as resp:
            print(f"[{name}] SUCCESS -> Status {resp.status}")
    except urllib.error.HTTPError as he:
        print(f"[{name}] HTTP RESPONSE -> Status {he.code}")
    except Exception as e:
        print(f"[{name}] FAILED -> {e}")

proc.terminate()
proc.wait()
print("All tests done.")
