# DB 설계 (ERD)

복싱의모든것의 DB 설계 문서입니다. PostgreSQL 기준입니다.

## 범위

- **V1 구현 테이블**: `category`, `brand`, `product`, `seller`, `offer`, `price_history`, `click_log`
- **V2 구현 테이블**: `crawl_run`, `raw_listing` (크롤링 수집 결과를 받는 테이블)
- **V2 기초 데이터**: `seller`(`goldenchamps`), `category` 7종(`shoes` 포함)

## ERD

```mermaid
erDiagram
    CATEGORY ||--o{ PRODUCT : has
    BRAND ||--o{ PRODUCT : makes
    PRODUCT ||--o{ OFFER : "sold as"
    SELLER ||--o{ OFFER : lists
    OFFER ||--o{ PRICE_HISTORY : records
    OFFER ||--o{ CLICK_LOG : "clicked"
    SELLER ||--o{ CRAWL_RUN : "crawled by"
    CRAWL_RUN ||--o{ RAW_LISTING : collects
    PRODUCT |o--o{ RAW_LISTING : "matched to"

    CATEGORY {
        bigint id PK
        varchar slug UK
        varchar name
        int sort_order
    }
    BRAND {
        bigint id PK
        varchar name UK
    }
    PRODUCT {
        bigint id PK
        bigint category_id FK
        bigint brand_id FK
        varchar name
        varchar image_url
        timestamptz created_at
    }
    SELLER {
        bigint id PK
        varchar code UK "11st, naver ..."
        varchar name
        varchar base_url
        boolean active
    }
    OFFER {
        bigint id PK
        bigint product_id FK
        bigint seller_id FK
        varchar external_id "판매처 상품 ID"
        varchar url
        int price "KRW"
        int shipping_fee "KRW"
        boolean in_stock
        timestamptz last_seen_at
    }
    PRICE_HISTORY {
        bigint id PK
        bigint offer_id FK
        int price
        int shipping_fee
        timestamptz captured_at
    }
    CRAWL_RUN {
        bigint id PK
        bigint seller_id FK
        timestamptz started_at
        timestamptz finished_at
        varchar status "RUNNING, SUCCESS, FAILED"
        int items_found "0 이상"
        varchar error_message "nullable"
    }
    RAW_LISTING {
        bigint id PK
        bigint crawl_run_id FK
        bigint product_id FK "nullable"
        varchar external_id "crawl_run_id와 unique"
        varchar title
        int price "KRW"
        int shipping_fee "KRW"
        varchar url
        jsonb payload
        varchar match_status "UNMATCHED, AUTO, MANUAL"
        numeric match_score "nullable"
        varchar unmatched_reason "nullable"
    }
    CLICK_LOG {
        bigint id PK
        bigint offer_id FK
        timestamptz clicked_at
        varchar referrer
        varchar visitor_hash
    }
```

> 다이어그램의 `varchar`는 길이를 생략한 표기입니다. 실제 길이와 NOT NULL 여부는 `V1__create_core_tables.sql`, `V2__create_crawl_tables.sql`이 기준입니다. 모든 PK는 `bigint GENERATED ALWAYS AS IDENTITY`입니다.

## 설계 결정

