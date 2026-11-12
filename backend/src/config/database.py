import json, sqlite3
from contextlib import contextmanager
from urllib.parse import urlparse, unquote
from src.config.settings import DATABASE_URL
TABLES = ("users", "datasets", "models", "runs", "plans", "reports", "audit")
@contextmanager
def connection():
    if DATABASE_URL.startswith("sqlite:///"):
        db = sqlite3.connect(DATABASE_URL[10:], timeout=20)
    else:
        import pymysql
        u = urlparse(DATABASE_URL)
        db = pymysql.connect(host=u.hostname, port=u.port or 3306, user=unquote(u.username), password=unquote(u.password), database=u.path[1:], charset="utf8mb4", connect_timeout=5)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def execute(db, sql, args=()):
    cur = db.cursor()
    cur.execute(sql if DATABASE_URL.startswith("sqlite") else sql.replace("?", "%s"), args)
    return cur

def initialize():
    with connection() as db:
        for table in TABLES:
            execute(db, f"CREATE TABLE IF NOT EXISTS {table} (id VARCHAR(80) PRIMARY KEY, natural_key VARCHAR(180) UNIQUE NOT NULL, payload LONGTEXT NOT NULL)")

def get(table, key):
    assert table in TABLES
    with connection() as db:
        row=execute(db, f"SELECT payload FROM {table} WHERE id=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None

def all_rows(table):
    assert table in TABLES
    with connection() as db:
        rows=execute(db,f"SELECT payload FROM {table} ORDER BY natural_key").fetchall()
    return [json.loads(r[0]) for r in rows]

def insert(table, obj, natural_key=None, preserve=False):
    assert table in TABLES
    natural_key=natural_key or obj["id"]
    with connection() as db:
        found=execute(db,f"SELECT payload FROM {table} WHERE natural_key=?",(natural_key,)).fetchone()
        if found:
            if preserve: return json.loads(found[0])
            execute(db,f"UPDATE {table} SET payload=? WHERE natural_key=?",(json.dumps(obj,ensure_ascii=False,allow_nan=False),natural_key))
        else:
            execute(db,f"INSERT INTO {table} (id,natural_key,payload) VALUES (?,?,?)",(obj["id"],natural_key,json.dumps(obj,ensure_ascii=False,allow_nan=False)))
    return obj
