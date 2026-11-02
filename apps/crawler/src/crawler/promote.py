"""승격 계획 수립 순수 로직. DB·네트워크 접근 금지.

분류된 상품과 기존 offer 상태를 받아 NEW/UPDATE 작업 목록(plan)을 만든다.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

StockChange = Literal["none", "to_out", "to_in"]

# 이번 수집이 전체 수집일 때, 최근 SUCCESS의 최대 items_found 대비 이 비율 미만이면 이상으로 본다
MIN_ITEMS_RATIO = 0.5
BASELINE_RUNS = 5  # 기준값을 정할 때 보는 최근 SUCCESS crawl_run 개수
MAX_PARSE_FAIL_RATIO = 0.10


@dataclass(frozen=True)
class Candidate:
    """승격 대상(PROMOTABLE) 상품."""

    external_id: str
    name: str  # 정규화된 이름
    brand: str
    category_slug: str
    image_url: str | None
    product_url: str
    price: int
    sold_out: bool


@dataclass(frozen=True)
class ExistingOffer:
    id: int
    product_id: int
    price: int
    shipping_fee: int
    in_stock: bool


@dataclass(frozen=True)
class Action:
    kind: Literal["NEW", "UPDATE"]
    candidate: Candidate
    shipping_fee: int
    in_stock: bool
    existing: ExistingOffer | None
    add_history: bool  # price_history 행을 추가해야 하는가
    price_changed: bool  # 가격 또는 배송비가 바뀌었는가
    stock_change: StockChange
    sync_product: bool  # 기존 product의 name/image/category/brand를 동기화해도 되는가


@dataclass(frozen=True)
class PlanCounts:
    new: int
    updated: int
    history_added: int
    price_changed: int
    to_out: int
    to_in: int


def plan(
    candidates: Iterable[Candidate],
    existing: Mapping[str, ExistingOffer],
    shared_product_ids: set[int],
    shipping_fee: int,
) -> list[Action]:
    """상품별 작업 목록. 같은 external_id가 두 번 들어와도 처음 것만 처리한다."""
    actions: list[Action] = []
    seen: set[str] = set()
    for c in candidates:
        if c.external_id in seen:
            continue
        seen.add(c.external_id)
        in_stock = not c.sold_out
        old = existing.get(c.external_id)
        if old is None:
            actions.append(
                Action("NEW", c, shipping_fee, in_stock, None, True, False, "none", False)
            )
            continue
        price_changed = old.price != c.price or old.shipping_fee != shipping_fee
        if old.in_stock == in_stock:
            stock_change: StockChange = "none"
        else:
            stock_change = "to_in" if in_stock else "to_out"
        actions.append(
            Action(
                "UPDATE",
                c,
                shipping_fee,
                in_stock,
                old,
                price_changed,  # 재고만 바뀐 경우는 이력을 쌓지 않는다
                price_changed,
                stock_change,
                old.product_id not in shared_product_ids,
            )
        )
    return actions


def count(actions: Iterable[Action]) -> PlanCounts:
    acts = list(actions)
    return PlanCounts(
        new=sum(a.kind == "NEW" for a in acts),
        updated=sum(a.kind == "UPDATE" for a in acts),
        history_added=sum(a.add_history for a in acts),
        price_changed=sum(a.price_changed for a in acts),
        to_out=sum(a.stock_change == "to_out" for a in acts),
        to_in=sum(a.stock_change == "to_in" for a in acts),
    )


def anomaly_baseline(recent_items: Sequence[int]) -> int | None:
    """최근 SUCCESS crawl_run들의 items_found에서 비교 기준값(최댓값)을 정한다. 이력이 없으면 None.

    부분 수집처럼 작은 값이 섞여도 기준이 낮아지지 않도록 평균이 아닌 최댓값을 쓴다.
    """
    return max(recent_items) if recent_items else None


def detect_anomaly(
    request_errors: int,
    parsed_rows: int,
    parse_failed: int,
    unique_count: int,
    baseline_items: int | None,
    partial: bool,
) -> str | None:
    """수집 이상이면 사유 문자열, 정상이면 None.

    baseline_items는 anomaly_baseline()의 결과다. partial(--category/--max-pages)이면
    기준값 대비 비율 검사는 생략한다.
    """
    if request_errors > 0:
        return f"요청 오류 {request_errors}건"
    total = parsed_rows + parse_failed
    if total == 0:
        return "수집된 상품이 없음"
    if parse_failed / total > MAX_PARSE_FAIL_RATIO:
        return f"파싱 실패 {parse_failed}/{total}건 (10% 초과)"
    if (
        not partial
        and baseline_items
        and unique_count < baseline_items * MIN_ITEMS_RATIO
    ):
        return (
            f"고유 상품 수 {unique_count}개가 최근 SUCCESS 최대 {baseline_items}개의 50% 미만"
        )
    return None
