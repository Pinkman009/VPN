import sqlite3, json

con = sqlite3.connect(r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db')
cur = con.cursor()
row = cur.execute("SELECT * FROM ProfileItem").fetchone()
cols = [d[0] for d in cur.description]
d = dict(zip(cols, row))
for k, v in d.items():
    print(f"{k}: {repr(v).encode('ascii', 'backslashreplace').decode('ascii')}")
con.close()

