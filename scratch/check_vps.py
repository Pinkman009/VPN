import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

stdin, stdout, stderr = client.exec_command('cat /usr/local/x-ui/bin/config.json')
cfg_text = stdout.read().decode('utf-8')
cfg = json.loads(cfg_text)

print("=== OUTBOUNDS ===")
for ob in cfg.get('outbounds', []):
    print("Tag:", ob.get('tag'), "Protocol:", ob.get('protocol'))

print("=== ROUTING RULES ===")
for r in cfg.get('routing', {}).get('rules', []):
    print("Rule:", r.get('outboundTag'), "domain:", r.get('domain', [])[:3], "ip:", r.get('ip', []))

client.close()
