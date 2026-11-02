from crawler.promote import (
    Candidate,
    ExistingOffer,
    anomaly_baseline,
    count,
    detect_anomaly,
    plan,
)


def cand(ext="1", price=10000, sold_out=False, name="아디다스 글러브") -> Candidate:
    return Candidate(
        external_id=ext,
        name=name,
        brand="Adidas",
        category_slug="gloves",
        image_url="https://x/i.jpg",
        product_url="https://x/p",
        price=price,
        sold_out=sold_out,
    )


def old(price=10000, fee=0, in_stock=True, product_id=100, oid=1) -> ExistingOffer:
    return ExistingOffer(id=oid, product_id=product_id, price=price, shipping_fee=fee,
                         in_stock=in_stock)


def one(candidate, existing=None, shared=None, fee=0):
    actions = plan([candidate], existing or {}, shared or set(), fee)
    assert len(actions) == 1
    return actions[0]


def test_new_offer_gets_first_history():
    a = one(cand())
    assert a.kind == "NEW" and a.existing is None
    assert a.add_history is True
    assert a.stock_change == "none"
    assert a.in_stock is True
    assert a.sync_product is False


def test_same_price_recrawl_has_no_history():
    a = one(cand(price=10000), {"1": old(price=10000)})
    assert a.kind == "UPDATE"
    assert (a.add_history, a.price_changed, a.stock_change) == (False, False, "none")


def test_price_change_adds_history():
    a = one(cand(price=9000), {"1": old(price=10000)})
    assert (a.add_history, a.price_changed) == (True, True)


def test_shipping_fee_change_adds_history():
    a = one(cand(price=10000), {"1": old(price=10000, fee=0)}, fee=3000)
    assert (a.add_history, a.price_changed) == (True, True)
    assert a.shipping_fee == 3000


def test_stock_change_only_has_no_history_but_flags_transition():
    a = one(cand(sold_out=True), {"1": old(in_stock=True)})
    assert a.in_stock is False
    assert (a.add_history, a.price_changed, a.stock_change) == (False, False, "to_out")


def test_restock():
    a = one(cand(sold_out=False), {"1": old(in_stock=False)})
    assert a.stock_change == "to_in" and a.add_history is False


def test_price_and_stock_change_together():
    a = one(cand(price=8000, sold_out=True), {"1": old(price=10000, in_stock=True)})
    assert (a.add_history, a.stock_change) == (True, "to_out")


def test_product_sync_forbidden_when_other_seller_has_offer():
    a = one(cand(), {"1": old(product_id=100)}, shared={100})
    assert a.sync_product is False


def test_product_sync_allowed_when_only_this_seller():
    a = one(cand(), {"1": old(product_id=100)}, shared={999})
    assert a.sync_product is True


def test_sold_out_candidate_is_not_in_stock_even_when_new():
    a = one(cand(sold_out=True))
    assert a.kind == "NEW" and a.in_stock is False


def test_duplicate_external_id_processed_once():
    actions = plan([cand("1", 10000), cand("1", 5000), cand("2")], {}, set(), 0)
    assert [a.candidate.external_id for a in actions] == ["1", "2"]
    assert actions[0].candidate.price == 10000


def test_counts():
    actions = plan(
        [cand("1"), cand("2", price=9000), cand("3", sold_out=True), cand("4"), cand("5")],
        {
            "2": old(price=10000, oid=2),
            "3": old(oid=3, in_stock=True),
            "4": old(oid=4, in_stock=False),
            "5": old(oid=5),
        },
        set(),
        0,
    )
    c = count(actions)
    assert (c.new, c.updated) == (1, 4)
    assert (c.history_added, c.price_changed) == (2, 1)
    assert (c.to_out, c.to_in) == (1, 1)


def test_anomaly_request_errors():
    assert detect_anomaly(1, 100, 0, 100, None, False) is not None


def test_anomaly_parse_failure_ratio():
    assert detect_anomaly(0, 90, 10, 90, None, False) is None  # 정확히 10%는 통과
    assert detect_anomaly(0, 89, 11, 89, None, False) is not None


def test_anomaly_items_drop_below_half_of_previous():
    assert detect_anomaly(0, 49, 0, 49, 100, False) is not None
    assert detect_anomaly(0, 50, 0, 50, 100, False) is None
    assert detect_anomaly(0, 10, 0, 10, None, False) is None  # 이전 SUCCESS 없음


def test_partial_mode_skips_only_the_ratio_check():
    assert detect_anomaly(0, 10, 0, 10, 100, True) is None
    assert detect_anomaly(1, 10, 0, 10, 100, True) is not None
    assert detect_anomaly(0, 80, 20, 80, 100, True) is not None


def test_anomaly_nothing_collected():
    assert detect_anomaly(0, 0, 0, 0, None, False) is not None


# --- 수집 이상 기준값: 최근 SUCCESS 최대 5건의 최댓값 ---


def test_baseline_uses_max_of_recent_runs():
    assert anomaly_baseline([300, 5000, 4800, 10, 4900]) == 5000


def test_baseline_not_lowered_by_small_partial_runs():
    full_only = anomaly_baseline([5000, 4900])
    with_partials = anomaly_baseline([10, 20, 5000, 4900, 15])
    assert full_only == with_partials == 5000
    # 부분 수집 값이 섞여도 전체 수집이 크게 줄면 이상으로 잡힌다
    assert detect_anomaly(0, 2000, 0, 2000, with_partials, False) is not None


def test_baseline_none_without_history_skips_check():
    assert anomaly_baseline([]) is None
    assert detect_anomaly(0, 10, 0, 10, anomaly_baseline([]), False) is None


def test_exactly_half_of_baseline_passes_and_below_fails():
    baseline = anomaly_baseline([100, 80])
    assert detect_anomaly(0, 50, 0, 50, baseline, False) is None
    assert detect_anomaly(0, 49, 0, 49, baseline, False) is not None


def test_partial_mode_skips_baseline_check_with_history():
    baseline = anomaly_baseline([5000, 4900])
    assert detect_anomaly(0, 10, 0, 10, baseline, True) is None
