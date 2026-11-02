import pytest

from crawler.classify import (
    PROMOTABLE,
    UNMATCHED,
    classify,
    dedupe,
    extract_brand,
    extract_model_code,
    normalize_name,
)
from crawler.report import build_report


def _c(name: str, category_no: int = 0):
    return classify({"shop_product_no": "1", "name": name, "category_no": category_no})


def test_normalize_name():
    assert normalize_name("[라스트] 아디다스  글러브 ") == "아디다스 글러브"
    assert normalize_name("[A][B] x") == "x"
    assert normalize_name("글러브 [중간] 블랙") == "글러브 [중간] 블랙"


def test_tilt_350_glove():
    name = "[라스트] 아디다스 틸트 350 프로 트레이닝 글러브 레이스업 (ADISPD350TG) 블랙/골드"
    r = _c(name)
    assert not r.name.startswith("[")
    assert (r.brand, r.category_slug, r.category_reason) == ("Adidas", "gloves", "keyword:글러브")
    assert r.model_code == "ADISPD350TG"
    assert r.status == PROMOTABLE and r.unmatched_reason is None


def test_fallback_gloves():
    r = _c("아디다스 파워 500 레이스업 (PWR500L) - 화이트", 24)
    assert (r.brand, r.category_slug, r.category_reason) == ("Adidas", "gloves", "fallback:24")
    assert r.model_code == "PWR500L"


def test_handwraps_whitespace():
    r = _c("아디다스 복싱 프로  핸드랩  - 멕시칸 (ADIBP032S)")
    assert r.name == "아디다스 복싱 프로 핸드랩 - 멕시칸 (ADIBP032S)"
    assert (r.category_slug, r.model_code) == ("handwraps", "ADIBP032S")


def test_number_before_brand():
    r = _c("2024 아디다스 복싱 유니폼 세트 (ADIBTT02) - 블루")
    assert (r.brand, r.category_slug, r.model_code) == ("Adidas", "apparel", "ADIBTT02")


def test_adispeed():
    r = _c("아디다스 아디스피드 500 레이스업 (ADISBG500) - 블랙/골드", 24)
    assert r.brand == "Adidas" and r.category_slug == "gloves"
    assert r.model_code == "ADISBG500"


def test_winning_headgear():
    r = _c("위닝 풀페이스 코보호 헤드기어 (FG-5000)")
    assert (r.brand, r.category_slug, r.model_code) == ("Winning", "headgear", "FG-5000")


def test_protectors():
    assert _c("아디다스 그로인 컵 서포터 (ADIBP06B) - 화이트").category_slug == "protectors"
    r = _c("아디다스 마우스피스 싱글 (ADIBP09) - 화이트")
    assert (r.brand, r.category_slug) == ("Adidas", "protectors")


def test_rival_without_code():
    r = _c("라이벌 Rival 에어로 스파링글러브 RS4V 블랙")
    assert (r.brand, r.category_slug, r.model_code) == ("Rival", "gloves", "RS4V")


def test_exclude_beats_category_keyword():
    r = _c("유니폼 마크비(마킹비)")
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "excluded_accessory")
    assert r.category_slug is None and r.category_reason.startswith("excluded:")


def test_keyring_excluded():
    r = _c("아디다스 펀칭백 미니 키링 (ADIGA02)")
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "excluded_accessory")


def test_unknown_brand():
    r = _c("웨이브 요가 매트")
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "unknown_brand")


def test_nike_shoes_fallback():
    r = _c("나이키 마초마이 3 (ABC123)", 74)
    assert (r.brand, r.category_slug, r.category_reason) == ("Nike", "shoes", "fallback:74")


def test_unknown_category():
    r = _c("아디다스 폼롤러", 28)
    assert (r.status, r.unmatched_reason, r.category_reason) == (
        UNMATCHED, "unknown_category", "none"
    )


def test_no_fallback_for_mixed_categories():
    for no in (28, 53):
        assert _c("아디다스 폼롤러", no).category_slug is None


def test_priority_handwraps_over_gloves():
    r = _c("아디다스 글러브 핸드랩 세트")
    assert (r.category_slug, r.category_reason) == ("handwraps", "keyword:핸드랩")


def test_brand_only_in_first_three_tokens():
    assert extract_brand("프로 복싱 글러브 아디다스") is None
    assert extract_brand("ADIDAS pro glove") == "Adidas"


