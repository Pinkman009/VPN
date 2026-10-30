import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    return out

print("LISTENING PORTS:")
print(run("ss -tulpn | grep xray"))

print("\nPROCESSES:")
print(run("ps aux | grep xray | grep -v grep"))

print("\nXRAY ERROR LOG:")
print(run("tail -n 20 /var/log/x-ui/error.log"))

ssh.close()
