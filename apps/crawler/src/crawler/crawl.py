"""카테고리의 목록 페이지를 순차로 돌려주는 공통 루프(cli --dry-run, pipeline --save 공용)."""

import logging
from collections.abc import Iterator

from crawler.http import Fetcher
from crawler.shops.base import ListPage, ShopAdapter

log = logging.getLogger("crawler")


class PageGuardError(RuntimeError):
    """쪽 수 상한을 넘는 등, 수집을 계속하면 안 되는 상황."""


def iter_pages(
    adapter: ShopAdapter, fetcher: Fetcher, category_no: int, max_pages: int | None
) -> Iterator[ListPage]:
    """1쪽부터 마지막 쪽까지 ListPage를 하나씩 돌려준다. 요청 실패는 httpx 예외 그대로 올린다.

    adapter.max_pages_limit이 있으면 마지막 쪽이 상한을 넘을 때 PageGuardError를 올리고,
    어떤 쪽이 직전 쪽과 같은 상품 집합이면 조용히 중단한다.
    """
    limit = adapter.max_pages_limit
    page, last_page = 1, 1
    previous: set[str] | None = None
    while page <= last_page and (max_pages is None or page <= max_pages):
        html = fetcher.get_text(adapter.list_url(category_no, page))
        parsed = adapter.parse_list(html, category_no)
        if page == 1:
            last_page = parsed.last_page
            if limit is not None and last_page > limit:
                raise PageGuardError(
                    f"카테고리 {category_no}: 쪽 수 {last_page}가 상한 {limit}을 넘음"
                )
        if limit is not None:
            ids = {p.shop_product_no for p in parsed.products}
            if previous is not None and ids and ids == previous:
                log.warning("카테고리 %d 쪽 %d: 직전 쪽과 같은 상품이라 중단", category_no, page)
                return
            previous = ids
        yield parsed
        page += 1


def merge_unknown_images(into: list[str], page: ListPage) -> None:
    """페이지의 알려진 아이콘 외 이미지 src를 순서를 지키며 중복 없이 into에 더한다."""
    for src in page.unknown_images or ():
        if src not in into:
            into.append(src)


UNKNOWN_IMAGES_LIMIT = 10


def format_unknown_images(images: list[str]) -> str:
    shown = images[:UNKNOWN_IMAGES_LIMIT]
    return "\n".join(
        ["상품 칸 안 알려진 아이콘 외 이미지 src (최대 10개):"] + [f"  {s}" for s in shown]
        if shown
        else ["상품 칸 안 알려진 아이콘 외 이미지 src: 없음"]
    )
