import json

path = r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\binConfigs\config.json'
with open(path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

# Fix network
for ob in cfg.get('outbounds', []):
    if ob.get('tag') == 'proxy':
        if 'streamSettings' in ob:
            ob['streamSettings']['network'] = 'tcp'

# Fix DNS
cfg['dns'] = {
    "servers": [
        "77.88.8.8",
        "8.8.8.8"
    ],
    "tag": "dns-module"
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print('Updated binConfigs/config.json')
