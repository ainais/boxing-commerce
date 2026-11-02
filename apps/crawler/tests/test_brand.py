import pytest

from crawler.classify import PROMOTABLE, UNMATCHED, classify, extract_brand, normalize_brand


def _c(name, category_no, brand_text):
    return classify({
        "shop": "boxingmall", "shop_product_no": "1", "name": name,
        "category_no": category_no, "brand_text": brand_text,
    })


def test_brand_text_used_as_is():
    r = _c("스파트 펀치500 복싱 글러브", 2990, "스파트")
    assert (r.brand, r.category_slug, r.status) == ("스파트", "gloves", PROMOTABLE)
    r = _c("탑텐 월드복싱 WB공인 복싱글러브_ 블루", 2990, "탑텐")
    assert (r.brand, r.category_slug, r.status) == ("탑텐", "gloves", PROMOTABLE)


@pytest.mark.parametrize(
    ("text", "brand"), [("아디다스복싱", "Adidas"), ("리복", "Reebok"), ("나이키", "Nike")]
)
def test_alias_wins_over_raw_text(text, brand):
    assert _c("복싱 글러브", 2990, text).brand == brand


def test_jump_rope_brand_and_fallback():
    r = _c("김수열줄넘기 프로 스피드", 2852, "김수열줄넘기")
    assert (r.brand, r.category_slug) == ("김수열줄넘기", "training")
    assert r.category_reason == "keyword:줄넘기"  # 이름 키워드가 폴백보다 먼저
    r = _c("김수열 스피드 로프", 2852, "김수열줄넘기")
    assert (r.category_slug, r.category_reason) == ("training", "fallback:2852")


def test_category_fallbacks_with_brand_text():
    assert _c("스타 메디신볼 3kg", 2851, "스타").category_reason == "fallback:2851"
    assert _c("스타 메디신볼 3kg", 2851, "스타").category_slug == "training"
    r = _c("스파트 기능성 의류", 2791, "스파트")
    assert (r.category_slug, r.category_reason, r.brand) == ("apparel", "fallback:2791", "스파트")
    r = _c("스파트 라이트 플러스", 2767, "스파트")
    assert (r.category_slug, r.category_reason, r.brand) == ("shoes", "fallback:2767", "스파트")


def test_meaningless_brand_falls_back_to_name_alias():
    r = _c("아디다스 복싱 글러브 (ADIXX)", 2990, "기타")
    assert (r.brand, r.status) == ("Adidas", PROMOTABLE)


@pytest.mark.parametrize(
    "text", ["기타", "-", "없음", "브랜드없음", "무브랜드", "공용", "미정", "", "  "]
)
def test_meaningless_values_without_known_name_are_unknown_brand(text):
    r = _c("월드 복싱 글러브", 2990, text)
    assert (r.brand, r.status, r.unmatched_reason) == (None, UNMATCHED, "unknown_brand")


def test_brand_text_whitespace_and_nbsp_normalized():
    assert extract_brand("x", " 스파트 ") == "스파트"
    assert extract_brand("x", "\xa0스파트\xa0") == "스파트"
    assert extract_brand("x", " 타이틀   복싱 ") == "타이틀 복싱"
    assert normalize_brand("Title  Boxing") == "Title Boxing"  # 대소문자는 유지


def test_brand_text_truncated_to_200():
    brand = extract_brand("x", "가" * 250)
    assert brand == "가" * 200


def test_keyring_excluded_even_with_brand():
    r = _c("스파트 복싱 미니글러브 [열쇠고리]", 2990, "스파트")
    assert (r.brand, r.status, r.unmatched_reason) == ("스파트", UNMATCHED, "excluded_accessory")


def test_goldenchamps_without_brand_text_unchanged():
    gc = classify({"shop_product_no": "1", "name": "탑텐 글러브", "category_no": 24})
    assert (gc.brand, gc.unmatched_reason) == (None, "unknown_brand")
    gc = classify({"shop_product_no": "1", "name": "아디다스 글러브", "category_no": 24,
                   "brand_text": None})
    assert gc.brand == "Adidas"
