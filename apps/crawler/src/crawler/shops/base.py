from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from crawler.models import ScrapedProduct


@dataclass
class ListPage:
    products: list[ScrapedProduct] = field(default_factory=list)
    last_page: int = 1
    failed: int = 0
    # 상품 칸 안에서 발견된 알려진 아이콘 외 이미지 src. None이면 이 어댑터는 보고하지 않는다
    unknown_images: list[str] | None = None


class ShopAdapter(Protocol):
    """쇼핑몰 어댑터. 새 쇼핑몰은 이 인터페이스를 구현한 파일 하나로 추가한다."""

    name: str
    code: str  # seller.code
    display_name: str
    base_url: str
    # 요청해도 되는 URL 경로. {경로: {쿼리 키: 값}}이면 그 쿼리도 일치해야 허용한다
    # http.Fetcher가 이 밖의 요청을 거부한다
    allowed_paths: Collection[str] | Mapping[str, Mapping[str, str]]
    # robots.txt Disallow 대상. 허용 규칙과 별개로 한 번 더 막는다
    forbidden_prefixes: tuple[str, ...]
    encoding: str | None  # None이면 httpx 기본 디코딩
    # 시스템 CA에 더해 신뢰할 인증서(PEM) 경로를 담은 환경변수 이름. None이면 추가 인증서 없음
    extra_ca_env: str | None
    shipping_fee_env: str
    # 이 값이 있으면 쪽 수 상한과 "직전 쪽과 같은 상품 집합이면 중단" 안전장치를 쓴다
    max_pages_limit: int | None
    reports_unknown_images: bool  # True면 수집 요약에 알려진 아이콘 외 이미지 src 목록을 출력한다
    categories: Mapping[int, str]

    def list_url(self, category_no: int, page: int) -> str: ...

    def parse_list(
        self, html: str, category_no: int, now: datetime | None = None
    ) -> ListPage: ...
