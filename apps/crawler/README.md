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

복싱몰(`--shop boxingmall`) 카테고리(`--category`에 category 번호): 2990 복싱글러브, 2897 백글러브, 2981 샌드백, 2980 펀치/라운드볼, 2977 미트, 2767 복싱화, 2722 복싱복, 2791 땀복, 2979 복싱보호용품, 2978 헤드기어, 2852 줄넘기, 2851 메디신볼.

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

- 환경변수: `CRAWLER_DB_HOST`(기본 localhost), `CRAWLER_DB_PORT`(기본 5432), `CRAWLER_DB_NAME`, `CRAWLER_DB_USER`, `CRAWLER_DB_PASSWORD`, 몰별 배송비 `GOLDENCHAMPS_SHIPPING_FEE`·`BOXINGMALL_SHIPPING_FEE`(정수, 기본 0). 접속은 개별 파라미터로 하므로 비밀번호에 특수문자가 있어도 됩니다.
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
- `SHOP_CATEGORY_FALLBACK`: 키워드로 못 정했을 때 쓰는 몰별(goldenchamps, boxingmall) category_no 폴백
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

## 복싱몰 (`--shop boxingmall`)

- 문자 인코딩이 EUC-KR(cp949)이라 응답 바이트를 cp949로 디코딩합니다.
- 서버가 중간 인증서를 내려주지 않아 기본 검증이 실패합니다. 인증서 검증은 끄지 않고, 시스템 CA에 환경변수 `BOXINGMALL_CA_FILE`이 가리키는 PEM 파일을 더해 신뢰합니다. 변수가 없거나 파일이 없으면 "복싱몰 중간 인증서 파일을 찾을 수 없습니다" 오류로 DB 접속 전에 종료합니다.
- 이 파일은 공개 중간 인증서(GeoTrust TLS RSA CA G1, 만료 2027-11-02)지만 레포에 두지 않습니다(`certs/`는 .gitignore). Jenkins 컨테이너에는 `/var/jenkins_certs/boxingmall-intermediate.pem`으로 마운트되어 있고, 로컬은 `.env`의 `BOXINGMALL_CA_FILE`에 파일 경로를 지정합니다.
- 요청은 `/boxingmall.php`의 `loadpage=list` 목록만 허용하며 detail·join·login 등은 거부합니다. 카테고리당 쪽 수 상한은 50이고, 어떤 쪽이 직전 쪽과 같은 상품이면 중단합니다.
- 품절 표시 방식은 아직 확인되지 않았습니다. 상품 칸 안의 "품절" 텍스트나 soldout 계열 이미지를 품절로 보고, 수집 요약(stderr)에 알려진 아이콘 외 이미지 src를 최대 10개 보여 줍니다.

### 중간 인증서 받기

1. 사이트 인증서를 받습니다: `openssl s_client -connect www.boxingmall.co.kr:443 -servername www.boxingmall.co.kr -showcerts </dev/null | openssl x509 -outform PEM > /tmp/bm_leaf.pem`
2. 인증서의 CA Issuers 주소를 확인합니다: `openssl x509 -in /tmp/bm_leaf.pem -noout -text | grep -A1 "CA Issuers"`
3. 그 주소의 파일(대개 DER `.crt`)을 받아 PEM으로 변환해 `BOXINGMALL_CA_FILE` 경로에 저장합니다: `curl -o /tmp/bm_inter.crt <CA Issuers 주소>` 후 `openssl x509 -inform DER -in /tmp/bm_inter.crt -out "$BOXINGMALL_CA_FILE"` (이미 PEM이면 `-inform PEM`)
4. 확인: `openssl verify -untrusted "$BOXINGMALL_CA_FILE" /tmp/bm_leaf.pem`

## `--raw-only` (승격 없이 raw_listing까지만)

`--save --raw-only`는 `crawl_run`과 `raw_listing`까지만 저장합니다. `product`·`offer`·`price_history` 생성·갱신과 만료 처리는 하지 않고, `raw_listing`의 `match_status`는 모두 `UNMATCHED`입니다(분류 결과는 payload에 들어감). `unmatched_reason`은 분류가 UNMATCHED면 그 사유, PROMOTABLE이면 `not_promoted_raw_only`입니다. `--dry-run`과는 함께 쓸 수 없습니다.

```bash
uv run --env-file .env python -m crawler --shop boxingmall --save --raw-only
```
