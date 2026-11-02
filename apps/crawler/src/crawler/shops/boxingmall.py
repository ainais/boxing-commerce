import logging
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from crawler.models import ScrapedProduct
from crawler.shops.base import ListPage

log = logging.getLogger(__name__)

BASE_URL = "https://www.boxingmall.co.kr"
LIST_PATH = "/boxingmall.php"

# 상품 링크는 uid 뒤에 &category= 가 붙는다. 배너 링크는 uid만 있어 여기에 걸리지 않는다
_PRODUCT_LINK = re.compile(r"loadpage=detail&uid=(\d+)&category=")
_SOLD_OUT_MARKS = ("soldout", "sold_out", "sold-out", "품절")
_KNOWN_ICONS = frozenset({"icon_ja.gif", "icon_glass.gif", "icon_won.gif", "clover_icon.gif"})
_PRODUCT_PHOTO_PREFIX = "product_images/"

# category -> (top_category, 이름)
_CATEGORIES: dict[int, tuple[int, str]] = {
    2990: (1, "복싱글러브"),
    2897: (1, "백글러브"),
    2981: (2, "샌드백"),
    2980: (2, "펀치/라운드볼"),
    2977: (2, "미트"),
    2767: (3, "복싱화"),
    2722: (3, "복싱복"),
    2791: (3, "땀복"),
    2979: (4, "복싱보호용품"),
    2978: (4, "헤드기어"),
    2852: (6, "줄넘기"),
    2851: (6, "메디신볼"),
}


class BoxingMallAdapter:
    name = "boxingmall"
    code = "boxingmall"
    display_name = "복싱몰"
    base_url = BASE_URL
    # 목록(loadpage=list) 요청만 허용한다. detail, join, login, qanda 등은 거부
    allowed_paths = {LIST_PATH: {"loadpage": "list"}}
    forbidden_prefixes = ("/admin", "/boxingmall/")
    encoding = "cp949"
    extra_ca_env = "BOXINGMALL_CA_FILE"  # 레포에는 두지 않는다. README 참고
    shipping_fee_env = "BOXINGMALL_SHIPPING_FEE"
    max_pages_limit = 50
    reports_unknown_images = True
    categories = {no: label for no, (_, label) in _CATEGORIES.items()}

    def list_url(self, category_no: int, page: int) -> str:
        top = _CATEGORIES[category_no][0]
        return (
            f"{BASE_URL}{LIST_PATH}?loadpage=list&category={category_no}"
            f"&top_category={top}&position={page}"
        )

    def parse_list(
        self, html: str, category_no: int, now: datetime | None = None
    ) -> ListPage:
        soup = BeautifulSoup(html, "lxml")
        now = now or datetime.now(UTC)
        result = ListPage(last_page=_last_page(soup), unknown_images=[])
        seen: set[str] = set()
        for span in soup.select("td.gray span[onclick]"):
            m = _PRODUCT_LINK.search(str(span.get("onclick")))
            if not m or m.group(1) in seen:
                continue
            uid = m.group(1)
            seen.add(uid)
            cell = _cell(span, uid)
            product = _parse_cell(span, cell, uid, category_no, now)
            if product is None:
                result.failed += 1
                continue
            result.products.append(product)
            for src in _unknown_images(cell):
                if src not in result.unknown_images:
                    result.unknown_images.append(src)
        return result


def _cell(span: Tag, uid: str) -> Tag:
    """상품 한 칸. 같은 uid의 상품 사진을 함께 가진 가장 가까운 조상, 없으면 가격을 가진 조상."""
    link = re.compile(rf"uid={uid}&category=")
    for ancestor in span.parents:
        if ancestor.name in ("body", "html", "[document]"):
            break
        if ancestor.find("img", onclick=link):
            return ancestor
    for ancestor in span.parents:
        if ancestor.select_one("span.red12_b, span.line"):
            return ancestor
    return span.parent


def _parse_cell(
    span: Tag, cell: Tag, uid: str, category_no: int, now: datetime
) -> ScrapedProduct | None:
    name = span.get_text(" ", strip=True)
    sale = _to_int(_text(cell.select_one("span.red12_b")))
    line = _to_int(_text(cell.select_one("span.line")))
    if not name or sale is None:
        log.warning("파싱 실패 블록 건너뜀: uid=%s name=%r price=%r", uid, name, sale)
        return None

    img = cell.find("img", onclick=re.compile(rf"uid={uid}&category="))
    src = img.get("src") if img else None
    return ScrapedProduct(
        shop="boxingmall",
        shop_product_no=uid,
        name=name,
        model_summary=None,
        price=sale,
        list_price=line,
        image_url=_absolute_https(str(src)) if src else None,
        product_url=f"{BASE_URL}{LIST_PATH}?loadpage=detail&uid={uid}",
        sold_out=_sold_out(cell),
        category_no=category_no,
        scraped_at=now,
        brand_text=_brand(span, cell),
    )


def _brand(span: Tag, cell: Tag) -> str | None:
    """이름 칸(td.gray) 바로 다음 td.gray."""
    name_td = span.find_parent("td")
    brand_td = name_td.find_next("td", class_="gray") if name_td else None
    if brand_td is None or cell not in brand_td.parents:
        return None
    text = re.sub(r"[\s\xa0]+", " ", brand_td.get_text()).strip()
    return text or None


def _sold_out(cell: Tag) -> bool:
    """방식 미확인: "품절" 텍스트, 또는 img src·alt에 품절 표시 문자열이 있으면 품절로 본다."""
    if "품절" in cell.get_text():
        return True
    for img in cell.find_all("img"):
        haystack = f"{img.get('src') or ''} {img.get('alt') or ''}".lower()
        if any(mark in haystack for mark in _SOLD_OUT_MARKS):
            return True
    return False


def _unknown_images(cell: Tag) -> list[str]:
    found: list[str] = []
    for img in cell.find_all("img"):
        src = str(img.get("src") or "").strip()
        if not src or src.rsplit("/", 1)[-1] in _KNOWN_ICONS:
            continue
        if src.lstrip("/").startswith(_PRODUCT_PHOTO_PREFIX):
            continue
        if src not in found:
            found.append(src)
    return found


def _text(tag: Tag | None) -> str | None:
    return tag.get_text(strip=True) if tag else None


def _to_int(text: str | None) -> int | None:
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else None


def _absolute_https(src: str) -> str:
    url = urljoin(BASE_URL + "/", src)
    return "https:" + url[5:] if url.startswith("http://") else url


def _last_page(soup: BeautifulSoup) -> int:
    """alt='마지막목록' 이미지가 든 <a> 주소에서 마지막 position 값. 없으면 1쪽뿐."""
    for a in soup.find_all("a"):
        if not a.find("img", alt="마지막목록"):
            continue
        positions = parse_qs(urlparse(str(a.get("href"))).query).get("position")
        if positions and positions[-1].isdigit():
            return max(int(positions[-1]), 1)
    return 1
