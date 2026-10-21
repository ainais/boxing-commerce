# DB 설계 (ERD)

복싱의모든것의 DB 설계 문서입니다. PostgreSQL 기준입니다.

## 범위

- **1차 구현 테이블**: `category`, `brand`, `product`, `seller`, `offer`, `price_history`, `click_log`
- **크롤링 수집 단계에서 추가 예정**: `crawl_run`, `raw_listing`

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
        int items_found
    }
    RAW_LISTING {
        bigint id PK
        bigint crawl_run_id FK
        bigint product_id FK "nullable"
        varchar external_id
        varchar title
        int price
        int shipping_fee
        varchar url
        jsonb payload
        varchar match_status "UNMATCHED, AUTO, MANUAL"
        numeric match_score
    }
    CLICK_LOG {
        bigint id PK
        bigint offer_id FK
        timestamptz clicked_at
        varchar referrer
        varchar visitor_hash
    }
```

## 설계 결정

- **offer와 raw_listing 분리**: raw_listing은 크롤링마다 쌓이는 원본 스냅샷, offer는 판매처별 현재 상태입니다. 매칭 로직을 고쳐도 원본으로 재처리할 수 있습니다.
- **상품 매칭은 raw_listing에서 수행**: `match_status`, `match_score`로 자동 매칭과 수동 확인 대상을 구분합니다.
- **price_history는 offer 단위로 적재**: 상세 페이지의 30일 차트는 일별 최저가 쿼리로 생성하고, 느려지면 일별 집계 테이블을 추가합니다.
- **offer는 `(seller_id, external_id)` unique**: 재수집 시 upsert합니다.
- **click_log에는 IP 원문을 저장하지 않고 `visitor_hash`만 저장**: 프론트 `/go/[offerId]`에서 기록합니다.
- **금액은 KRW 정수(int)로 저장**합니다.

## 인덱스 후보

- `product(category_id, brand_id)`
- `offer(product_id, price)`
- `offer(seller_id, external_id)` unique
- `price_history(offer_id, captured_at)`
- `raw_listing(match_status)`
- `click_log(offer_id, clicked_at)`
