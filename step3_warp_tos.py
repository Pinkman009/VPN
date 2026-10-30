import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess, time, os

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "WARP_CLI_ACCEPT_TOS": "yes"})
    out = r.stdout.strip()
    err = r.stderr.strip()
    return out + ("\n" + err if err else "")

# Try multiple approaches to accept ToS
print("=== Approach 1: Set WARP_CLI_ACCEPT_TOS env ===")

# First try settings for ToS
print(run("warp-cli settings --help 2>&1 | head -20"))
print()

# Try registration with env var
print("=== Registration ===")
# Write mdm config to accept ToS non-interactively
mdm_config = '{"organization": "", "accept_tos": true}'
with open("/var/lib/cloudflare-warp/mdm.xml", "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
</dict>
</plist>""")

# Restart warp-svc to pick up config
print(run("systemctl restart warp-svc"))
time.sleep(2)

# Try piping yes
print(run("yes | warp-cli registration new 2>&1"))
time.sleep(1)
print()

print("=== Status after registration ===")
print(run("warp-cli status 2>&1"))
'''

run_script_on_vps(script)
