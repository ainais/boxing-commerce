from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from crawler.models import ScrapedProduct


@dataclass
class ListPage:
    products: list[ScrapedProduct] = field(default_factory=list)
    last_page: int = 1
    failed: int = 0


class ShopAdapter(Protocol):
    """쇼핑몰 어댑터. 새 쇼핑몰은 이 인터페이스를 구현한 파일 하나로 추가한다."""

    name: str
    # 크롤러가 요청해도 되는 URL 경로. http.Fetcher가 이 밖의 경로 요청을 거부한다
    allowed_paths: frozenset[str]
    categories: Mapping[int, str]

    def list_url(self, category_no: int, page: int) -> str: ...

    def parse_list(
        self, html: str, category_no: int, now: datetime | None = None
    ) -> ListPage: ...
