from run_remote import run_script_on_vps

script = """
import os, json, subprocess

os.makedirs('/var/log/xray', exist_ok=True)

with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)

cfg["log"]["access"] = "/var/log/xray/access.log"
cfg["log"]["error"] = "/var/log/xray/error.log"
cfg["log"]["loglevel"] = "debug"

with open('/usr/local/x-ui/bin/config.json', 'w') as f:
    json.dump(cfg, f, indent=2)

subprocess.run(["systemctl", "restart", "x-ui"])
print("Configured /var/log/xray logs and restarted x-ui")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
