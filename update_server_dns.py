from run_remote import run_script_on_vps

script = """
import json, sqlite3, subprocess

# 1. Update bin/config.json on server
with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)

cfg["routing"]["domainStrategy"] = "IPIfNonMatch"
cfg["dns"] = {
    "servers": [
        "1.1.1.1",
        "8.8.8.8",
        "localhost"
    ],
    "queryStrategy": "UseIPv4"
}

for ob in cfg.get("outbounds", []):
    if ob.get("protocol") == "freedom":
        ob.setdefault("settings", {})["domainStrategy"] = "UseIPv4"

with open('/usr/local/x-ui/bin/config.json', 'w') as f:
    json.dump(cfg, f, indent=2)

print("Updated /usr/local/x-ui/bin/config.json")

# 2. Restart x-ui / xray
subprocess.run(["systemctl", "restart", "x-ui"])
print("x-ui restarted successfully")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
