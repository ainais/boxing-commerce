"""수집 → dedupe → 분류 → raw_listing 적재 → 승격 → 만료·정리 → crawl_run 마무리."""

import logging
import os
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx
import psycopg
from psycopg.types.json import Jsonb

from crawler import db, rules
from crawler.classify import PROMOTABLE, ClassifiedProduct, classify, dedupe
from crawler.http import Fetcher
from crawler.models import ScrapedProduct
from crawler.promote import (
    BASELINE_RUNS,
    Action,
    Candidate,
    ExistingOffer,
    anomaly_baseline,
    count,
    detect_anomaly,
    plan,
)
from crawler.shops.base import ShopAdapter

log = logging.getLogger("crawler")

SELLER_CODE = "goldenchamps"
RAW_LISTING_RETENTION = timedelta(days=30)
DEFAULT_EXPIRE_DAYS = 3
PRODUCT_NAME_MAX = 200  # product.name varchar(200)
RAW_TITLE_MAX = 500  # raw_listing.title varchar(500)
ERROR_MESSAGE_MAX = 1000  # crawl_run.error_message varchar(1000)


@dataclass
class Stats:
    unique: int = 0
    promotable: int = 0
    new: int = 0
    updated: int = 0
    history_added: int = 0
    price_changed: int = 0
    to_out: int = 0
    to_in: int = 0
    expired: int = 0
    unmatched: Counter = field(default_factory=Counter)
    raw_purged: int = 0


def shipping_fee_from_env() -> int:
    raw = os.environ.get("GOLDENCHAMPS_SHIPPING_FEE", "0")
    try:
        fee = int(raw)
    except ValueError as e:
        raise db.ConfigError(f"GOLDENCHAMPS_SHIPPING_FEE는 정수여야 합니다: {raw!r}") from e
    if fee < 0:
        raise db.ConfigError("GOLDENCHAMPS_SHIPPING_FEE는 0 이상이어야 합니다")
    return fee


def collect(
    adapter: ShopAdapter, fetcher: Fetcher, categories: list[int], max_pages: int | None
) -> tuple[list[ScrapedProduct], int, int]:
    """카테고리·페이지를 순차 수집해 (상품, 파싱 실패 수, 요청 오류 수)를 돌려준다."""
    products: list[ScrapedProduct] = []
    failed = errors = 0
    for cate in categories:
        got = 0
        page, last_page = 1, 1
        while page <= last_page and (max_pages is None or page <= max_pages):
            try:
                html = fetcher.get_text(adapter.list_url(cate, page))
            except httpx.HTTPError as e:
                log.error("카테고리 %d 페이지 %d 요청 실패, 이 카테고리 중단: %s", cate, page, e)
                errors += 1
                break
            parsed = adapter.parse_list(html, cate)
            if page == 1:
                last_page = parsed.last_page
            failed += parsed.failed
            products.extend(parsed.products)
            got += len(parsed.products)
            page += 1
        print(f"[{cate} {adapter.categories[cate]}] 수집 {got}", file=sys.stderr)
    return products, failed, errors


def _required_slugs() -> set[str]:
    slugs = {slug for slug, _ in rules.CATEGORY_KEYWORDS}
    return slugs | set(rules.SHOP_CATEGORY_FALLBACK.values())


def _candidate(d: dict[str, Any], c: ClassifiedProduct) -> Candidate:
    assert c.brand and c.category_slug
    return Candidate(
        external_id=c.shop_product_no,
        name=c.name,
        brand=c.brand,
        category_slug=c.category_slug,
        image_url=d["image_url"],
        product_url=d["product_url"],
        price=d["price"],
        sold_out=bool(d["sold_out"]),
    )


def _raw_rows(
    run_id: int, items: list[tuple[dict[str, Any], ClassifiedProduct]], shipping_fee: int
) -> list[tuple]:
    rows = []
    for d, c in items:
        payload = {**d, "classification": asdict(c)}
        promotable = c.status == PROMOTABLE
        rows.append(
            (
                run_id,
                c.shop_product_no,
                d["name"][:RAW_TITLE_MAX],  # 정규화 전 원본 이름
                d["price"],
                shipping_fee,
                d["product_url"],
                Jsonb(payload),
                "AUTO" if promotable else "UNMATCHED",
                100.00 if promotable else None,
                None if promotable else c.unmatched_reason,
            )
        )
    return rows


