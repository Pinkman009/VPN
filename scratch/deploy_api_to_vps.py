import paramiko
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

LOCAL_SCRIPT = os.path.join(os.path.dirname(__file__), "teletok_server_api.py")
with open(LOCAL_SCRIPT, "r", encoding="utf-8") as f:
    api_code = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("193.233.138.42", 22, "root", "xXM3yS7biwUj", timeout=10)

sftp = ssh.open_sftp()
with sftp.file("/usr/local/bin/teletok_server_api.py", "w") as rf:
    rf.write(api_code)
sftp.chmod("/usr/local/bin/teletok_server_api.py", 0o755)
sftp.close()

# Restart service and check status
stdin, stdout, stderr = ssh.exec_command("systemctl restart teletok-api && systemctl status teletok-api --no-pager")
print("STATUS:\n", stdout.read().decode())
print("ERR:\n", stderr.read().decode())

ssh.close()
