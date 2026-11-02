import pytest

from crawler import cli, db, rules
from crawler.classify import classify, dedupe
from crawler.pipeline import RAW_ONLY_REASON, _raw_rows, raw_row_status, shipping_fee_from_env
from crawler.promote import plan


def _classified(name, brand_text, category_no=2990):
    return classify({
        "shop": "boxingmall", "shop_product_no": "1", "name": name,
        "category_no": category_no, "brand_text": brand_text,
    })


def test_cli_rejects_raw_only_with_dry_run():
    with pytest.raises(SystemExit) as e:
        cli.main(["--shop", "boxingmall", "--dry-run", "--raw-only"])
    assert e.value.code == 2


def test_cli_rejects_raw_only_without_save():
    with pytest.raises(SystemExit) as e:
        cli.main(["--shop", "boxingmall", "--raw-only"])
    assert e.value.code == 2


def test_raw_only_status_for_promotable():
    c = _classified("리복 베이직 복싱글러브(RSCB-12010BK) 블랙", "리복")
    assert raw_row_status(c, raw_only=True) == ("UNMATCHED", None, RAW_ONLY_REASON)
    assert RAW_ONLY_REASON == "not_promoted_raw_only"
    assert raw_row_status(c, raw_only=False) == ("AUTO", 100.00, None)


def test_raw_only_status_keeps_unmatched_reason():
    c = _classified("월드복싱 복싱글러브", "기타")
    assert raw_row_status(c, raw_only=True) == ("UNMATCHED", None, "unknown_brand")


def test_raw_rows_raw_only_all_unmatched():
    d = {"shop_product_no": "1", "name": "리복 복싱글러브", "price": 1000, "product_url": "u",
         "brand_text": "리복", "category_no": 2990, "shop": "boxingmall"}
    rows = _raw_rows(1, [(d, classify(d))], 0, raw_only=True)
    assert [r[7:] for r in rows] == [("UNMATCHED", None, RAW_ONLY_REASON)]


def test_plan_is_empty_without_candidates():
    # raw-only는 승격 후보를 비워 plan이 비고, 따라서 product/offer/price_history 쓰기가 없다
    assert plan([], {}, set(), 0) == []


def test_lock_key_differs_per_seller():
    assert db.lock_key(1) != db.lock_key(2)
    assert db.lock_key(1) == db.ADVISORY_LOCK_KEY + 1


def test_shipping_fee_env_name(monkeypatch):
    monkeypatch.setenv("BOXINGMALL_SHIPPING_FEE", "3000")
    monkeypatch.delenv("GOLDENCHAMPS_SHIPPING_FEE", raising=False)
    assert shipping_fee_from_env("BOXINGMALL_SHIPPING_FEE") == 3000
    assert shipping_fee_from_env("GOLDENCHAMPS_SHIPPING_FEE") == 0
    monkeypatch.setenv("BOXINGMALL_SHIPPING_FEE", "-1")
    with pytest.raises(db.ConfigError):
        shipping_fee_from_env("BOXINGMALL_SHIPPING_FEE")


def test_dedupe_uses_each_shops_fallback():
    gc = [{"shop": "goldenchamps", "shop_product_no": "1", "category_no": 28},
          {"shop": "goldenchamps", "shop_product_no": "1", "category_no": 24}]
    assert dedupe(gc)[0]["category_no"] == 24
    bm = [{"shop": "boxingmall", "shop_product_no": "1", "category_no": 9999},
          {"shop": "boxingmall", "shop_product_no": "1", "category_no": 2990}]
    assert dedupe(bm)[0]["category_no"] == 2990
    # 몰이 다르면 같은 번호여도 다른 상품
    assert len(dedupe([{"shop": "boxingmall", "shop_product_no": "1"},
                       {"shop": "goldenchamps", "shop_product_no": "1"}])) == 2


def test_fallback_tables_per_shop():
    assert set(rules.SHOP_CATEGORY_FALLBACK) == {"goldenchamps", "boxingmall"}