def _apply(
    cur: psycopg.Cursor,
    run_id: int,
    seller_id: int,
    category_ids: dict[str, int],
    items: list[tuple[dict[str, Any], ClassifiedProduct]],
    shipping_fee: int,
    stats: Stats,
) -> None:
    # a. raw_listing 적재
    cur.executemany(
        "INSERT INTO raw_listing (crawl_run_id, external_id, title, price, shipping_fee, url,"
        " payload, match_status, match_score, unmatched_reason)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        _raw_rows(run_id, items, shipping_fee),
    )

    # b. 승격
    candidates = [_candidate(d, c) for d, c in items if c.status == PROMOTABLE]
    stats.promotable = len(candidates)

    brand_ids: dict[str, int] = {}
    for name in sorted({c.brand for c in candidates}):
        cur.execute(
            "INSERT INTO brand (name) VALUES (%s)"
            " ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            (name,),
        )
        brand_ids[name] = cur.fetchone()[0]

    cur.execute(
        "SELECT external_id, id, product_id, price, shipping_fee, in_stock"
        " FROM offer WHERE seller_id = %s",
        (seller_id,),
    )
    existing = {
        ext: ExistingOffer(oid, pid, price, fee, in_stock)
        for ext, oid, pid, price, fee, in_stock in cur.fetchall()
    }
    cur.execute("SELECT DISTINCT product_id FROM offer WHERE seller_id <> %s", (seller_id,))
    shared = {row[0] for row in cur.fetchall()}

    actions = plan(candidates, existing, shared, shipping_fee)
    counts = count(actions)
    stats.new, stats.updated = counts.new, counts.updated
    stats.history_added, stats.price_changed = counts.history_added, counts.price_changed
    stats.to_out, stats.to_in = counts.to_out, counts.to_in

    product_of: dict[str, int] = {}  # external_id -> product_id (raw_listing 채우기용)
    history: list[tuple] = []

    new_actions = [a for a in actions if a.kind == "NEW"]
    product_ids = db.insert_returning_ids(
        cur,
        "INSERT INTO product (category_id, brand_id, name, image_url) VALUES (%s, %s, %s, %s)"
        " RETURNING id",
        [
            (
                category_ids[a.candidate.category_slug],
                brand_ids[a.candidate.brand],
                a.candidate.name[:PRODUCT_NAME_MAX],
                a.candidate.image_url,
            )
            for a in new_actions
        ],
    )
    offer_ids = db.insert_returning_ids(
        cur,
        "INSERT INTO offer (product_id, seller_id, external_id, url, price, shipping_fee,"
        " in_stock, last_seen_at) VALUES (%s, %s, %s, %s, %s, %s, %s, now()) RETURNING id",
        [
            (pid, seller_id, a.candidate.external_id, a.candidate.product_url,
             a.candidate.price, a.shipping_fee, a.in_stock)
            for pid, a in zip(product_ids, new_actions, strict=True)
        ],
    )
    for pid, oid, a in zip(product_ids, offer_ids, new_actions, strict=True):
        product_of[a.candidate.external_id] = pid
        history.append((oid, a.candidate.price, a.shipping_fee))

    update_actions = [a for a in actions if a.kind == "UPDATE"]
    cur.executemany(
        "UPDATE offer SET url = %s, price = %s, shipping_fee = %s, in_stock = %s,"
        " last_seen_at = now() WHERE id = %s",
        [
            (a.candidate.product_url, a.candidate.price, a.shipping_fee, a.in_stock,
             _existing(a).id)
            for a in update_actions
        ],
    )
    cur.executemany(
        "UPDATE product SET category_id = %s, brand_id = %s, name = %s, image_url = %s"
        " WHERE id = %s",
        [
            (
                category_ids[a.candidate.category_slug],
                brand_ids[a.candidate.brand],
                a.candidate.name[:PRODUCT_NAME_MAX],
                a.candidate.image_url,
                _existing(a).product_id,
            )
            for a in update_actions
            if a.sync_product
        ],
    )
    for a in update_actions:
        old = _existing(a)
        product_of[a.candidate.external_id] = old.product_id
        if a.add_history:
            history.append((old.id, a.candidate.price, a.shipping_fee))

    cur.executemany(
        "INSERT INTO price_history (offer_id, price, shipping_fee) VALUES (%s, %s, %s)", history
    )
    cur.executemany(
        "UPDATE raw_listing SET product_id = %s WHERE crawl_run_id = %s AND external_id = %s",
        [(pid, run_id, ext) for ext, pid in product_of.items()],
    )


def _existing(action: Action) -> ExistingOffer:
    assert action.existing is not None
    return action.existing


def _expire(cur: psycopg.Cursor, seller_id: int, cutoff: datetime) -> int:
    cur.execute(
        "UPDATE offer SET in_stock = false"
        " WHERE seller_id = %s AND in_stock AND last_seen_at < %s",
        (seller_id, cutoff),
    )
    return cur.rowcount


def _purge_raw(cur: psycopg.Cursor, cutoff: datetime) -> int:
    cur.execute(
        "DELETE FROM raw_listing WHERE crawl_run_id IN"
        " (SELECT id FROM crawl_run WHERE started_at < %s)",
        (cutoff,),
    )
    return cur.rowcount


def _mark_failed(conn: psycopg.Connection, run_id: int, message: str) -> None:
    conn.rollback()
    conn.execute(
        "UPDATE crawl_run SET status = 'FAILED', finished_at = now(), error_message = %s"
        " WHERE id = %s",
        (message[:ERROR_MESSAGE_MAX], run_id),
    )
    conn.commit()


