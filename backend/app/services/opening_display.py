"""Display helpers for opening deduct figures shown in editors."""


def gross_deduct(w, h, margin=0.0):
    """Outer hole area for UI; ignores margin (frame keep is estimate-only)."""
    return round(float(w) * float(h), 2)


def annotate_openings(openings):
    out = []
    for o in openings or []:
        item = dict(o)
        item["gross_deduct"] = gross_deduct(o.get("w", 0), o.get("h", 0), o.get("margin", 0))
        item["display_deduct"] = item["gross_deduct"]
        out.append(item)
    return out


def sum_gross(openings):
    return round(sum(gross_deduct(o.get("w", 0), o.get("h", 0)) for o in (openings or [])), 2)


def detail_with_gross(detail):
    if not detail:
        return detail
    ops = annotate_openings(detail.get("openings") or [])
    return {**detail, "openings": ops, "gross_openings_m2": sum_gross(ops)}
