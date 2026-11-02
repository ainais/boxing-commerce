from datetime import UTC, datetime
from pathlib import Path

import pytest

from crawler.http import Fetcher, ForbiddenUrlError
from crawler.shops.goldenchamps import GoldenChampsAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "goldenchamps_list.html"
NOW = datetime(2026, 11, 2, tzinfo=UTC)


@pytest.fixture
def adapter() -> GoldenChampsAdapter:
    return GoldenChampsAdapter()


@pytest.fixture
def page(adapter):
    return adapter.parse_list(FIXTURE.read_text(encoding="utf-8"), 24, now=NOW)


def test_parses_all_blocks(page):
    assert [p.shop_product_no for p in page.products] == ["1257", "1256", "1255", "9999"]
    assert page.failed == 0


def test_first_product_fields(page):
    p = page.products[0]
    assert p.shop == "goldenchamps"
    assert p.name == "라이벌 Rival 에어로 스파링글러브 RS4V 블랙"  # "상품명 :" 라벨 제외
    assert p.price == 132000
    assert p.list_price == 132000
    assert isinstance(p.price, int)
    assert p.model_summary == "Rival Aero Sparring Gloves RS4V / Red"
    assert p.category_no == 24
    assert p.scraped_at == NOW
    assert p.sold_out is False


def test_urls_are_absolute_https(page):
    for p in page.products:
        assert p.image_url.startswith("https://goldenchamps.co.kr/web/product/medium/")
        assert p.product_url.startswith("https://goldenchamps.co.kr/product/")
    assert page.products[0].product_url.endswith("/1257/category/24/display/1/")


def test_prices_not_taken_from_hidden_discount_elements(page):
    # 모든 상품에서 가격이 spec 라벨 기준 정수로 나와야 한다
    assert all(isinstance(p.price, int) and p.price > 0 for p in page.products)
    assert all(p.list_price is None or isinstance(p.list_price, int) for p in page.products)


def test_sold_out_detected_only_on_synthetic_block(page):
    assert [p.sold_out for p in page.products] == [False, False, False, True]


def test_last_page_from_last_link(page):
    assert page.last_page == 2


def test_last_page_from_numbers_when_no_last_link(adapter):
    html = (
        '<div class="ec-base-paginate"><ol>'
        '<li><a href="?cate_no=24&page=1">1</a></li>'
        '<li><a href="?cate_no=24&page=3">3</a></li>'
        "</ol></div>"
    )
    assert adapter.parse_list(html, 24).last_page == 3


def test_last_page_without_pagination(adapter):
    assert adapter.parse_list("<html></html>", 24).last_page == 1


def _block(no: str, name: str | None, price: str | None) -> str:
    name_html = f'<a href="/p/{no}"><span>{name}</span></a>' if name else ""
    price_html = (
        '<li><strong class="title displaynone"><span>판매가</span> :</strong>'
        f"<span>{price}</span></li>"
        if price
        else ""
    )
    return (
        f'<li id="anchorBoxId_{no}"><div class="prdImg">'
        f'<a href="/p/{no}" name="anchorBoxName_{no}"><img src="//x.kr/{no}.jpg" alt=""/></a></div>'
        f'<div class="description"><strong class="name">{name_html}</strong>'
        f'<ul class="spec">{price_html}</ul></div></li>'
    )


def test_skips_blocks_missing_required_values(adapter):
    html = (
        '<ul class="prdList">'
        + _block("1", "정상 상품", "10,000원")
        + _block("2", "가격 없음", None)
        + _block("3", None, "5,000원")
        + "</ul>"
    )
    page = adapter.parse_list(html, 24)
    assert [p.shop_product_no for p in page.products] == ["1"]
    assert page.failed == 2


def test_non_numeric_block_id_and_comments_are_ignored(adapter):
    html = (
        '<ul class="prdList"><!-- <li id="anchorBoxId_5">template</li> -->'
        '<li id="anchorBoxId_$product_no">template</li></ul>'
    )
    page = adapter.parse_list(html, 24)
    assert page.products == []
    assert page.failed == 0


def test_name_falls_back_to_img_alt(adapter):
    html = _block("7", None, "1,000원").replace('alt=""', 'alt="대체 이름"')
    page = adapter.parse_list(f'<ul class="prdList">{html}</ul>', 24)
    assert page.products[0].name == "대체 이름"


def test_list_url(adapter):
    assert adapter.list_url(24, 2) == (
        "https://goldenchamps.co.kr/product/list.html?cate_no=24&page=2"
    )


def test_fetcher_rejects_paths_outside_product_list(adapter):
    fetcher = Fetcher(adapter.allowed_paths)
    for url in (
        "https://goldenchamps.co.kr/admin/x",
        "https://goldenchamps.co.kr/exec/front/Product/List",
        "https://goldenchamps.co.kr/member/login.html",
    ):
        with pytest.raises(ForbiddenUrlError):
            fetcher.get_text(url)
    fetcher.close()
