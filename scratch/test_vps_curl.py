import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8').strip()

print("DIRECT VPS HTTP CODE:", run('curl -s -o /dev/null -w "%{http_code}" https://chatgpt.com'))
print("WARP SOCKS5 HTTP CODE:", run('curl -s --socks5 127.0.0.1:40000 -o /dev/null -w "%{http_code}" https://chatgpt.com'))
ssh.close()