def test_model_code_rules():
    assert extract_model_code("x (adiSBG800FG)", None) == "ADISBG800FG"
    assert extract_model_code("x (ADISBG175_3.0)", None) == "ADISBG175_3.0"
    assert extract_model_code("x (블랙) (2024) (ABCD)", None) is None
    assert extract_model_code("x (2024) (AB12)", None) == "AB12"


def test_sold_out_does_not_affect_classification():
    r = classify(
        {"shop_product_no": "1", "name": "아디다스 글러브", "category_no": 24, "sold_out": True}
    )
    assert r.status == PROMOTABLE


def test_dedupe_prefers_fallback_category():
    rows = [
        {"shop_product_no": "7", "category_no": 28},
        {"shop_product_no": "8", "category_no": 28},
        {"shop_product_no": "7", "category_no": 24},
        {"shop_product_no": "8", "category_no": 25},
    ]
    result = dedupe(rows)
    # 25도 폴백 키라서 28보다 우선한다
    assert [(r["shop_product_no"], r["category_no"]) for r in result] == [("7", 24), ("8", 25)]


def test_report_smoke():
    rows = [
        {"shop_product_no": "1", "name": "[라스트] 아디다스 글러브 (AB12)", "category_no": 24,
         "sold_out": True},
        {"shop_product_no": "1", "name": "[라스트] 아디다스 글러브 (AB12)", "category_no": 28,
         "sold_out": True},
        {"shop_product_no": "2", "name": "웨이브 요가 매트", "category_no": 27, "sold_out": False},
    ]
    text = build_report(rows, show_unmatched="unknown_brand")
    assert "입력 행 수: 3" in text
    assert "고유 상품 수: 2" in text
    assert "PROMOTABLE: 1개" in text
    assert "모델 코드 추출률: 1 / 2" in text
    assert "이름 정규화로 바뀐 상품 수: 1" in text
    assert "그중 PROMOTABLE: 1" in text


@pytest.mark.parametrize(
    ("name", "brand", "slug", "reason", "code"),
    [
        ("아디다스 수퍼 바디 슬립 프로텍터 (ADISBP01) - 블랙/화이트", "Adidas", "protectors",
         "keyword:프로텍터", "ADISBP01"),
        ("아디다스 스피드 헤드가드 (ADISBHG041) - 블루/골드", "Adidas", "headgear",
         "keyword:헤드가드", "ADISBHG041"),
        ("이사미 풀페이스 복서 헤드 가드 IBX-295 화이트", "Isami", "headgear",
         "keyword:헤드 가드", "IBX-295"),
        ("위닝 복싱 너클 겔가드 (NG-2)", "Winning", "protectors", "keyword:겔가드", "NG-2"),
        ("위닝 프로 파이터 경기용 테이프 (F-4-W)", "Winning", "handwraps",
         "keyword:테이프", "F-4-W"),
        ("리복 와이드 헤드밴드 넥워머 그래픽 3 RACH-10131 라이트그레이", "Reebok", "apparel",
         "keyword:넥워머", "RACH-10131"),
        ("아디다스 너클 슬리브 (ADISKS01) 핑크", "Adidas", "protectors", "fallback:25",
         "ADISKS01"),
        ("아디다스 엘보 가드 (ADIEG01)", "Adidas", "protectors", "keyword:엘보", "ADIEG01"),
    ],
)
def test_category_25_cases(name, brand, slug, reason, code):
    r = _c(name, 25)
    assert (r.brand, r.category_slug, r.category_reason, r.model_code) == (
        brand, slug, reason, code
    )
    assert r.status == PROMOTABLE


def test_converter_excluded():
    r = _c("골든챔스 레이스업 글러브 컨버터 - 2종", 24)
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "excluded_accessory")


def test_unknown_brand_with_category_25():
    r = _c("스컬텍 복싱 겔 가드", 25)
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "unknown_brand")
    r = _c("웨이브 폼롤러 Fazienrolle Wave - 오렌지", 27)
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "unknown_brand")


def test_foam_roller_falls_back_to_training_for_27():
    r = _c("아디다스 폼롤러", 27)
    assert (r.brand, r.category_slug, r.category_reason) == ("Adidas", "training", "fallback:27")
    assert r.status == PROMOTABLE


