"""Display helpers for opening deduct figures shown in editors.

扣除口径必须与估漆回包一致：内口 (w-2m)×(h-2m)，由 wall_area.inner_opening
统一计算；合计同样先累加精确内口积再取整。留边 0 时内口等于洞口。
不再提供毛洞 (w*h) 展示口径。
"""

from app.engines.wall_area import InvalidOpening, inner_opening, round_detail


def _inner_item(o):
    try:
        d = inner_opening(
            o.get("w", 0), o.get("h", 0), o.get("margin", 0.0),
            o.get("id"), o.get("kind"),
        )
    except InvalidOpening:
        # 与估算同一规则：内口非法时不给扣除值（估算会整单拒绝）。
        return {
            **dict(o),
            "inner_w": None, "inner_h": None,
            "deduct_m2": None, "_raw_deduct": None, "valid": False,
        }
    rd = round_detail(d)
    return {**dict(o), "inner_w": rd["inner_w"], "inner_h": rd["inner_h"],
            "deduct_m2": rd["deduct_m2"], "_raw_deduct": d["deduct_m2"],
            "valid": True}


def annotate_openings(openings):
    """逐洞补内口尺寸与本洞扣除（内口口径，取整同估漆回包）。"""
    ops = [_inner_item(o) for o in (openings or [])]
    for o in ops:
        o.pop("_raw_deduct", None)
    return ops


def detail_with_inner(detail):
    if not detail:
        return detail
    ops = [_inner_item(o) for o in (detail.get("openings") or [])]
    # 先累加精确内口积再取整，与 wall_area 的 openings_m2 完全一致
    total = round(sum(o["_raw_deduct"] for o in ops if o["_raw_deduct"] is not None), 2)
    for o in ops:
        o.pop("_raw_deduct", None)
    return {**detail, "openings": ops, "openings_m2": total}
