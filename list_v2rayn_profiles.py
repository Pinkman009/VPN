import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db')
c = conn.cursor()

print("Existing Profiles in v2rayN:")
for row in c.execute("SELECT IndexId, Remarks, Address, Port, Sni, PublicKey, ShortId, Flow, Id FROM ProfileItem").fetchall():
    print(f"ID={row[0]} | Name='{row[1]}' | Server={row[2]}:{row[3]} | SNI={row[4]} | Flow={row[7]}")

conn.close()
