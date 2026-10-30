import sqlite3

db_path = r'C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\guiConfigs\guiNDB.db'
con = sqlite3.connect(db_path)
cur = con.cursor()

# Update Profile 1 to swdist.apple.com
cur.execute("""
UPDATE ProfileItem 
SET Sni = 'swdist.apple.com', 
    Remarks = 'Финляндия VLESS Reality 443 (Apple CDN)'
WHERE Port = 443
""")
print(f"Updated {cur.rowcount} rows in ProfileItem for port 443")

# Check if port 2053 exists, if not duplicate with www.samsung.com
row2 = cur.execute("SELECT count(*) FROM ProfileItem WHERE Port = 2053").fetchone()[0]
if not row2:
    row1 = cur.execute("SELECT * FROM ProfileItem WHERE Port = 443").fetchone()
    # Replace columns for 2053
    r_list = list(row1)
    # IndexId is col 0
    import uuid
    r_list[0] = str(uuid.uuid4())
    r_list[8] = 'Финляндия VLESS Reality 2053 (Samsung CDN)' # Remarks
    r_list[10] = 2053 # Port
    r_list[19] = 'www.samsung.com' # Sni
    cur.execute(f"INSERT INTO ProfileItem VALUES ({','.join(['?']*len(r_list))})", r_list)
    print("Added backup profile for port 2053 with Samsung CDN!")

con.commit()
con.close()
