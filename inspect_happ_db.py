import sqlite3, json

conn = sqlite3.connect(r'C:\Users\MiPro\AppData\Local\Happ\subs.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables in subs.db:', [t[0] for t in tables])

for t in tables:
    name = t[0]
    print(f'\n=== Table: {name} ===')
    cols = [col[1] for col in c.execute(f"PRAGMA table_info({name})").fetchall()]
    print('Columns:', cols)
    rows = c.execute(f'SELECT * FROM {name} LIMIT 5').fetchall()
    for r in rows:
        print(r)

conn.close()
