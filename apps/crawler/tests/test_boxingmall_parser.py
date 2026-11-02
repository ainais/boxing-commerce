import ssl
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from crawler import http
from crawler.classify import PROMOTABLE, UNMATCHED, classify
from crawler.crawl import PageGuardError, format_unknown_images, iter_pages
from crawler.http import Fetcher, ForbiddenUrlError, MissingCertificateError
from crawler.shops.boxingmall import BoxingMallAdapter
from crawler.shops.goldenchamps import GoldenChampsAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "boxingmall_list.html"
NOW = datetime(2026, 11, 2, tzinfo=UTC)


@pytest.fixture
def adapter() -> BoxingMallAdapter:
    return BoxingMallAdapter()


@pytest.fixture
def html() -> str:
    # 픽스처는 cp949 바이트다. Fetcher와 같은 방식으로 디코딩한다
    return FIXTURE.read_bytes().decode("cp949", errors="replace")


@pytest.fixture
def page(adapter, html):
    return adapter.parse_list(html, 2990, now=NOW)


def by_uid(page):
    return {p.shop_product_no: p for p in page.products}


def test_fixture_is_cp949_not_utf8():
    data = FIXTURE.read_bytes()
    with pytest.raises(UnicodeDecodeError):
        data.decode("utf-8")
    assert "복싱글러브" in data.decode("cp949")


def test_unique_products_banner_excluded_and_duplicate_once(page):
    # 139253이 두 번 나오지만 한 번만, 배너 uid(94697, 125131)는 상품이 아니다
    assert [p.shop_product_no for p in page.products] == [
        "139253", "112709", "126492", "900001", "900002",
    ]
    assert page.failed == 1  # 900003: 판매가 없음


def test_first_product_fields(page):
    p = by_uid(page)["139253"]
    assert p.shop == "boxingmall"
    assert p.name == "탑텐 월드복싱 WB공인 복싱글러브_ 블루"
    assert p.brand_text == "탑텐"
    assert p.price == 220000
    assert p.list_price == 242000
    assert isinstance(p.price, int) and isinstance(p.list_price, int)
    assert p.image_url == (
        "https://www.boxingmall.co.kr/product_images/normal/2026/20260818155727205929normal.jpg"
    )
    assert p.product_url == "https://www.boxingmall.co.kr/boxingmall.php?loadpage=detail&uid=139253"
    assert p.category_no == 2990
    assert p.model_summary is None
    assert p.sold_out is False
    assert p.scraped_at == NOW


def test_korean_decoding_and_brand(page):
    products = by_uid(page)
    assert products["112709"].name == "리복 베이직 복싱글러브(RSCB-12010BK) 블랙"
    assert products["112709"].brand_text == "리복"
    assert products["126492"].name == "스파트 복싱 미니글러브 [열쇠고리]"
    assert "�" not in "".join(p.name for p in page.products)


def test_single_price_is_sale_price(page):
    p = by_uid(page)["900002"]
    assert p.price == 58000
    assert p.list_price is None


def test_no_price_fails_block(adapter):
    cell = (
        '<table><tr><td class="gray"><span onClick="location.href=\'/boxingmall.php?'
        'loadpage=detail&uid=7&category=2990&top_category=1\'">이름</span></td></tr>'
        '<tr><td class="gray">리복&nbsp;</td></tr></table>'
    )
    page = adapter.parse_list(cell, 2990)
    assert page.products == []
    assert page.failed == 1


def test_sold_out_detected_on_synthetic_cell(page):
    products = by_uid(page)
    assert products["900001"].sold_out is True
    assert [uid for uid, p in products.items() if p.sold_out] == ["900001"]


@pytest.mark.parametrize(
    "marker",
    ['<img src="x/soldout.gif">', '<img src="x/sold_out.gif">', '<img src="x/sold-out.gif">',
     '<img src="x/a.gif" alt="품절">', "<b>품절</b>"],
)
def test_sold_out_markers(adapter, html, marker):
    tag = marker + '<span class="line">242,000원</span>'
    changed = html.replace('<span class="line">242,000원</span>', tag, 1)
    assert by_uid(adapter.parse_list(changed, 2990))["139253"].sold_out is True


