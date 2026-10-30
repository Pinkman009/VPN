import sqlite3

con = sqlite3.connect(r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db')
cur = con.cursor()
for t in ['DNSItem', 'RoutingItem']:
    rows = cur.execute(f"SELECT * FROM {t}").fetchall()
    cols = [d[0] for d in cur.description]
    print(f"Table {t} cols: {cols}")
    for r in rows:
        # print ascii-safe representation
        print("  ", [str(x).encode('ascii', 'backslashreplace').decode('ascii') for x in r])
con.close()
