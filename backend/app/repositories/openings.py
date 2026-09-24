import sqlite3


def for_room(conn, room_id):
    return [dict(r) for r in conn.execute(
        "SELECT * FROM openings WHERE room_id=? ORDER BY id", (room_id,)).fetchall()]


def get(conn, opening_id):
    row = conn.execute("SELECT * FROM openings WHERE id=?", (opening_id,)).fetchone()
    return dict(row) if row else None


def update_margin(conn, opening_id, margin):
    cur = conn.execute("UPDATE openings SET margin=? WHERE id=?", (float(margin), opening_id))
    conn.commit()
    return cur.rowcount
