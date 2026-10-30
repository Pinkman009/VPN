import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

# 1. Enable subJson
c.execute("UPDATE settings SET value='true' WHERE key='subJsonEnable'")

# 2. Configure subJsonDns to use reliable non-blocked DNS
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
c.execute("UPDATE settings SET value=? WHERE key='subJsonDns'", (json.dumps(dns_config, indent=2),))

# 3. Enable Happ routing
c.execute("UPDATE settings SET value='true' WHERE key='subEnableRouting'")
c.execute("UPDATE settings SET value='true' WHERE key='happLinkEnable'")

conn.commit()
conn.close()

subprocess.run("x-ui restart", shell=True)
print("Configured subJsonEnable=true and reliable DNS in 3X-UI!")
'''

run_script_on_vps(script)
