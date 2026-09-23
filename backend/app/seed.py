import json
from app.db import connect
from app.engines.estimate import estimate_room

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY, name TEXT, length REAL, width REAL, height REAL);
CREATE TABLE IF NOT EXISTS openings(id INTEGER PRIMARY KEY, room_id INTEGER, kind TEXT, w REAL, h REAL, margin REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS calc_runs(id INTEGER PRIMARY KEY, kind TEXT, room_id INTEGER, input_json TEXT, result_json TEXT, created_at TEXT);
"""

# 既有库（无 margin 列）平滑加列；新库建表已带 margin。
_MIGRATIONS = {
    "openings": [("margin", "REAL NOT NULL DEFAULT 0")],
}


def _migrate(conn):
    for table, cols in _MIGRATIONS.items():
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, decl in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    conn.commit()


def init_db():
    conn = connect()
    conn.executescript(_SCHEMA)
    _migrate(conn)
    if conn.execute("SELECT COUNT(*) c FROM rooms").fetchone()["c"] == 0:
        conn.execute("INSERT INTO rooms(name,length,width,height) VALUES ('客厅',5.0,4.0,2.8)")
        conn.execute("INSERT INTO rooms(name,length,width,height) VALUES ('卧室(多种洞)',4.0,3.2,2.8)")
        conn.execute("INSERT INTO openings(room_id,kind,w,h,margin) VALUES (1,'door',0.9,2.1,0)")
        conn.execute("INSERT INTO openings(room_id,kind,w,h,margin) VALUES (1,'window',1.5,1.4,0)")
        conn.execute("INSERT INTO openings(room_id,kind,w,h,margin) VALUES (2,'door',0.9,2.1,0)")
        conn.execute("INSERT INTO openings(room_id,kind,w,h,margin) VALUES (2,'window',1.8,1.5,0)")
        conn.execute("INSERT INTO openings(room_id,kind,w,h,margin) VALUES (2,'window',1.2,1.5,0)")
        conn.execute("INSERT INTO settings(key,value) VALUES ('coverage','8')")
        conn.execute("INSERT INTO settings(key,value) VALUES ('coats','2')")
        seed_openings = [
            {"id": 1, "kind": "door", "w": 0.9, "h": 2.1, "margin": 0.0},
            {"id": 2, "kind": "window", "w": 1.5, "h": 1.4, "margin": 0.0},
        ]
        est = estimate_room(5, 4, 2.8, seed_openings, 8, 2)
        conn.execute("INSERT INTO calc_runs(kind,room_id,input_json,result_json,created_at) VALUES ('estimate',1,?,?,datetime('now'))",
            (json.dumps({"room_id": 1, "coats": 2, "coverage": 8, "openings": seed_openings}), json.dumps(est)))
        conn.commit()
    conn.close()
