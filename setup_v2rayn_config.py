import json
import os

config_path = "v2rayN/guiNConfig.json"

server_item = {
    "configType": 1,
    "configVersion": 2,
    "address": "193.233.138.42",
    "port": 443,
    "id": "04756662-2f98-44ad-a53a-369d29118670",
    "alterId": 0,
    "security": "none",
    "network": "tcp",
    "remarks": "Финляндия VLESS Reality 443 (YouTube + Обход блокировок)",
    "headerType": "none",
    "requestHost": "",
    "path": "",
    "streamSecurity": "reality",
    "allowInsecure": False,
    "sni": "dl.google.com",
    "fingerprint": "chrome",
    "alpn": "",
    "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
    "shortId": "b07c",
    "spiderX": "/ec2973b76d0d4ce",
    "flow": "xtls-rprx-vision",
    "coreType": 1,
    "displayIndex": 1
}

guin_config = {
    "inbound": [
        {
            "localPort": 10808,
            "protocol": "socks",
            "udpEnabled": True,
            "sniffingEnabled": True,
            "destOverride": ["http", "tls"]
        }
    ],
    "sysProxyType": 1,
    "routingMode": 1,
    "uiItem": {
        "currentLanguage": "ru"
    },
    "profileItems": [server_item]
}

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(guin_config, f, indent=2, ensure_ascii=False)

print("Pre-configured v2rayN with VLESS Reality server!")
