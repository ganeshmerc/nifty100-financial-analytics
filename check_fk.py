import sqlite3

conn = sqlite3.connect("db/nifty100.db")
conn.execute("PRAGMA foreign_keys = ON")

result = conn.execute("PRAGMA foreign_key_check").fetchall()

print(f"Foreign key violations: {len(result)}")
if result:
    print(result[:10])

conn.close()