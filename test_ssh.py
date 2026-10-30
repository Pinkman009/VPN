import paramiko
import sys

def test_ssh():
    host = "193.233.138.42"
    user = "root"
    password = "xXM3yS7biwUj"
    
    print(f"Connecting to {host} as {user}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=10)
        print("Connected successfully!")
        
        commands = [
            "cat /etc/os-release | grep PRETTY_NAME",
            "uname -a",
            "free -m",
            "df -h /",
            "uptime",
            "ss -tulpn | head -n 20"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out:
                print(out)
            if err:
                print("ERR:", err)
                
        client.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_ssh()
