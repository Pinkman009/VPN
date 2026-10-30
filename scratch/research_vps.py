import paramiko, json, sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)

def run(cmd):
    _, o, e = ssh.exec_command(cmd)
    return (o.read() + e.read()).decode('utf-8', errors='replace').strip()

py = r'''
import sqlite3, json
c = sqlite3.connect("/etc/x-ui/x-ui.db").cursor()
rows = dict(c.execute("select key, value from settings").fetchall())
for k in sorted(rows):
    v = rows[k]
    if k == "xrayTemplateConfig":
        try:
            t = json.loads(v)
            warp = [r for r in t.get("routing", {}).get("rules", []) if r.get("outboundTag") == "warp"]
            print("TEMPLATE warp domains count:", len(warp[0]["domain"]) if warp else None)
            print("TEMPLATE outbounds:", [o.get("tag") for o in t.get("outbounds", [])])
        except Exception as e:
            print("Template parse error:", e)
    elif "pass" not in k.lower() and "secret" not in k.lower():
        print(f"{k} = {v[:80]}")
'''
sftp = ssh.open_sftp()
f = sftp.file('/tmp/q.py', 'w')
f.write(py)
f.close()
sftp.close()

print(run('python3 /tmp/q.py'))
print('--- running config warp count ---')
print(run("python3 -c \"import json;c=json.load(open('/usr/local/x-ui/bin/config.json'));print([len(r.get('domain',[])) for r in c['routing']['rules'] if r.get('outboundTag')=='warp'])\""))
print('--- open ports ---')
print(run('ss -tlnp | grep -v 127.0.0.1'))
print('--- system info ---')
print(run('python3 --version; which nginx; ufw status | head -15'))
ssh.close()