- **offer와 raw_listing 분리**: raw_listing은 크롤링마다 쌓이는 원본 스냅샷, offer는 판매처별 현재 상태입니다. 매칭 로직을 고쳐도 원본으로 재처리할 수 있습니다.
- **상품 매칭은 raw_listing에서 수행**: `match_status`, `match_score`로 자동 매칭과 수동 확인 대상을 구분합니다.
- **price_history는 offer 단위로 적재**: 상세 페이지의 30일 차트는 일별 최저가 쿼리로 생성하고, 느려지면 일별 집계 테이블을 추가합니다.
- **offer는 `(seller_id, external_id)` unique**: 재수집 시 upsert합니다.
- **click_log에는 IP 원문을 저장하지 않고 `visitor_hash`만 저장**: 프론트 `/go/[offerId]`에서 기록합니다.
- **금액은 KRW 정수(int)로 저장**하고 `price`, `shipping_fee`에 `CHECK (>= 0)`를 둡니다. `shipping_fee`는 `NOT NULL DEFAULT 0`입니다.
- **FK 삭제 정책은 NO ACTION(기본값)**: 삭제 정책은 아직 정하지 않았습니다. 부모 행을 지우려면 자식 행을 먼저 지워야 합니다.
- **기본값**: `category.sort_order`는 `NOT NULL DEFAULT 0`, `offer.last_seen_at`은 `NOT NULL DEFAULT now()`입니다. `offer.in_stock`, `seller.active`는 `NOT NULL DEFAULT true`입니다.
- **NULL 허용 컬럼**: `product.image_url`(이미지가 없을 수 있음), `click_log.referrer`(리퍼러가 없는 유입), `click_log.visitor_hash`(식별값을 만들지 못한 경우), `crawl_run.finished_at`(실행 중), `crawl_run.error_message`(실패했을 때만), `raw_listing.product_id`(아직 매칭 전), `raw_listing.match_score`, `raw_listing.unmatched_reason`입니다.
- **raw_listing은 크롤링마다 쌓이는 스냅샷**: 같은 상품도 실행(`crawl_run`)마다 새 행이 생기며 `(crawl_run_id, external_id)`만 unique입니다. 30일이 지난 행은 정리 대상입니다.
- **승격은 crawler가 수행**: raw_listing을 product/offer로 승격(생성)하는 일은 crawler가 맡습니다. 스키마 변경은 apps/api의 Flyway만 합니다.
- **price_history는 offer의 가격·배송비·재고가 바뀔 때만 적재**: 값이 그대로면 재수집해도 행을 만들지 않습니다.
- **기초 데이터는 멱등하게 넣음**: V2의 `seller`, `category` 삽입은 `ON CONFLICT DO NOTHING`이며, dev 시드(`R__seed_demo_data.sql`)도 같은 방식이라 순서와 무관하게 충돌하지 않습니다.

## 인덱스와 제약

V1 (`V1__create_core_tables.sql`):

| 종류 | 이름 | 대상 |
| --- | --- | --- |
| Unique | `uq_category_slug` | `category(slug)` |
| Unique | `uq_brand_name` | `brand(name)` |
| Unique | `uq_seller_code` | `seller(code)` |
| Unique | `uq_offer_seller_external` | `offer(seller_id, external_id)` |
| CHECK | `ck_offer_price` | `offer.price >= 0` |
| CHECK | `ck_offer_shipping_fee` | `offer.shipping_fee >= 0` |
| CHECK | `ck_price_history_price` | `price_history.price >= 0` |
| CHECK | `ck_price_history_shipping_fee` | `price_history.shipping_fee >= 0` |
| Index | `idx_product_category_brand` | `product(category_id, brand_id)` |
| Index | `idx_product_brand` | `product(brand_id)` — 복합 인덱스의 선두가 `category_id`라서 `brand_id` 단독 조회용으로 추가 |
| Index | `idx_offer_product_price` | `offer(product_id, price)` |
| Index | `idx_price_history_offer_captured` | `price_history(offer_id, captured_at)` |
| Index | `idx_click_log_offer_clicked` | `click_log(offer_id, clicked_at)` |

FK 제약은 `fk_<테이블>_<참조 대상>` 형식입니다 (`fk_product_category`, `fk_product_brand`, `fk_offer_product`, `fk_offer_seller`, `fk_price_history_offer`, `fk_click_log_offer`).

V2 (`V2__create_crawl_tables.sql`):

| 종류 | 이름 | 대상 |
| --- | --- | --- |
| Unique | `uq_raw_listing_run_external` | `raw_listing(crawl_run_id, external_id)` |
| CHECK | `ck_crawl_run_status` | `crawl_run.status IN ('RUNNING', 'SUCCESS', 'FAILED')` |
| CHECK | `ck_crawl_run_items_found` | `crawl_run.items_found >= 0` |
| CHECK | `ck_raw_listing_price` | `raw_listing.price >= 0` |
| CHECK | `ck_raw_listing_shipping_fee` | `raw_listing.shipping_fee >= 0` |
| CHECK | `ck_raw_listing_match_status` | `raw_listing.match_status IN ('UNMATCHED', 'AUTO', 'MANUAL')` |
| Index | `idx_crawl_run_seller_started` | `crawl_run(seller_id, started_at)` |
| Index | `idx_raw_listing_match_status` | `raw_listing(match_status)` |
| Index | `idx_raw_listing_product` | `raw_listing(product_id) WHERE product_id IS NOT NULL` — 부분 인덱스 |

V2의 FK 제약은 `fk_crawl_run_seller`, `fk_raw_listing_crawl_run`, `fk_raw_listing_product`입니다.