def test_points_text_is_not_stock(page):
    # "220개"는 적립 포인트라 재고 판단에 쓰지 않는다
    assert by_uid(page)["139253"].sold_out is False


def test_unknown_images_exclude_known_icons_and_photos(page):
    assert page.unknown_images == ["boxingmall/images/list/soldout.gif"]
    out = format_unknown_images(page.unknown_images + [f"s{i}" for i in range(20)])
    assert out.count("\n  ") == 10


def test_last_page_is_last_position_value(adapter, page):
    assert page.last_page == 2  # position=1 ... position=2 에서 마지막 값


def test_last_page_without_link_is_one(adapter):
    assert adapter.parse_list("<table></table>", 2990).last_page == 1
    assert adapter.parse_list('<a href="x?position=3">[3]</a>', 2990).last_page == 1


def test_last_page_large(adapter):
    html = (
        "<a href='boxingmall.php?loadpage=list&position=1&category=2990&position=7'>"
        "<img src='a.gif' alt='마지막목록'></a>"
    )
    assert adapter.parse_list(html, 2990).last_page == 7


def test_list_url(adapter):
    assert adapter.list_url(2990, 2) == (
        "https://www.boxingmall.co.kr/boxingmall.php?loadpage=list&category=2990"
        "&top_category=1&position=2"
    )
    assert adapter.list_url(2851, 1).endswith("category=2851&top_category=6&position=1")
    assert set(adapter.categories) == {
        2990, 2897, 2981, 2980, 2977, 2767, 2722, 2791, 2979, 2978, 2852, 2851,
    }


def test_fetcher_decodes_cp949_bytes(adapter):
    body = "복싱글러브".encode("cp949")
    transport = httpx.MockTransport(lambda r: httpx.Response(200, content=body))
    client = httpx.Client(transport=transport)
    fetcher = Fetcher.for_adapter(adapter, client=client)
    assert fetcher.get_text(adapter.list_url(2990, 1)) == "복싱글러브"


# --- Fetcher 허용 규칙 ---


def test_fetcher_allows_only_list_requests(adapter):
    fetcher = Fetcher.for_adapter(adapter, client=httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, text="ok"))))
    base = "https://www.boxingmall.co.kr"
    assert fetcher.get_text(f"{base}/boxingmall.php?loadpage=list&category=2990&position=1") == "ok"
    for url in (
        f"{base}/boxingmall.php?loadpage=detail&uid=1",
        f"{base}/boxingmall.php?loadpage=join",
        f"{base}/boxingmall.php?loadpage=login",
        f"{base}/boxingmall.php?loadpage=qanda",
        f"{base}/boxingmall.php",
        f"{base}/boxingmall.php?loadpage=list&loadpage=detail",
        f"{base}/other.php?loadpage=list",
        f"{base}/admin/x",
    ):
        with pytest.raises(ForbiddenUrlError):
            fetcher.get_text(url)


def test_goldenchamps_fetcher_rules_unchanged():
    gc = GoldenChampsAdapter()
    fetcher = Fetcher.for_adapter(gc)
    for url in ("https://goldenchamps.co.kr/admin/x", "https://goldenchamps.co.kr/boxingmall.php"):
        with pytest.raises(ForbiddenUrlError):
            fetcher.get_text(url)
    fetcher.close()


# --- TLS (인증서 경로는 환경변수 BOXINGMALL_CA_FILE) ---


def test_missing_env_gives_clear_error(adapter, monkeypatch):
    monkeypatch.delenv("BOXINGMALL_CA_FILE", raising=False)
    with pytest.raises(MissingCertificateError) as e:
        Fetcher.for_adapter(adapter)
    msg = str(e.value)
    assert "복싱몰 중간 인증서 파일을 찾을 수 없습니다" in msg
    assert "BOXINGMALL_CA_FILE" in msg and "README" in msg


