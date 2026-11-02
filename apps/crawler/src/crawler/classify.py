"""상품 이름 정규화·브랜드·카테고리·모델 코드 분류. 순수 함수만 둔다(네트워크·DB 사용 금지)."""

import re
from dataclasses import dataclass
from typing import Any

from crawler import rules

PROMOTABLE = "PROMOTABLE"
UNMATCHED = "UNMATCHED"

_PREFIX = re.compile(rules.NAME_PREFIX_PATTERN)
_SPACES = re.compile(r"\s+")
_MODEL_CODE = re.compile(r"\(([A-Za-z0-9][A-Za-z0-9_.\-]*)\)")
_TOKEN_CHARS = re.compile(r"[A-Za-z0-9_.\-]+")
_MEASURE = re.compile(r"^\d+(\.\d+)?(oz|m|cm|kg|g|ml|mm)$", re.IGNORECASE)
BRAND_TOKEN_WINDOW = 3
BRAND_NAME_MAX = 200  # brand.name 길이 상한


def _has_letter_and_digit(text: str) -> bool:
    return any(c.isalpha() for c in text) and any(c.isdigit() for c in text)


@dataclass
class ClassifiedProduct:
    shop_product_no: str
    name: str
    brand: str | None
    category_slug: str | None
    category_reason: str
    model_code: str | None
    status: str
    unmatched_reason: str | None


def normalize_name(name: str) -> str:
    name = _PREFIX.sub("", name)
    return _SPACES.sub(" ", name).strip()


def normalize_brand(text: str | None) -> str:
    """브랜드명 정규화: 앞뒤 공백(nbsp 포함) 제거, 연속 공백 1개로. 대소문자는 그대로."""
    return _SPACES.sub(" ", text or "").strip()


def extract_brand(name: str, brand_text: str | None = None) -> str | None:
    """브랜드 판정.

    brand_text(브랜드 칸)가 있으면 BRAND_ALIASES → brand_text 자체(의미 없는 값 제외) →
    상품명 앞쪽 3개 토큰 순으로 찾는다. 없으면 상품명 앞쪽 3개 토큰만 본다.
    """
    text = normalize_brand(brand_text)
    if text:
        lowered_text = text.lower()
        for brand, keywords in rules.BRAND_ALIASES.items():
            if any(k.lower() in lowered_text for k in keywords):
                return brand
        if lowered_text not in rules.MEANINGLESS_BRAND_VALUES:
            return text[:BRAND_NAME_MAX].strip()
    for token in normalize_name(name).split(" ")[:BRAND_TOKEN_WINDOW]:
        lowered = token.lower()
        for brand, keywords in rules.BRAND_ALIASES.items():
            if any(k.lower() in lowered for k in keywords):
                return brand
    return None


def extract_model_code(name: str, model_summary: str | None = None) -> str | None:
    """이름 안의 괄호 코드 중 영문자와 숫자를 모두 포함하는 첫 번째를 대문자로 돌려준다.

    괄호 코드가 없으면 공백 토큰에서 찾는다(용량·길이 표기 제외).
    model_summary는 상품 요약 문구라 코드 형식이 일정하지 않아 현재는 사용하지 않는다.
    """
    for code in _MODEL_CODE.findall(name):
        if _has_letter_and_digit(code):
            return code.upper()
    # 괄호 코드가 없으면 공백 토큰 중 모델 코드처럼 생긴 첫 토큰을 쓴다
    for token in name.split():
        if (
            _TOKEN_CHARS.fullmatch(token)
            and len(token) >= 4
            and _has_letter_and_digit(token)
            and not _MEASURE.match(token.strip("-_."))
        ):
            return token.upper()
    return None


def _has_keyword(lowered: str, keyword: str) -> bool:
    """공백이 든 키워드("헤드 가드")는 이름의 공백을 모두 지운 문자열과도 비교한다."""
    kw = keyword.lower()
    if kw in lowered:
        return True
    return " " in kw and kw.replace(" ", "") in lowered.replace(" ", "")


def classify_category(
    name: str, shop_category_no: int | None, shop: str = rules.DEFAULT_SHOP
) -> tuple[str | None, str]:
    lowered = normalize_name(name).lower()
    for keyword in rules.EXCLUDE_KEYWORDS:
        if _has_keyword(lowered, keyword):
            return None, f"excluded:{keyword}"
    for slug, keywords in rules.CATEGORY_KEYWORDS:
        for keyword in keywords:
            if _has_keyword(lowered, keyword):
                return slug, f"keyword:{keyword}"
    shop_fallback = rules.SHOP_CATEGORY_FALLBACK.get(shop, {})
    fallback = shop_fallback.get(shop_category_no) if shop_category_no else None
    if fallback:
        return fallback, f"fallback:{shop_category_no}"
    return None, "none"


def classify(product: dict[str, Any]) -> ClassifiedProduct:
    name = normalize_name(product["name"])
    brand = extract_brand(name, product.get("brand_text"))
    slug, reason = classify_category(
        name, product.get("category_no"), product.get("shop", rules.DEFAULT_SHOP)
    )
    if reason.startswith("excluded:"):
        unmatched = "excluded_accessory"
    elif brand is None:
        unmatched = "unknown_brand"
    elif slug is None:
        unmatched = "unknown_category"
    else:
        unmatched = None
    return ClassifiedProduct(
        shop_product_no=str(product["shop_product_no"]),
        name=name,
        brand=brand,
        category_slug=slug,
        category_reason=reason,
        model_code=extract_model_code(name, product.get("model_summary")),
        status=UNMATCHED if unmatched else PROMOTABLE,
        unmatched_reason=unmatched,
    )


def dedupe(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """(shop, 상품 번호) 기준 중복 제거. 그 몰의 폴백 category_no를 우선, 없으면 먼저 나온 것."""
    chosen: dict[tuple[str, str], dict[str, Any]] = {}
    for p in products:
        shop = p.get("shop", rules.DEFAULT_SHOP)
        fallback = rules.SHOP_CATEGORY_FALLBACK.get(shop, {})
        key = (shop, str(p["shop_product_no"]))
        current = chosen.get(key)
        if current is None:
            chosen[key] = p
        elif current.get("category_no") not in fallback and p.get("category_no") in fallback:
            chosen[key] = p
    return list(chosen.values())
