from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# 1. Routing rules for Xray/v2ray subscriptions (subRoutingRules)
# Blocks QUIC (UDP 443) and directs Russian domains/IPs
v2ray_rules = [
    {
        "type": "field",
        "port": "443",
        "network": "udp",
        "outboundTag": "block"
    },
    {
        "type": "field",
        "domain": [
            "geosite:category-ru",
            "regexp:.*\\\\.ru$",
            "regexp:.*\\\\.su$",
            "regexp:.*\\\\.xn--p1ai$"
        ],
        "outboundTag": "direct"
    },
    {
        "type": "field",
        "ip": [
            "geoip:ru",
            "geoip:private"
        ],
        "outboundTag": "direct"
    }
]

# 2. Clash rules
clash_rules = \"\"\"- AND,((NETWORK,udp),(DST-PORT,443)),REJECT
- GEOSITE,category-ru,DIRECT
- GEOIP,RU,DIRECT
- MATCH,PROXY\"\"\"

# 3. Sing-box / JSON DNS
dns_config = {
    "servers": [
        {
            "tag": "remote",
            "address": "tcp://8.8.8.8",
            "detour": "proxy"
        },
        {
            "tag": "local",
            "address": "77.88.8.8",
            "detour": "direct"
        }
    ],
    "rules": [
        {
            "geosite": "category-ru",
            "server": "local"
        },
        {
            "domain_suffix": [".ru", ".xn--p1ai", ".su"],
            "server": "local"
        }
    ],
    "strategy": "prefer_ipv4"
}

c.execute("UPDATE settings SET value=? WHERE key='subRoutingRules'", (json.dumps(v2ray_rules),))
c.execute("UPDATE settings SET value='true' WHERE key='subEnableRouting'")
c.execute("UPDATE settings SET value=? WHERE key='subClashRules'", (clash_rules,))
c.execute("UPDATE settings SET value='true' WHERE key='subClashEnableRouting'")
c.execute("UPDATE settings SET value='true' WHERE key='subClashAutoDetect'")
c.execute("UPDATE settings SET value=? WHERE key='subJsonDns'", (json.dumps(dns_config, indent=2),))

conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True)
print("Successfully injected DNS and Block QUIC into all 3X-UI subscription generators!")
"""

run_script_on_vps(script)
