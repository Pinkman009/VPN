import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = r'''
import subprocess

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if err:
        out += " STDERR: " + err
    return out

# === SYSCTL OPTIMIZATION ===
sysctl_conf = """
# === VPN Performance Optimization (2026-10-12) ===

# BBR congestion control (already enabled, ensure persistence)
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# TCP Fast Open (3 = client + server)
net.ipv4.tcp_fastopen = 3

# Increase connection backlog
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096

# Increase TCP buffer sizes (16MB max for high-latency links)
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# MTU probing (helps with path MTU discovery)
net.ipv4.tcp_mtu_probing = 1

# Disable slow start after idle (keeps connections fast)
net.ipv4.tcp_slow_start_after_idle = 0

# Enable TCP window scaling
net.ipv4.tcp_window_scaling = 1

# Reduce TIME_WAIT sockets
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1

# Increase max open files tracking
net.core.netdev_max_backlog = 16384

# Optimize for keepalive connections
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5
"""

# Write sysctl config
with open("/etc/sysctl.d/99-vpn-optimize.conf", "w") as f:
    f.write(sysctl_conf)

print("Written /etc/sysctl.d/99-vpn-optimize.conf")

# Apply
result = run("sysctl --system 2>&1 | tail -30")
print("sysctl --system result (last 30 lines):")
print(result)

# Verify key values
print()
print("=== VERIFICATION ===")
for key in ["net.core.default_qdisc", "net.ipv4.tcp_congestion_control",
            "net.ipv4.tcp_fastopen", "net.core.rmem_max", "net.core.wmem_max",
            "net.ipv4.tcp_mtu_probing", "net.ipv4.tcp_slow_start_after_idle",
            "net.ipv4.tcp_max_syn_backlog"]:
    print("  " + run("sysctl " + key))
'''

run_script_on_vps(script)
