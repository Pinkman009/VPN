import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("193.233.138.42", 22, "root", "xXM3yS7biwUj", timeout=10)

commands = [
    "lscpu",
    "free -m",
    "df -h /",
    "uptime",
    "vnstat -h 2>/dev/null || ip -s link",
    "cat /sys/class/net/*/speed 2>/dev/null"
]

for cmd in commands:
    print(f"=== {cmd} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

ssh.close()
