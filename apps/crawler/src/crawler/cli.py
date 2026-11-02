import argparse
import json
import logging
import os
import sys

import httpx

from crawler.http import DEFAULT_DELAY, Fetcher
from crawler.shops import ADAPTERS
from crawler.shops.base import ShopAdapter

log = logging.getLogger("crawler")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crawler", description="쇼핑몰 상품 목록 수집")
    p.add_argument("--shop", required=True, choices=sorted(ADAPTERS))
    p.add_argument(
        "--category", type=int, action="append",
        help="카테고리 번호(여러 번 지정 가능, 생략 시 전체)",
    )
    p.add_argument("--max-pages", type=int, help="카테고리당 최대 페이지(빠른 시험용)")
    p.add_argument(
        "--delay", type=float,
        default=float(os.environ.get("CRAWLER_DELAY_SECONDS", DEFAULT_DELAY)),
        help="요청 사이 대기 초(기본 1.5, 환경변수 CRAWLER_DELAY_SECONDS)",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="DB에 쓰지 않고 JSON Lines로 stdout 출력"
    )
    mode.add_argument(
        "--save", action="store_true", help="수집 결과를 DB에 적재하고 product/offer로 승격"
    )
    p.add_argument(
        "--expire-days", type=int, default=3,
        help="--save 시 이 일수 동안 안 보인 offer를 품절 처리(기본 3, 부분 수집에서는 생략)",
    )
    return p


def crawl_category(adapter: ShopAdapter, fetcher: Fetcher, category_no: int,
                   max_pages: int | None) -> tuple[int, int, int, int]:
    """카테고리를 순차 수집해 JSON을 한 줄씩 출력하고 (수집, 품절, 파싱 실패, 오류)를 돌려준다."""
    collected = sold_out = failed = errors = 0
    page, last_page = 1, 1
    while page <= last_page and (max_pages is None or page <= max_pages):
        try:
            html = fetcher.get_text(adapter.list_url(category_no, page))
        except httpx.HTTPError as e:
            log.error("카테고리 %d 페이지 %d 요청 실패, 이 카테고리 중단: %s", category_no, page, e)
            errors += 1
            break
        parsed = adapter.parse_list(html, category_no)
        if page == 1:
            last_page = parsed.last_page
        failed += parsed.failed
        for product in parsed.products:
            print(json.dumps(product.to_dict(), ensure_ascii=False), flush=True)
            collected += 1
            sold_out += product.sold_out
        page += 1
    return collected, sold_out, failed, errors


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")

    if not (args.dry_run or args.save):
        print("--dry-run 또는 --save 중 하나를 지정하세요.", file=sys.stderr)
        return 1

    adapter = ADAPTERS[args.shop]()
    categories = args.category or list(adapter.categories)
    unknown = [c for c in categories if c not in adapter.categories]
    if unknown:
        print(f"알 수 없는 카테고리: {unknown} (가능: {list(adapter.categories)})", file=sys.stderr)
        return 2

    if args.save:
        from crawler.pipeline import run_save  # psycopg는 --save에서만 불러온다

        return run_save(adapter, categories, args)

    fetcher = Fetcher(adapter.allowed_paths, delay=args.delay)
    total = sold = failed = errors = 0
    try:
        for cate in categories:
            c, s, f, e = crawl_category(adapter, fetcher, cate, args.max_pages)
            print(f"[{cate} {adapter.categories[cate]}] 수집 {c}", file=sys.stderr)
            total, sold, failed, errors = total + c, sold + s, failed + f, errors + e
    finally:
        fetcher.close()

    summary = f"총 {total}개, 품절 {sold}개, 파싱 실패 {failed}개, 요청 오류 {errors}건"
    print(summary, file=sys.stderr)
    return 0 if errors == 0 else 1
