import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

# This script sets the Xray template in 3X-UI to route traffic through WARP for
# sites that block datacenter IPs (ChatGPT, Google captchas, Netflix, etc.)
script = r'''
import sqlite3, json, subprocess

xray_template = {
    "api": {
        "services": ["HandlerService", "LoggerService", "StatsService"],
        "tag": "api"
    },
    "inbounds": [
        {
            "listen": "127.0.0.1",
            "port": 62789,
            "protocol": "dokodemo-door",
            "settings": {"address": "127.0.0.1"},
            "tag": "api"
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "settings": {},
            "tag": "direct"
        },
        {
            "protocol": "blackhole",
            "settings": {},
            "tag": "blocked"
        },
        {
            "protocol": "socks",
            "settings": {
                "servers": [
                    {
                        "address": "127.0.0.1",
                        "port": 40000
                    }
                ]
            },
            "tag": "warp"
        }
    ],
    "policy": {
        "levels": {
            "0": {
                "statsUserDownlink": True,
                "statsUserUplink": True
            }
        },
        "system": {
            "statsInboundDownlink": True,
            "statsInboundUplink": True,
            "statsOutboundDownlink": True,
            "statsOutboundUplink": True
        }
    },
    "routing": {
        "rules": [
            {
                "inboundTag": ["api"],
                "outboundTag": "api",
                "type": "field"
            },
            {
                "type": "field",
                "outboundTag": "blocked",
                "ip": ["geoip:private"]
            },
            {
                "type": "field",
                "outboundTag": "blocked",
                "protocol": ["bittorrent"]
            },
            {
                "type": "field",
                "outboundTag": "warp",
                "domain": [
                    "openai.com",
                    "chatgpt.com",
                    "chat.openai.com",
                    "api.openai.com",
                    "auth0.openai.com",
                    "platform.openai.com",
                    "anthropic.com",
                    "claude.ai",
                    "api.anthropic.com",
                    "netflix.com",
                    "nflxvideo.net",
                    "nflxext.com",
                    "nflximg.net",
                    "nflxso.net",
                    "spotify.com",
                    "scdn.co",
                    "spotifycdn.com",
                    "notion.so",
                    "notion-static.com",
                    "notionusercontent.com",
                    "canva.com",
                    "canva.dev",
                    "perplexity.ai",
                    "bing.com",
                    "copilot.microsoft.com"
                ]
            }
        ]
    },
    "stats": {}
}

template_str = json.dumps(xray_template, indent=2)

conn = sqlite3.connect("/etc/x-ui/x-ui.db")
c = conn.cursor()

# Check if xrayTemplateConfig exists
existing = c.execute("SELECT value FROM settings WHERE key='xrayTemplateConfig'").fetchone()
if existing:
    c.execute("UPDATE settings SET value=? WHERE key='xrayTemplateConfig'", (template_str,))
    print("Updated existing xrayTemplateConfig")
else:
    c.execute("INSERT INTO settings (key, value) VALUES ('xrayTemplateConfig', ?)", (template_str,))
    print("Inserted new xrayTemplateConfig")

conn.commit()
conn.close()

# Restart x-ui to apply template
r = subprocess.run("x-ui restart", shell=True, capture_output=True, text=True, timeout=30)
print("x-ui restart:", r.stdout.strip(), r.stderr.strip())

import time
time.sleep(3)

# Verify xray is running with the template
r = subprocess.run("ss -tlnp | grep xray", shell=True, capture_output=True, text=True, timeout=10)
print()
print("=== Xray listening ports after template applied ===")
print(r.stdout.strip())

# Test WARP outbound
print()
print("=== Test: Direct IP (without WARP) ===")
r = subprocess.run("curl -s https://api.ipify.org", shell=True, capture_output=True, text=True, timeout=10)
print("Direct IP:", r.stdout.strip())

print()
print("=== Test: WARP IP (via SOCKS5) ===")
r = subprocess.run("curl -x socks5h://127.0.0.1:40000 -s https://api.ipify.org", shell=True, capture_output=True, text=True, timeout=10)
print("WARP IP:", r.stdout.strip())
'''

run_script_on_vps(script)
