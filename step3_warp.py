import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess, time

def run(cmd, timeout=60):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    out = r.stdout.strip()
    err = r.stderr.strip()
    return out + ("\n" + err if err else "")

# Step 1: Add Cloudflare WARP repo and install
print("=== Installing Cloudflare WARP ===")
print(run("curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg"))
print(run('echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/cloudflare-client.list'))
print(run("apt-get update -qq 2>&1 | tail -5", timeout=120))
print(run("apt-get install -y cloudflare-warp 2>&1 | tail -10", timeout=120))

# Step 2: Register WARP
print()
print("=== Registering WARP ===")
print(run("warp-cli registration new --accept-tos 2>&1"))

# Step 3: Set WARP to proxy mode (SOCKS5 on 127.0.0.1:40000)
print()
print("=== Setting proxy mode ===")
print(run("warp-cli mode proxy 2>&1"))
print(run("warp-cli proxy port 40000 2>&1"))

# Step 4: Connect
print()
print("=== Connecting WARP ===")
print(run("warp-cli connect 2>&1"))
time.sleep(3)

# Step 5: Verify
print()
print("=== Verification ===")
print("Status:", run("warp-cli status 2>&1"))
print()
print("WARP IP test:", run("curl -x socks5h://127.0.0.1:40000 -s https://cloudflare.com/cdn-cgi/trace 2>&1 | head -15"))
print()
print("Listening:", run("ss -tlnp | grep 40000"))
'''

run_script_on_vps(script)
