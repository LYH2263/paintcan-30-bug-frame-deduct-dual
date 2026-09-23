import json
from datetime import datetime, timezone


def insert(conn, kind, payload, result, room_id=None):
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute("INSERT INTO calc_runs(kind,room_id,input_json,result_json,created_at) VALUES (?,?,?,?,?)",
        (kind, room_id, json.dumps(payload, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now))
    conn.commit()
    return int(cur.lastrowid)


def list_recent(conn, limit=50):
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM calc_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    # 历史打开带回钉选时的输入（各洞留边）与结果（净面积/扣除/升数），
    # 不随后续洞口留边改动而变化。
    for r in rows:
        r["input"] = json.loads(r.pop("input_json") or "{}")
        r["result"] = json.loads(r.pop("result_json") or "{}")
    return rows
