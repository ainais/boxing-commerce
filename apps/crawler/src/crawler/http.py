import logging
import os
import ssl
import time
from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

import httpx

if TYPE_CHECKING:
    from crawler.shops.base import ShopAdapter

USER_AGENT = "Mozilla/5.0 (compatible; boxing-commerce-crawler/0.1)"
DEFAULT_DELAY = 1.5
TIMEOUT = 15.0
MAX_RETRIES = 2

# robots.txt Disallow 대상(골든챔스). 허용 경로 검사와 별개로 한 번 더 막는다
FORBIDDEN_PREFIXES = ("/admin", "/exec/front/", "/api", "/member/", "/myshop/", "/board")

log = logging.getLogger(__name__)


class ForbiddenUrlError(ValueError):
    pass


class MissingCertificateError(RuntimeError):
    pass


def resolve_ca_file(env_name: str | None, label: str = "") -> Path | None:
    """추가 인증서 경로를 환경변수에서 읽는다. 변수가 없거나 파일이 없으면 오류."""
    if env_name is None:
        return None
    value = os.environ.get(env_name, "").strip()
    if not value or not Path(value).is_file():
        raise MissingCertificateError(
            f"{label} 중간 인증서 파일을 찾을 수 없습니다: "
            f"환경변수 {env_name} 경로를 확인하세요 (README 참고)".strip()
        )
    return Path(value)


def build_ssl_context(extra_ca_file: Path | None) -> ssl.SSLContext:
    """시스템 CA에 extra_ca_file(PEM)을 더한 검증 컨텍스트. 검증은 끄지 않는다."""
    ctx = ssl.create_default_context()
    if extra_ca_file is not None:
        ctx.load_verify_locations(cafile=str(extra_ca_file))
    return ctx


class Fetcher:
    """순차 요청 전용 HTTP 클라이언트: 요청 간 대기, 타임아웃, 5xx·타임아웃 재시도.

    allowed_paths는 경로 집합이거나 {경로: {쿼리 키: 값}} 매핑이다(후자는 그 쿼리도 일치해야 허용).
    """

    def __init__(
        self,
        allowed_paths: Collection[str] | Mapping[str, Mapping[str, str]],
        delay: float = DEFAULT_DELAY,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        *,
        forbidden_prefixes: tuple[str, ...] = FORBIDDEN_PREFIXES,
        encoding: str | None = None,
        extra_ca_file: Path | None = None,
    ) -> None:
        if isinstance(allowed_paths, Mapping):
            self._allowed: dict[str, Mapping[str, str]] = dict(allowed_paths)
        else:
            self._allowed = {path: {} for path in allowed_paths}
        self._forbidden = forbidden_prefixes
        self._encoding = encoding
        self._delay = delay
        self._sleep = sleep
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=False,
            verify=build_ssl_context(extra_ca_file),
        )
        self._last_request: float | None = None

    @classmethod
    def for_adapter(
        cls,
        adapter: "ShopAdapter",
        delay: float = DEFAULT_DELAY,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> "Fetcher":
        return cls(
            adapter.allowed_paths,
            delay=delay,
            client=client,
            sleep=sleep,
            forbidden_prefixes=adapter.forbidden_prefixes,
            encoding=adapter.encoding,
            extra_ca_file=(
                None if client else resolve_ca_file(adapter.extra_ca_env, adapter.display_name)
            ),
        )

    def close(self) -> None:
        self._client.close()

    def _check(self, url: str) -> None:
        parsed = urlparse(url)
        path = parsed.path
        if path not in self._allowed or path.startswith(self._forbidden):
            raise ForbiddenUrlError(f"허용되지 않은 경로: {path}")
        required = self._allowed[path]
        if required:
            query = parse_qs(parsed.query)
            for key, value in required.items():
                if query.get(key) != [value]:
                    raise ForbiddenUrlError(f"허용되지 않은 요청: {path}?{key}=...")

    def _wait(self) -> None:
        if self._last_request is None:
            return
        remaining = self._delay - (time.monotonic() - self._last_request)
        if remaining > 0:
            self._sleep(remaining)

    def get_text(self, url: str) -> str:
        self._check(url)
        for attempt in range(MAX_RETRIES + 1):
            self._wait()
            self._last_request = time.monotonic()
            try:
                resp = self._client.get(url)
                if resp.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"서버 오류 {resp.status_code}", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                if self._encoding:
                    return resp.content.decode(self._encoding, errors="replace")
                return resp.text
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                retryable = isinstance(e, httpx.TimeoutException) or e.response.status_code >= 500
                if not retryable or attempt == MAX_RETRIES:
                    raise
                backoff = 2**attempt
                log.warning("요청 실패(%s), %ss 후 재시도 %d/%d: %s", e, backoff, attempt + 1,
                            MAX_RETRIES, url)
                self._sleep(backoff)
        raise AssertionError("unreachable")