@pytest.mark.parametrize(
    ("name", "cate", "brand", "slug", "code"),
    [
        ("아디다스 포커스 미트 (레귤러 버젼) (ADISPD400FM) 블랙/화이트", 27, "Adidas",
         "training", "ADISPD400FM"),
        ("아디다스 무에타이 이코노 타이 킥 패드 (ADIBAC31) - 블랙 1개", 27, "Adidas",
         "training", "ADIBAC31"),
        ("위닝 가죽줄넘기 (F-16)", 27, "Winning", "training", "F-16"),
        ("아디다스 프로 점프 로프 (ADI1108) - L(블랙)", 27, "Adidas", "training", "ADI1108"),
        ("리복 손목 중량 밴드 RAWT-11211 - 1.0/1.5kg", 27, "Reebok", "training", "RAWT-11211"),
        ("아디다스 컴뱃스포츠 반바지 S23ATMSH1 (블랙)", 28, "Adidas", "apparel", "S23ATMSH1"),
        ("아디다스 컴뱃스포츠 트레이닝복 세트 (TR70) - 블랙 (기모)", 28, "Adidas", "apparel",
         "TR70"),
        ("아디다스 래쉬 가드 롱 슬리브 - 블랙/화이트 (ADICSR02)", 28, "Adidas", "apparel",
         "ADICSR02"),
        ("아디다스 컴뱃스포츠 3S+ 롱패딩 ADIPK03 SIGN OFF(네이비)", 28, "Adidas", "apparel",
         "ADIPK03"),
        ("위닝 코튼 볼캡 ( CP-2) 베이지", 28, "Winning", "apparel", None),
        ("아디다스 스포츠브라 트레인 브라스트 (adiSWTB01) - 블랙XS", 28, "Adidas", "apparel",
         "ADISWTB01"),
    ],
)
def test_training_and_apparel_cases(name, cate, brand, slug, code):
    r = _c(name, cate)
    assert (r.brand, r.category_slug, r.model_code) == (brand, slug, code)
    assert r.status == PROMOTABLE


def test_training_keyword_reasons():
    assert _c("아디다스 포커스 미트 (ADISPD400FM)", 27).category_reason == "keyword:미트"
    assert _c("위닝 가죽줄넘기 (F-16)", 27).category_reason == "keyword:줄넘기"


@pytest.mark.parametrize(
    ("name", "cate"),
    [
        ("아디다스 트롤리 백 (ADIACC056CS)", 28),
        ("아디다스 스포츠 백 (ADIACC044)", 28),
        ("위닝 로고 키홀더 (P-54)", 28),
        ("위닝 오리지날 핸드 타올 (TW-500)", 27),
    ],
)
def test_new_excluded_accessories(name, cate):
    r = _c(name, cate)
    assert (r.status, r.unmatched_reason) == (UNMATCHED, "excluded_accessory")


def test_training_word_alone_is_not_training_keyword():
    name = "아디다스 틸트 350 프로 트레이닝 글러브 레이스업 (ADISPD350TG) 블랙/골드"
    r = _c(name, 24)
    assert (r.category_slug, r.category_reason) == ("gloves", "keyword:글러브")


def test_bare_pad_is_not_a_keyword():
    # "패드" 단독은 훈련용품 키워드가 아니다(보호구 이름과 겹침)
    r = _c("아디다스 쿠션 패드", 28)
    assert r.category_slug is None


def test_spaced_keyword_matches_with_or_without_space():
    assert _c("위닝 헤드가드").category_slug == "headgear"
    assert _c("위닝 헤드 가드").category_slug == "headgear"
    assert _c("위닝 헤드   가드").category_slug == "headgear"


def test_knuckle_glove_stays_gloves():
    r = _c("아디다스 너클 프로텍션 글러브 (ADITEST01)", 24)
    assert (r.category_slug, r.category_reason) == ("gloves", "keyword:글러브")


def test_model_code_from_tokens():
    assert extract_model_code("라이벌 Rival RS100 스파링 글러브 화이트/골드") == "RS100"
    assert extract_model_code("위닝 복싱 글러브 (레이스타입) MS-300 -10oz") == "MS-300"
    assert extract_model_code("위닝 글러브 10oz 12oz 4.5m 150cm 2kg") is None
    assert extract_model_code("위닝 글러브 -10oz") is None
    assert extract_model_code("유니폼 마크비(마킹비)") is None
    assert extract_model_code("Rival Wave 글러브") is None
    assert extract_model_code("글러브 AB1") is None  # 길이 4 미만
    assert extract_model_code("글러브 AB12가 (CD34)") == "CD34"  # 한글 섞인 토큰 제외, 괄호 우선


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_name_is_unmatched(name):
    assert _c(name).status == UNMATCHED
