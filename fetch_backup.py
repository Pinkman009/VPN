import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

sftp = client.open_sftp()

os.makedirs('backup', exist_ok=True)

remote_files = [
    ('/etc/x-ui/x-ui.db', 'backup/x-ui.db'),
    ('/usr/local/x-ui/bin/config.json', 'backup/config.json'),
    ('/etc/ufw/user.rules', 'backup/ufw_user.rules'),
    ('/etc/sysctl.d/99-custom-vpn.conf', 'backup/99-custom-vpn.conf')
]

for r_path, l_path in remote_files:
    try:
        sftp.get(r_path, l_path)
        print(f"Downloaded {r_path} -> {l_path} ({os.path.getsize(l_path)} bytes)")
    except Exception as e:
        print(f"Failed to fetch {r_path}: {e}")

sftp.close()
client.close()
print("Backup completed successfully!")