def _print_summary(stats: Stats, run_id: int, elapsed: float) -> None:
    out = sys.stderr
    print("=== 저장 요약 ===", file=out)
    print(f"crawl_run id: {run_id}", file=out)
    print(f"수집 고유 상품: {stats.unique}개, 승격 대상: {stats.promotable}개", file=out)
    print(f"신규 product/offer: {stats.new}개, 갱신 offer: {stats.updated}개", file=out)
    print(f"price_history 추가: {stats.history_added}건", file=out)
    print(f"가격 변동: {stats.price_changed}건", file=out)
    print(f"재고 true→false: {stats.to_out}건, false→true: {stats.to_in}건", file=out)
    print(f"만료 처리: {stats.expired}건", file=out)
    reasons = ", ".join(f"{k} {v}" for k, v in stats.unmatched.most_common()) or "없음"
    print(f"UNMATCHED: {sum(stats.unmatched.values())}개 ({reasons})", file=out)
    print(f"raw_listing 정리 삭제: {stats.raw_purged}행", file=out)
    print(f"소요 시간: {elapsed:.1f}초", file=out)


def run_save(adapter: ShopAdapter, categories: list[int], args: Any) -> int:
    """종료 코드: 0 성공, 1 실패, 2 이미 실행 중."""
    t0 = time.monotonic()
    try:
        shipping_fee = shipping_fee_from_env()
        conn = db.connect_from_env()
    except (db.ConfigError, psycopg.Error) as e:
        print(f"설정/DB 연결 오류: {e}", file=sys.stderr)
        return 1
    try:
        if not db.try_lock(conn):
            print("이미 실행 중입니다 (advisory lock 사용 중).", file=sys.stderr)
            return 2
        try:
            return _run(conn, adapter, categories, args, shipping_fee, t0)
        finally:
            try:
                conn.rollback()
                db.unlock(conn)
            except psycopg.Error:
                pass  # 연결이 끊기면 락은 세션 종료와 함께 풀린다
    except psycopg.Error as e:
        print(f"DB 오류: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def _run(
    conn: psycopg.Connection,
    adapter: ShopAdapter,
    categories: list[int],
    args: Any,
    shipping_fee: int,
    t0: float,
) -> int:
    row = conn.execute("SELECT id FROM seller WHERE code = %s", (SELLER_CODE,)).fetchone()
    if row is None:
        print(f"seller '{SELLER_CODE}'가 DB에 없습니다. V2 마이그레이션 확인 필요", file=sys.stderr)
        return 1
    seller_id = row[0]
    category_ids = dict(conn.execute("SELECT slug, id FROM category").fetchall())
    missing = sorted(_required_slugs() - set(category_ids))
    if missing:
        print(f"DB에 없는 category slug: {missing}. 마이그레이션을 확인하세요.", file=sys.stderr)
        return 1

    run_id, started_at = conn.execute(
        "INSERT INTO crawl_run (seller_id, status) VALUES (%s, 'RUNNING')"
        " RETURNING id, started_at",
        (seller_id,),
    ).fetchone()
    conn.commit()

    partial = bool(args.category) or args.max_pages is not None
    stats = Stats()
    try:
        fetcher = Fetcher(adapter.allowed_paths, delay=args.delay)
        try:
            products, parse_failed, errors = collect(adapter, fetcher, categories, args.max_pages)
        finally:
            fetcher.close()

        unique = dedupe([p.to_dict() for p in products])
        stats.unique = len(unique)

        recent = conn.execute(
            "SELECT items_found FROM crawl_run"
            " WHERE seller_id = %s AND status = 'SUCCESS'"
            " ORDER BY started_at DESC, id DESC LIMIT %s",
            (seller_id, BASELINE_RUNS),
        ).fetchall()
        conn.commit()
        anomaly = detect_anomaly(
            errors, len(products), parse_failed, len(unique),
            anomaly_baseline([r[0] for r in recent]), partial
        )
        if anomaly:
            _mark_failed(conn, run_id, f"수집 이상: {anomaly}")
            print(f"수집 이상으로 중단: {anomaly} (crawl_run {run_id} FAILED)", file=sys.stderr)
            return 1

        items = [(d, classify(d)) for d in unique]
        stats.unmatched = Counter(c.unmatched_reason for _, c in items if c.status != PROMOTABLE)

        with conn.cursor() as cur:
            _apply(cur, run_id, seller_id, category_ids, items, shipping_fee, stats)
            if not partial:
                stats.expired = _expire(
                    cur, seller_id, started_at - timedelta(days=args.expire_days)
                )
            stats.raw_purged = _purge_raw(cur, started_at - RAW_LISTING_RETENTION)
        conn.execute(
            "UPDATE crawl_run SET status = 'SUCCESS', finished_at = now(), items_found = %s"
            " WHERE id = %s",
            (stats.unique, run_id),
        )
        conn.commit()
    except Exception as e:
        log.exception("저장 실패")
        try:
            _mark_failed(conn, run_id, f"{type(e).__name__}: {e}")
        except psycopg.Error:
            log.exception("crawl_run FAILED 기록도 실패")
        return 1

    _print_summary(stats, run_id, time.monotonic() - t0)
    return 0