def test_missing_file_gives_clear_error(adapter, tmp_path, monkeypatch):
    monkeypatch.setenv("BOXINGMALL_CA_FILE", str(tmp_path / "none.pem"))
    with pytest.raises(MissingCertificateError) as e:
        Fetcher.for_adapter(adapter)
    assert "BOXINGMALL_CA_FILE" in str(e.value)


def test_adapter_uses_env_not_repo_path(adapter):
    assert adapter.extra_ca_env == "BOXINGMALL_CA_FILE"
    assert not hasattr(adapter, "extra_ca_file")
    assert GoldenChampsAdapter.extra_ca_env is None



def test_tls_verification_stays_on(adapter, tmp_path, monkeypatch):
    pem = tmp_path / "ca.pem"
    pem.write_text("dummy")
    loaded = []
    monkeypatch.setattr(ssl.SSLContext, "load_verify_locations",
                        lambda self, cafile=None, **kw: loaded.append(cafile))
    seen = {}
    real_client = httpx.Client

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(http.httpx, "Client", spy)
    monkeypatch.setenv("BOXINGMALL_CA_FILE", str(pem))
    Fetcher.for_adapter(adapter).close()

    ctx = seen["verify"]
    assert ctx is not False
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True
    assert loaded == [str(pem)]


# --- 쪽 수 안전장치 ---


def _fake_fetcher(pages_html):
    class F:
        def __init__(self):
            self.urls = []

        def get_text(self, url):
            self.urls.append(url)
            return pages_html[len(self.urls) - 1]

    return F()


def test_iter_pages_stops_on_same_uid_set(adapter, html):
    fetcher = _fake_fetcher([html, html, html])  # last_page=2, 2쪽이 1쪽과 같은 상품
    pages = list(iter_pages(adapter, fetcher, 2990, None))
    assert len(pages) == 1
    assert len(fetcher.urls) == 2


def test_iter_pages_raises_over_limit(adapter):
    html = (
        "<a href='boxingmall.php?loadpage=list&position=51'>"
        "<img src='a.gif' alt='마지막목록'></a>"
    )
    with pytest.raises(PageGuardError):
        list(iter_pages(adapter, _fake_fetcher([html]), 2990, None))


# --- 분류 ---


def _c(name, category_no, brand_text=None):
    return classify({
        "shop": "boxingmall", "shop_product_no": "1", "name": name,
        "category_no": category_no, "brand_text": brand_text,
    })


def test_unlisted_brand_text_is_used_as_brand():
    r = _c("탑텐 월드복싱 WB공인 복싱글러브_ 블루", 2990, "탑텐")
    assert (r.status, r.brand, r.category_slug) == (PROMOTABLE, "탑텐", "gloves")


def test_reebok_from_brand_text():
    r = _c("리복 베이직 복싱글러브(RSCB-12010BK) 블랙", 2990, "리복")
    assert r.status == PROMOTABLE
    assert (r.brand, r.category_slug, r.model_code) == ("Reebok", "gloves", "RSCB-12010BK")


def test_brand_text_checked_before_name():
    r = _c("복싱 글러브 블랙", 2990, "아디다스")
    assert r.brand == "Adidas"


def test_keyring_excluded():
    r = _c("스파트 복싱 미니글러브 [열쇠고리]", 2990, "스파트")
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "excluded_accessory")


def test_fallback_per_shop():
    assert _c("리복 베이직 블랙", 2767, "리복").category_reason == "fallback:2767"
    assert _c("리복 베이직 블랙", 2767, "리복").category_slug == "shoes"
    r = _c("리복 베이직 블랙", 2977, "리복")
    assert (r.category_slug, r.category_reason) == ("training", "fallback:2977")
    # 같은 번호라도 골든챔스에서는 폴백이 아니다
    gc = classify({"shop_product_no": "1", "name": "리복 베이직 블랙", "category_no": 2767})
    assert gc.category_slug is None
