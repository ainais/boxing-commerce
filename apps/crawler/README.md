# crawler

쇼핑몰 상품 목록을 수집·파싱하는 Python 모듈입니다. 현재 단계는 **골든챔스 목록 수집 + JSON 출력**까지이며 DB 연결·쓰기는 구현되지 않았습니다.

## 실행

```bash
cd apps/crawler
uv sync
uv run python -m crawler --shop goldenchamps --dry-run
```

| 옵션 | 설명 |
| --- | --- |
| `--shop` | 쇼핑몰 어댑터 이름 (`goldenchamps`) |
| `--category N` | 카테고리 번호. 여러 번 지정 가능, 생략 시 전체 |
| `--max-pages N` | 카테고리당 최대 페이지 (빠른 시험용) |
| `--delay 초` | 요청 사이 대기. 기본 1.5, 환경변수 `CRAWLER_DELAY_SECONDS`로도 설정 |
| `--dry-run` | 상품을 한 줄에 하나씩 JSON으로 stdout에 출력하고, 요약은 stderr에 출력 |

`--dry-run` 없이 실행하면 "DB 쓰기는 아직 구현되지 않음" 안내 후 종료합니다.

빠른 시험 예: `uv run python -m crawler --shop goldenchamps --category 24 --max-pages 1 --dry-run > out.jsonl`

골든챔스 카테고리: 24 글러브, 25 보호용품, 27 트레이닝용품, 42 펀칭백, 53 중량용품, 28 의류/잡화, 74 신발, 140 도복.

## 테스트

```bash
uv run ruff check .
uv run pytest
```

테스트는 `tests/fixtures`의 축소 HTML만 사용하며 네트워크 요청을 하지 않습니다.

## DB 적재 (`--save`)

수집 → dedupe → 분류 → `raw_listing` 적재 → `product`/`offer` 승격 → 만료·정리 → `crawl_run` 마무리를 한 번에 실행합니다. `--dry-run`과 함께 쓸 수 없습니다.

```bash
cp .env.example .env   # 값을 채운다 (.env는 git 제외)
uv run --env-file .env python -m crawler --shop goldenchamps --save
uv run --env-file .env python -m crawler --shop goldenchamps --save --category 24 --max-pages 1
```

- 환경변수: `CRAWLER_DB_HOST`(기본 localhost), `CRAWLER_DB_PORT`(기본 5432), `CRAWLER_DB_NAME`, `CRAWLER_DB_USER`, `CRAWLER_DB_PASSWORD`, `GOLDENCHAMPS_SHIPPING_FEE`(정수, 기본 0). 접속은 개별 파라미터로 하므로 비밀번호에 특수문자가 있어도 됩니다.
- `--expire-days N`(기본 3): N일 넘게 안 보인 offer를 `in_stock=false`로 만듭니다.
- `--category`/`--max-pages`를 주면 부분 수집으로 보고, 만료 처리와 "직전 SUCCESS 대비 50%" 검사를 건너뜁니다.
- 수집 이상(요청 오류, 파싱 실패 10% 초과, 직전 대비 50% 미만)이면 `crawl_run`을 FAILED로 마무리하고 DB에는 쓰지 않습니다.
- 종료 코드: 0 성공, 1 실패, 2 다른 실행이 진행 중(advisory lock).
- `raw_listing`은 30일이 지난 실행분을 삭제합니다.
- 승격 계획은 `promote.py`(순수 로직)가 만들고 `pipeline.py`가 SQL로 적용합니다.

## Jenkins 정기 실행

- 파이프라인: `apps/crawler/Jenkinsfile` (Declarative). 단계는 Setup(`uv sync --frozen`) → Test(`uv run pytest -q`) → Crawl(`--save`)입니다.
- 스케줄: `cron('H 6 * * *')`, 매일 오전 6시대에 한 번 실행됩니다. 빌드는 동시에 하나만 돌고(`disableConcurrentBuilds`), 30분 timeout, 최근 30개 빌드만 보관합니다.
- 필요한 Jenkins Credentials: ID `boxing-db-password`, 종류 **Secret text** (DB 비밀번호). 나머지 접속 값(host, port, db, user, 배송비)은 비밀이 아니라 Jenkinsfile의 `environment`에 있습니다.
- DB 호스트가 `pg-local`인 이유: Jenkins는 컨테이너 안에서 돌기 때문에 `localhost`는 Jenkins 컨테이너 자신을 가리킵니다. 같은 Docker 네트워크의 Postgres 컨테이너를 서비스 이름 `pg-local`로 찾습니다. Jenkins 컨테이너에는 `uv`가 설치돼 있어야 합니다.
- Crawl 종료 코드: `0` 성공, `2` 다른 수집이 이미 실행 중(빌드 UNSTABLE로 표시하고 파이프라인은 정상 종료), 그 외(`1` 등)는 빌드 실패입니다.
- 수집 이상 판정의 "직전 대비 50%" 기준은 이 판매처의 최근 SUCCESS 최대 5건 `items_found`의 최댓값입니다. 이력이 없으면 생략하고, 부분 수집(`--category`, `--max-pages`)에서도 생략합니다.

## 분류 리포트

수집한 JSONL의 이름 정규화·브랜드·카테고리·모델 코드 분류 결과를 요약합니다. 파일을 읽기만 하며 네트워크·DB를 쓰지 않습니다.

```bash
uv run python -m crawler.report --input out.jsonl
uv run python -m crawler.report --input out.jsonl --samples 30 --show-unmatched unknown_brand
```

`--show-unmatched` 값: `excluded_accessory`, `unknown_brand`, `unknown_category`.

규칙은 `src/crawler/rules.py`의 데이터만 고치면 됩니다.

- `BRAND_ALIASES`: 브랜드 추가·키워드 보강 (이름 앞쪽 3개 토큰에서 찾음)
- `CATEGORY_KEYWORDS`: 리스트 순서가 우선순위
- `SHOP_CATEGORY_FALLBACK`: 키워드로 못 정했을 때 쓰는 골든챔스 category_no 폴백
- `EXCLUDE_KEYWORDS`: 액세서리 등 승격 제외 키워드 (카테고리 키워드보다 우선)

고친 뒤 `uv run pytest`로 `tests/test_classify.py`를 확인하세요.

## 어댑터 추가

1. `src/crawler/shops/<shop>.py`에 `shops/base.py`의 `ShopAdapter` Protocol을 구현한 클래스를 만듭니다.
   - `name`, `allowed_paths`(요청 허용 경로), `categories`, `list_url()`, `parse_list()`
   - `parse_list()`는 `ListPage(products, last_page, failed)`를 돌려줍니다. 파싱 실패 블록은 경고 로그 후 건너뛰고 `failed`로 셉니다.
2. `src/crawler/shops/__init__.py`의 `ADAPTERS`에 등록합니다.
3. `tests/fixtures`에 축소 HTML을 두고 파서 테스트를 추가합니다.

## 수집 매너

- 요청 URL은 상품 목록(`/product/list.html`)으로만 구성합니다. `Fetcher`가 어댑터의 `allowed_paths` 밖 경로와 robots.txt Disallow 경로(`/admin`, `/exec/front/`, `/api`, `/member/`, `/myshop/`, 게시판)를 거부합니다.
- 요청 사이 기본 1.5초 대기, timeout 15초, 5xx·타임아웃은 최대 2회 재시도(지수 백오프 1초, 2초).
- User-Agent: `Mozilla/5.0 (compatible; boxing-commerce-crawler/0.1)`
- 카테고리와 페이지는 순차 처리하며 동시 요청을 하지 않습니다.
