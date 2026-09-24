"""门窗框留边：洞口尺寸 w×h，两侧各留 margin，扣除按内口 (w-2m)×(h-2m) 计算。

留边缺省 0 时内口等于洞口，净面积与改造前一致。
内口宽或高不大于 0（或留边为负）时抛 InvalidOpening，由上层整单拒绝且不落记录。
"""


class InvalidOpening(ValueError):
    """内口宽或高不大于 0（或留边为负），无法成洞。"""


def inner_opening(w, h, margin=0.0, opening_id=None, kind=None) -> dict:
    """单洞：洞口减两侧留边得内口。返回精确内口尺寸与该洞扣除面积（未取整）。"""
    w = float(w)
    h = float(h)
    margin = float(margin or 0.0)
    tag = opening_id if opening_id is not None else "?"
    if margin < 0:
        raise InvalidOpening(f"洞口 {tag} 留边不可为负")
    inner_w = w - 2.0 * margin
    inner_h = h - 2.0 * margin
    if inner_w <= 0 or inner_h <= 0:
        raise InvalidOpening(
            f"洞口 {tag} 内口 {round(inner_w, 3)}×{round(inner_h, 3)} 不大于 0"
        )
    return {
        "id": opening_id,
        "kind": kind,
        "w": w,
        "h": h,
        "margin": margin,
        "inner_w": inner_w,
        "inner_h": inner_h,
        "deduct_m2": inner_w * inner_h,
    }


def round_detail(d: dict) -> dict:
    """渲染用：尺寸 3 位、面积 2 位取整。"""
    return {
        "id": d["id"],
        "kind": d["kind"],
        "w": round(d["w"], 3),
        "h": round(d["h"], 3),
        "margin": round(d["margin"], 3),
        "inner_w": round(d["inner_w"], 3),
        "inner_h": round(d["inner_h"], 3),
        "deduct_m2": round(d["deduct_m2"], 2),
    }


def wall_area(length: float, width: float, height: float, openings: list[dict]) -> dict:
    walls = 2 * (float(length) + float(width)) * float(height)
    raw = [
        inner_opening(o["w"], o["h"], o.get("margin", 0.0), o.get("id"), o.get("kind"))
        for o in openings
    ]
    hole = sum(d["deduct_m2"] for d in raw)  # 精确内口积；留边 0 时与改造前单次取整一致
    net = max(0.0, walls - hole)
    return {
        "gross_m2": round(walls, 2),
        "openings_m2": round(hole, 2),
        "net_m2": round(net, 2),
        "openings": [round_detail(d) for d in raw],
    }
