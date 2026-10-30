import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

def run_pty(cmd, wait=5):
    """Run a command with PTY allocation (so warp-cli sees a TTY)."""
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    time.sleep(wait)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f"CMD: {cmd}")
    if out.strip():
        print(f"OUT: {out.strip()}")
    if err.strip():
        print(f"ERR: {err.strip()}")
    print()
    return out

# Step 1: Register with PTY
print("=== Step 1: Registration with PTY ===")
run_pty("warp-cli registration new", wait=5)

# Step 2: Set proxy mode
print("=== Step 2: Set proxy mode ===")
run_pty("warp-cli mode proxy", wait=3)

# Step 3: Set proxy port
print("=== Step 3: Set proxy port ===")
run_pty("warp-cli proxy port 40000", wait=3)

# Step 4: Connect
print("=== Step 4: Connect ===")
run_pty("warp-cli connect", wait=5)

# Step 5: Verify status
print("=== Step 5: Status ===")
run_pty("warp-cli status", wait=3)

# Step 6: Test WARP via SOCKS5
print("=== Step 6: Test WARP SOCKS5 proxy ===")
run_pty("curl -x socks5h://127.0.0.1:40000 -s --max-time 10 https://cloudflare.com/cdn-cgi/trace", wait=12)

# Step 7: Check listening
print("=== Step 7: Listening ports ===")
run_pty("ss -tlnp | grep 40000", wait=3)

client.close()
