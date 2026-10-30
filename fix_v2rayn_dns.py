import json, sqlite3

# 1. Update guiNConfig.json
config_path = r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\guiConfigs\guiNConfig.json'
with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

cfg['SimpleDNSItem']['DirectDNS'] = '77.88.8.8'
cfg['SimpleDNSItem']['RemoteDNS'] = '8.8.8.8'
cfg['SimpleDNSItem']['BootstrapDNS'] = '77.88.8.8'

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print('Updated guiNConfig.json successfully')

# 2. Update guiNDB.db ProfileItem network to tcp
db_path = r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db'
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("UPDATE ProfileItem SET Network = 'tcp' WHERE Network = 'raw'")
con.commit()
print(f'Updated {cur.rowcount} rows in guiNDB.db ProfileItem')
con.close()
