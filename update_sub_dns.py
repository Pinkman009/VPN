from run_remote import run_script_on_vps

script = """
import sqlite3

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

dns_config = '''{
  "servers": [
    {
      "tag": "remote",
      "address": "https://1.1.1.1/dns-query",
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
}'''

c.execute("UPDATE settings SET value=? WHERE key='subJsonDns'", (dns_config,))
c.execute("UPDATE settings SET value='true' WHERE key='subJsonAutoDetect'")
c.execute("UPDATE settings SET value='.*' WHERE key='subJsonUserAgentRegex'")
conn.commit()
print("Updated subJsonDns and subJsonAutoDetect in x-ui.db")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
