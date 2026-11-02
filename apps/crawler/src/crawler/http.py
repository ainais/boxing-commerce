import logging
import time
from collections.abc import Callable, Collection
from urllib.parse import urlparse

import httpx

USER_AGENT = "Mozilla/5.0 (compatible; boxing-commerce-crawler/0.1)"
DEFAULT_DELAY = 1.5
TIMEOUT = 15.0
MAX_RETRIES = 2

# robots.txt Disallow 대상. 허용 경로 검사와 별개로 한 번 더 막는다
FORBIDDEN_PREFIXES = ("/admin", "/exec/front/", "/api", "/member/", "/myshop/", "/board")

log = logging.getLogger(__name__)


class ForbiddenUrlError(ValueError):
    pass


class Fetcher:
    """순차 요청 전용 HTTP 클라이언트: 요청 간 대기, 타임아웃, 5xx·타임아웃 재시도."""

    def __init__(
        self,
        allowed_paths: Collection[str],
        delay: float = DEFAULT_DELAY,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._allowed_paths = frozenset(allowed_paths)
        self._delay = delay
        self._sleep = sleep
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            follow_redirects=False,
        )
        self._last_request: float | None = None

    def close(self) -> None:
        self._client.close()

    def _check(self, url: str) -> None:
        path = urlparse(url).path
        if path not in self._allowed_paths or path.startswith(FORBIDDEN_PREFIXES):
            raise ForbiddenUrlError(f"허용되지 않은 경로: {path}")

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
