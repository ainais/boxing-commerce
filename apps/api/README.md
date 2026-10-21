# boxing-api

복싱의모든것 백엔드 (Spring Boot).

## 스택

- Java 21 (Gradle toolchain이 설치된 JDK 21을 자동 감지), Spring Boot 4.1, Gradle
- Spring Web, Data JPA, Validation, Flyway, PostgreSQL, springdoc-openapi

## 프로파일

- 기본(프로파일 없음)·prod: `db/migration`만 적용합니다.
- dev: `src/main/resources/application-dev.yml`(추적됨)이 `db/seed`(데모 시드)를 추가로 적용합니다.
- DB 접속 정보는 `config/application-dev.yml`(git 제외)에 둡니다. 같은 프로파일의 두 파일은 합쳐지고 `config/` 쪽이 우선합니다.
- 배포(prod)는 `config/` 파일 대신 환경변수 `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`로 주입합니다. prod에서 Swagger UI와 API 문서는 기본 비활성이고 `SWAGGER_ENABLED=true`로 켭니다.

## 로컬 실행

1. `config/application-dev.example.yml`을 같은 폴더의 `application-dev.yml`로 복사해 DB 접속 정보를 채웁니다.
2. `apps/api`에서 `./gradlew bootRun --args='--spring.profiles.active=dev'`

JDK 21이 설치되어 있어야 합니다.

- 서버 기본 포트는 8080입니다.
- health 확인: http://localhost:8080/api/health
- Swagger UI: http://localhost:8080/swagger-ui/index.html

## 조회 API

| Method | 경로 | 설명 |
| --- | --- | --- |
| GET | `/api/health` | 생존 확인 (`{"status":"ok"}`) |
| GET | `/api/categories` | 카테고리 목록 (`sort_order` 순) |
| GET | `/api/brands` | 브랜드 이름 배열 (이름순) |
| GET | `/api/products` | 상품 목록 (검색·필터·정렬·페이지네이션) |
| GET | `/api/products/{id}` | 상품 상세 (판매처별 가격, 최근 30일 가격 이력) |
| GET | `/api/products/{id}/related` | 관련 상품 (같은 카테고리의 다른 상품, 인기순) |

### 요청 파라미터

| 경로 | 파라미터 | 설명 | 기본값 / 제한 |
| --- | --- | --- | --- |
| `/api/brands` | `category` | 카테고리 slug. 주면 그 카테고리에 상품이 있는 브랜드만 | 생략 시 전체 |
| `/api/products` | `q` | 상품명·브랜드 부분 일치 (대소문자·공백 무시) | |
| | `category` | 카테고리 slug | |
| | `brand` | 브랜드 이름, 여러 번 지정 가능 (`brand=A&brand=B`) | |
| | `minPrice`, `maxPrice` | 최저가 기준 가격 범위 (원) | 0 이상, `minPrice <= maxPrice` |
| | `sort` | `lowestPrice` \| `priceDesc` \| `name` \| `popular` | `lowestPrice` |
| | `page` | 페이지 번호 | 1부터, 기본 1 |
| | `size` | 페이지 크기 | 기본 12, 최대 50 |
| `/api/products/{id}/related` | `limit` | 개수 | 기본 4, 최대 12 |

- `sort`: `lowestPrice` 최저가 낮은 순, `priceDesc` 최저가 높은 순, `name` 상품명 순, `popular` 최근 30일 클릭 수 → offer 수 → id 순. 동점은 항상 id 오름차순입니다.
- 가격 이력(`priceHistory`)은 최근 30일을 일별로, 상품의 모든 offer 중 최저가를 `{daysAgo, price}`로 내려줍니다 (`daysAgo` 0이 오늘, 날짜 경계는 `Asia/Seoul`). 기록이 없는 날은 건너뛰고, 오늘 기록이 없으면 현재 최저가로 채웁니다.
- offer가 없는 상품은 목록에서 제외되고 상세는 404입니다.

### 응답 형식

- 목록: `{ "items": [...], "total": 28, "page": 1, "size": 12 }`
  - item: `id`(숫자), `name`, `brand`, `categorySlug`, `categoryName`, `imageUrl`, `lowestPrice`, `lowestOffer`, `offerCount`
- 상세: item 필드에서 `offerCount` 대신 `offers`(가격 낮은 순, 같으면 배송비 낮은 순)와 `priceHistory`
- offer: `id`(숫자), `seller`(판매처 이름), `price`, `shippingFee`, `url`
- 오류: `{ "code": "INVALID_PARAMETER" | "NOT_FOUND" | "INTERNAL_ERROR" | ..., "message": "..." }` — 잘못된 파라미터는 400, 없는 상품은 404

### CORS

- 허용 origin은 `app.cors.allowed-origins`로 받습니다. dev 프로파일은 `http://localhost:3000`을 허용합니다.
- prod는 환경변수 `CORS_ALLOWED_ORIGINS`(쉼표 구분)로만 받고, 비어 있으면 허용하지 않습니다.

## 현재 상태

- `GET /api/health`, 조회 API, Flyway 마이그레이션 V1(핵심 7개 테이블), dev 시드 데이터가 있습니다.
- 클릭 로그 기록, 크롤링 수집은 아직 없습니다. web은 아직 이 API에 연결되어 있지 않습니다.
