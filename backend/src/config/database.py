import json, sqlite3
from contextlib import contextmanager
from urllib.parse import urlparse, unquote
from src.config.settings import DATABASE_URL
TABLES = ("users", "datasets", "models", "runs", "plans", "reports", "audit", "occupancies")
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
@contextmanager
def transaction():
    """单连接事务：同一事务内完成校验与占用写入，保证并发审批只有一份成功。"""
    if DATABASE_URL.startswith("sqlite:///"):
        db = sqlite3.connect(DATABASE_URL[10:], timeout=30)
        db.isolation_level = None
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise
        finally:
            db.close()
    else:
        import pymysql
        u = urlparse(DATABASE_URL)
        db = pymysql.connect(host=u.hostname, port=u.port or 3306, user=unquote(u.username), password=unquote(u.password), database=u.path[1:], charset="utf8mb4", connect_timeout=5)
        try:
            db.begin()
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

def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, allow_nan=False)

def tx_get(db, table, key):
    row = execute(db, f"SELECT payload FROM {table} WHERE id=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None

def tx_all_rows(db, table):
    rows = execute(db, f"SELECT payload FROM {table} ORDER BY natural_key").fetchall()
    return [json.loads(r[0]) for r in rows]

def tx_insert(db, table, obj, natural_key=None):
    """事务内插入；natural_key 唯一冲突时抛出 IntegrityError，由调用方判定。"""
    natural_key = natural_key or obj["id"]
    execute(db, f"INSERT INTO {table} (id,natural_key,payload) VALUES (?,?,?)",
            (obj["id"], natural_key, dumps(obj)))

def tx_update(db, table, obj, natural_key=None):
    natural_key = natural_key or obj["id"]
    execute(db, f"UPDATE {table} SET payload=? WHERE natural_key=?", (dumps(obj), natural_key))

def integrity_error():
    if DATABASE_URL.startswith("sqlite:///"):
        return sqlite3.IntegrityError
    from pymysql import IntegrityError
    return IntegrityError
