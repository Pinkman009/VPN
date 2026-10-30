import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_ssh_commands(cmds):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

    for cmd in cmds:
        print(f"=== {cmd} ===")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        if out:
            print(out)
        if err:
            print(f"[STDERR]: {err}")
    client.close()

if __name__ == '__main__':
    commands = [
        "systemctl is-active x-ui",
        "ls -la /etc/x-ui/ || true",
        "sqlite3 /etc/x-ui/x-ui.db 'SELECT * FROM settings;' || true",
        "sqlite3 /etc/x-ui/x-ui.db 'SELECT id, user_id, up, down, total, remark, enable, port, protocol, settings, stream_settings FROM inbounds;' || true",
        "curl -s ifconfig.me; echo ''",
        "curl -s https://ipinfo.io/json; echo ''"
    ]
    run_ssh_commands(commands)
