import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

db_path = r'v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Update Profile 1 (Port 443)
c.execute("""
UPDATE ProfileItem
SET Remarks = 'Финляндия VLESS Reality 443 (Cloudflare - Основной)',
    Address = '193.233.138.42',
    Port = 443,
    Sni = 'speed.cloudflare.com',
    RequestHost = 'speed.cloudflare.com',
    PublicKey = 't0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE',
    ShortId = 'dae45f',
    SpiderX = '/',
    Fingerprint = 'chrome',
    Flow = 'xtls-rprx-vision',
    Id = '04756662-2f98-44ad-a53a-369d29118670',
    StreamSecurity = 'reality',
    Network = 'tcp'
WHERE Port = 443 OR IndexId = '4850475246551215996'
""")

# 2. Update Profile 2 (Port 2053)
c.execute("""
UPDATE ProfileItem
SET Remarks = 'Финляндия VLESS Reality 2053 (Azure - Резервный)',
    Address = '193.233.138.42',
    Port = 2053,
    Sni = 'azure.microsoft.com',
    RequestHost = 'azure.microsoft.com',
    PublicKey = 't0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE',
    ShortId = 'dae45f',
    SpiderX = '/',
    Fingerprint = 'chrome',
    Flow = 'xtls-rprx-vision',
    Id = '04756662-2f98-44ad-a53a-369d29118670',
    StreamSecurity = 'reality',
    Network = 'tcp'
WHERE Port = 2053 OR IndexId = '747b909f-bdc4-4bb8-b170-a3584a3f39da'
""")

conn.commit()

print("Обновленные профили в v2rayN:")
for row in c.execute("SELECT IndexId, Remarks, Address, Port, Sni, Flow, ShortId FROM ProfileItem").fetchall():
    print(f"ID={row[0]} | Name='{row[1]}' | Server={row[2]}:{row[3]} | SNI={row[4]} | Flow={row[5]} | SID={row[6]}")

conn.close()
print("\nv2rayN база данных успешно обновлена актуальными серверами!")
