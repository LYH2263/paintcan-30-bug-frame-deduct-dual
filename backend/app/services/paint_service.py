from app.db import connect
from app.engines.estimate import estimate_room
from app.engines.wall_area import inner_opening
from app.repositories import openings, rooms, runs, settings


class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

    def list_rooms(self): return rooms.list_all(self._c)

    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        from app.services.opening_display import detail_with_gross
        return detail_with_gross({"room": r, "openings": openings.for_room(self._c, rid)})

    def settings(self): return settings.get_map(self._c)

    def history(self, limit=50):
        # 记录里已含钉选时的输入留边与结果净面积，不随后续改动变化
        return runs.list_recent(self._c, limit)

    def estimate(self, room_id, persist, coats=None, coverage=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        # 测量当下各洞留边快照
        ops = [{
            "id": o["id"], "kind": o["kind"], "w": float(o["w"]), "h": float(o["h"]),
            "margin": float(o.get("margin") or 0.0),
        } for o in detail["openings"]]
        # 任一洞内口 <= 0 会在此抛 InvalidOpening，发生在落库之前 → 整单拒绝、不写记录
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        payload = {
            "room_id": room_id, "coats": ct, "coverage": cov,
            "openings": [{"id": x["id"], "kind": x["kind"], "w": x["w"], "h": x["h"], "margin": x["margin"]} for x in ops],
        }
        rid = runs.insert(self._c, "estimate", payload, result, room_id) if persist else None
        return {"run_id": rid, "room_id": room_id, **result}

    def update_opening_margin(self, opening_id, margin):
        o = openings.get(self._c, opening_id)
        if not o: return None
        # 与估算同一套内口规则：内口宽或高 <= 0（或留边为负）即拒绝，不写库
        inner_opening(o["w"], o["h"], margin, o["id"], o["kind"])
        openings.update_margin(self._c, opening_id, margin)
        return openings.get(self._c, opening_id)

    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
