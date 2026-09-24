"""详情/门窗列表的洞口扣除展示。

与估漆引擎同一套内口径：每洞扣除 = (w − 2·margin) × (h − 2·margin)，
不再使用洞口毛宽高积 w×h，避免「详情扣除」与「估漆回包扣除」对不上。

内口非法（留边为负或内口宽/高 <= 0）时不抛错：详情仍要能打开并编辑留边，
此时不给该洞扣除并标记 invalid；估算侧仍会按规则整单拒绝、不落记录。
"""
from app.engines.wall_area import InvalidOpening, inner_opening


def _annotate_one(o: dict) -> dict:
    item = dict(o)
    w = float(item.get("w") or 0.0)
    h = float(item.get("h") or 0.0)
    margin = float(item.get("margin") or 0.0)
    item["inner_w"] = round(w - 2.0 * margin, 3)
    item["inner_h"] = round(h - 2.0 * margin, 3)
    try:
        d = inner_opening(w, h, margin, item.get("id"), item.get("kind"))
        item["deduct_m2"] = round(d["deduct_m2"], 2)
        item["invalid"] = False
    except InvalidOpening:
        item["deduct_m2"] = None
        item["invalid"] = True
    return item


def annotate_openings(openings):
    return [_annotate_one(o) for o in (openings or [])]


def sum_inner(openings):
    # 与 wall_area 完全同一套：各洞先按精确内口积相加，最后再取整；
    # 非法洞不贡献扣除（估算侧本就会整单拒绝）。
    total = 0.0
    for o in openings or []:
        try:
            d = inner_opening(o.get("w", 0), o.get("h", 0), o.get("margin", 0.0),
                              o.get("id"), o.get("kind"))
        except InvalidOpening:
            continue
        total += d["deduct_m2"]
    return round(total, 2)


def detail_with_inner(detail):
    if not detail:
        return detail
    ops = annotate_openings(detail.get("openings") or [])
    return {**detail, "openings": ops, "openings_m2": sum_inner(ops)}
