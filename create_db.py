import sqlite3
from pathlib import Path

schema_path = Path("db/schema.sql")
db_path = Path("db/nifty100.db")

schema_sql = schema_path.read_text()

conn = sqlite3.connect(db_path)
conn.executescript(schema_sql)
conn.close()

print("Database created from schema.")