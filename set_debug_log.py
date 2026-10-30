from run_remote import run_script_on_vps

script = """
import json, subprocess

with open('/usr/local/x-ui/bin/config.json') as f:
    cfg = json.load(f)

cfg["log"]["loglevel"] = "debug"

with open('/usr/local/x-ui/bin/config.json', 'w') as f:
    json.dump(cfg, f, indent=2)

subprocess.run(["systemctl", "restart", "x-ui"])
print("Xray restarted with loglevel: debug")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
