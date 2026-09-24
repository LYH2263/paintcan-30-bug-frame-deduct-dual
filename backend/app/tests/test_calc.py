import pytest
from app.engines.estimate import estimate_room
from app.engines.paint_volume import paint_liters
from app.engines.wall_area import InvalidOpening, wall_area, inner_opening

DOOR = {"id": 1, "kind": "door", "w": 0.9, "h": 2.1}
WINDOW = {"id": 2, "kind": "window", "w": 1.5, "h": 1.4}


def test_living_room_net():
    a = wall_area(5, 4, 2.8, [DOOR, WINDOW])
    assert a["gross_m2"] == 50.4
    assert a["net_m2"] == 46.41


def test_liters_two_coats():
    v = paint_liters(46.41, 8, 2)
    assert v["liters"] == 11.6


def test_estimate_combined():
    e = estimate_room(5, 4, 2.8, [DOOR, WINDOW], 8, 2)
    assert e["liters"] == 11.6


def test_bad_coverage():
    with pytest.raises(ValueError):
        paint_liters(10, 0, 2)


# ---------- 门窗框留边 ----------

def test_margin_zero_matches_legacy():
    """留边缺省/为 0：净面积与改造前同房同洞一致，且带逐洞明细。"""
    legacy_hole = 0.9 * 2.1 + 1.5 * 1.4
    legacy_net = round(max(0.0, 50.4 - legacy_hole), 2)
    a = wall_area(5, 4, 2.8, [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}])
    assert a["openings_m2"] == round(legacy_hole, 2)
    assert a["net_m2"] == legacy_net == 46.41
    assert a["openings"][0]["margin"] == 0
    assert a["openings"][0]["inner_w"] == 0.9 and a["openings"][0]["inner_h"] == 2.1


def test_deduction_uses_inner_opening():
    """两侧各减留边：door margin .05 → 内口 .8×2.0=1.6；扣除合计与净面积随之变。"""
    d = inner_opening(0.9, 2.1, 0.05, 1, "door")
    assert (d["inner_w"], d["inner_h"], d["deduct_m2"]) == (0.8, 2.0, 1.6)
    a = wall_area(5, 4, 2.8, [{**DOOR, "margin": 0.05}, WINDOW])
    assert a["openings_m2"] == 3.7          # 1.6 + 2.1
    assert a["net_m2"] == 46.7
    e = estimate_room(5, 4, 2.8, [{**DOOR, "margin": 0.05}, WINDOW], 8, 2)
    assert e["liters"] == 11.68
    assert e["openings"][0]["deduct_m2"] == 1.6


def test_inner_width_not_positive_rejected():
    # 2*margin == w（内口宽 0）以及 > w（内口宽为负）都须拒绝
    for m in (0.45, 0.5):
        with pytest.raises(InvalidOpening):
            wall_area(5, 4, 2.8, [{**DOOR, "margin": m}])


def test_inner_height_not_positive_rejected():
    # 内口高不大于 0 同样拒绝（即使内口宽仍为正）
    with pytest.raises(InvalidOpening):
        inner_opening(2.0, 1.0, 0.5)        # inner 1.0×0.0
    with pytest.raises(InvalidOpening):
        inner_opening(2.0, 1.0, 0.6)        # inner 0.8×-0.2


def test_negative_margin_rejected():
    with pytest.raises(InvalidOpening):
        inner_opening(0.9, 2.1, -0.01, 1)


# ---------- 钉选 / 历史不可变 / 拒绝不落库（服务层，临时库） ----------

@pytest.fixture()
def svc(tmp_path, monkeypatch):
    from app import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    from app import seed
    seed.init_db()
    from app.services.paint_service import PaintService
    with PaintService() as s:
        yield s


def _count(s):
    return len(s.history(1000))


def test_persist_false_only_returns(svc):
    before = _count(svc)
    r = svc.estimate(1, False)
    assert r["run_id"] is None
    assert r["net_m2"] == 46.41 and r["openings_m2"] == 3.99
    assert _count(svc) == before          # 不写记录


