import sqlite3
db = sqlite3.connect('data/database.sqlite')
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for t in tables:
    name = t[0]
    cursor.execute(f"PRAGMA table_info({name})")
    cols = cursor.fetchall()
    print(f"Table {name}: {[c[1] for c in cols]}")

db.close()
