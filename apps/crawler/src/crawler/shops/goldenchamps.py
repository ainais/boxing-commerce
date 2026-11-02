import logging
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from crawler.http import FORBIDDEN_PREFIXES
from crawler.models import ScrapedProduct
from crawler.shops.base import ListPage

log = logging.getLogger(__name__)

BASE_URL = "https://goldenchamps.co.kr"
LIST_PATH = "/product/list.html"
_BLOCK_ID = re.compile(r"^anchorBoxId_(\d+)$")


class GoldenChampsAdapter:
    name = "goldenchamps"
    code = "goldenchamps"
    display_name = "골든챔스"
    base_url = BASE_URL
    forbidden_prefixes = FORBIDDEN_PREFIXES
    encoding = None  # httpx 기본 디코딩
    extra_ca_env = None
    shipping_fee_env = "GOLDENCHAMPS_SHIPPING_FEE"
    max_pages_limit = None
    reports_unknown_images = False
    allowed_paths = frozenset({LIST_PATH})
    categories = {
        24: "글러브",
        25: "보호용품",
        27: "트레이닝용품",
        42: "펀칭백",
        53: "중량용품",
        28: "의류/잡화",
        74: "신발",
        140: "도복",
    }

    def list_url(self, category_no: int, page: int) -> str:
        return f"{BASE_URL}{LIST_PATH}?cate_no={category_no}&page={page}"

    def parse_list(
        self, html: str, category_no: int, now: datetime | None = None
    ) -> ListPage:
        soup = BeautifulSoup(html, "lxml")
        now = now or datetime.now(UTC)
        result = ListPage(last_page=_last_page(soup))
        seen: set[str] = set()
        for li in soup.select('ul.prdList li[id^="anchorBoxId_"]'):
            m = _BLOCK_ID.match(str(li.get("id")))
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            product = _parse_block(li, m.group(1), category_no, now)
            if product is None:
                result.failed += 1
            else:
                result.products.append(product)
        return result


def _parse_block(
    li: Tag, product_no: str, category_no: int, now: datetime
) -> ScrapedProduct | None:
    anchor = li.select_one('a[name^="anchorBoxName_"]')
    href = anchor.get("href") if anchor else None
    img = anchor.find("img") if anchor else None
    src = img.get("src") if img else None
    name = _name(li, img)
    values = _spec_values(li)
    price = _to_int(values.get("판매가"))

    if not (href and src and name and price is not None):
        log.warning("파싱 실패 블록 건너뜀: no=%s name=%r price=%r", product_no, name, price)
        return None

    return ScrapedProduct(
        shop="goldenchamps",
        shop_product_no=product_no,
        name=name,
        model_summary=values.get("상품요약정보") or None,
        price=price,
        list_price=_to_int(values.get("소비자가")),
        image_url=_absolute_https(str(src)),
        product_url=urljoin(BASE_URL, str(href)),
        sold_out=li.find("img", alt="품절") is not None,
        category_no=category_no,
        scraped_at=now,
    )


def _name(li: Tag, img: Tag | None) -> str | None:
    a = li.select_one(".description strong.name a")
    if a:
        # "상품명 :" 라벨용 span 제외
        for label in a.select("span.title"):
            label.decompose()
        text = a.get_text(" ", strip=True)
        if text:
            return text
    alt = img.get("alt") if img else None
    return str(alt).strip() or None if alt else None


def _spec_values(li: Tag) -> dict[str, str]:
    """ul.spec li를 라벨(strong.title) 기준으로 {라벨: 값}으로 만든다."""
    values: dict[str, str] = {}
    for item in li.select(".description ul.spec > li"):
        title = item.select_one("strong.title")
        if not title:
            continue
        label = title.get_text(strip=True).replace(":", "").strip()
        for span in item.find_all("span", recursive=False):
            text = span.get_text(strip=True)
            if text:
                values[label] = text
                break
    return values


def _to_int(text: str | None) -> int | None:
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else None


def _absolute_https(src: str) -> str:
    url = urljoin(BASE_URL + "/", src)
    return "https:" + url[5:] if url.startswith("http://") else url


def _page_of(href: str | None) -> int | None:
    if not href:
        return None
    pages = parse_qs(urlparse(href).query).get("page")
    return int(pages[0]) if pages and pages[0].isdigit() else None


def _last_page(soup: BeautifulSoup) -> int:
    pager = soup.select_one(".ec-base-paginate")
    if not pager:
        return 1
    last = pager.select_one("a.last")
    page = _page_of(str(last.get("href"))) if last else None
    if page:
        return page
    numbers = [_page_of(str(a.get("href"))) for a in pager.select("ol a")]
    return max((n for n in numbers if n), default=1)