def test_persist_pins_snapshot_and_history_immutable(svc):
    run_a = svc.estimate(1, True)
    assert run_a["run_id"] is not None
    pinned_a = next(h for h in svc.history(1000) if h["id"] == run_a["run_id"])
    assert pinned_a["result"]["net_m2"] == 46.41
    assert pinned_a["result"]["openings"][0]["margin"] == 0
    assert pinned_a["result"]["openings"][0]["deduct_m2"] == 1.89

    # 事后改某洞留边，当场再测用新留边
    assert svc.update_opening_margin(1, 0.05)["margin"] == 0.05
    run_b = svc.estimate(1, True)
    assert run_b["net_m2"] == 46.7 and run_b["openings"][0]["deduct_m2"] == 1.6

    # 旧估算记录净面积不得跟着变
    old_a = next(h for h in svc.history(1000) if h["id"] == run_a["run_id"])
    assert old_a["result"]["net_m2"] == 46.41
    assert old_a["result"]["openings"][0]["margin"] == 0


def test_invalid_estimate_rejected_without_record(svc):
    # 直接把某洞留边改成使内口 <= 0 的值
    from app.db import connect
    c = connect(); c.execute("UPDATE openings SET margin=0.5 WHERE id=1"); c.commit(); c.close()
    n = _count(svc)
    with pytest.raises(InvalidOpening):
        svc.estimate(1, True)
    assert _count(svc) == n               # 整单拒绝、不写记录


def test_invalid_margin_update_rejected(svc):
    with pytest.raises(InvalidOpening):
        svc.update_opening_margin(1, 0.45)   # 内口宽 0
    assert svc.room_detail(1)["openings"][0]["margin"] == 0.0


def test_detail_deduction_matches_estimate_inner(svc):
    """改留边后：房间详情/门窗列表的逐洞扣除与合计，必须与估漆回包同一套内口径。"""
    assert svc.update_opening_margin(1, 0.05)["margin"] == 0.05
    detail = svc.room_detail(1)
    est = svc.estimate(1, False)

    # 逐洞：详情内口/扣除 == 估漆回包（1 号门内口 .8×2.0=1.6）
    d1 = next(o for o in detail["openings"] if o["id"] == 1)
    e1 = next(o for o in est["openings"] if o["id"] == 1)
    assert d1["inner_w"] == 0.8 and d1["inner_h"] == 2.0
    assert d1["deduct_m2"] == e1["deduct_m2"] == 1.6
    assert d1["invalid"] is False

    # 合计：详情 openings_m2 与估漆扣除合计一致（1.6 + 2.1 = 3.7），不再是毛洞 3.99
    assert detail["openings_m2"] == est["openings_m2"] == 3.7
    assert "gross_openings_m2" not in detail
    assert all("gross_deduct" not in o for o in detail["openings"])


def test_detail_invalid_opening_marked_without_raising(svc):
    """库里存在内口 <=0 的洞（绕过服务层写入）：详情仍可打开，该洞标 invalid、无扣除，
    合法洞仍按内口给扣除；估算侧依旧整单拒绝。"""
    from app.db import connect
    c = connect(); c.execute("UPDATE openings SET margin=0.5 WHERE id=1"); c.commit(); c.close()

    detail = svc.room_detail(1)
    bad = next(o for o in detail["openings"] if o["id"] == 1)
    good = next(o for o in detail["openings"] if o["id"] == 2)
    assert bad["invalid"] is True and bad["deduct_m2"] is None
    assert good["invalid"] is False and good["deduct_m2"] == 2.1
    # 合计只含合法内口洞
    assert detail["openings_m2"] == 2.1

    with pytest.raises(InvalidOpening):
        svc.estimate(1, True)


def test_pinned_history_differs_from_live_detail_after_margin_change(svc):
    """历史按编号打开：钉选净面积固化；改留边后详情现场扣除变内口新值，
    旧记录仍为钉选时口径，不被带跑。"""
    pinned = svc.estimate(1, True)
    assert pinned["net_m2"] == 46.41 and pinned["openings_m2"] == 3.99

    svc.update_opening_margin(1, 0.05)
    detail = svc.room_detail(1)
    assert detail["openings_m2"] == 3.7                 # 现场：内口径新值

    old = next(h for h in svc.history(1000) if h["id"] == pinned["run_id"])
    assert old["result"]["net_m2"] == 46.41             # 钉选不被带跑
    assert old["result"]["openings_m2"] == 3.99
    assert old["result"]["openings"][0]["deduct_m2"] == 1.89
