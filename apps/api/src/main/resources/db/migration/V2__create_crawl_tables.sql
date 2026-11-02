CREATE TABLE crawl_run (
    id            bigint GENERATED ALWAYS AS IDENTITY,
    seller_id     bigint        NOT NULL,
    started_at    timestamptz   NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    status        varchar(20)   NOT NULL,
    items_found   integer       NOT NULL DEFAULT 0,
    error_message varchar(1000),
    CONSTRAINT pk_crawl_run PRIMARY KEY (id),
    CONSTRAINT fk_crawl_run_seller FOREIGN KEY (seller_id) REFERENCES seller (id),
    CONSTRAINT ck_crawl_run_status CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    CONSTRAINT ck_crawl_run_items_found CHECK (items_found >= 0)
);

CREATE TABLE raw_listing (
    id               bigint GENERATED ALWAYS AS IDENTITY,
    crawl_run_id     bigint        NOT NULL,
    product_id       bigint,
    external_id      varchar(100)  NOT NULL,
    title            varchar(500)  NOT NULL,
    price            integer       NOT NULL,
    shipping_fee     integer       NOT NULL DEFAULT 0,
    url              varchar(1000) NOT NULL,
    payload          jsonb         NOT NULL,
    match_status     varchar(20)   NOT NULL DEFAULT 'UNMATCHED',
    match_score      numeric(5, 2),
    unmatched_reason varchar(100),
    CONSTRAINT pk_raw_listing PRIMARY KEY (id),
    CONSTRAINT fk_raw_listing_crawl_run FOREIGN KEY (crawl_run_id) REFERENCES crawl_run (id),
    CONSTRAINT fk_raw_listing_product FOREIGN KEY (product_id) REFERENCES product (id),
    CONSTRAINT uq_raw_listing_run_external UNIQUE (crawl_run_id, external_id),
    CONSTRAINT ck_raw_listing_price CHECK (price >= 0),
    CONSTRAINT ck_raw_listing_shipping_fee CHECK (shipping_fee >= 0),
    CONSTRAINT ck_raw_listing_match_status CHECK (match_status IN ('UNMATCHED', 'AUTO', 'MANUAL'))
);

CREATE INDEX idx_crawl_run_seller_started ON crawl_run (seller_id, started_at);
CREATE INDEX idx_raw_listing_match_status ON raw_listing (match_status);
CREATE INDEX idx_raw_listing_product ON raw_listing (product_id) WHERE product_id IS NOT NULL;

-- 기초 데이터 (재실행해도 중복 행이 생기지 않는다)
INSERT INTO seller (code, name, base_url) VALUES
    ('goldenchamps', '골든챔스', 'https://goldenchamps.co.kr')
ON CONFLICT (code) DO NOTHING;

INSERT INTO category (slug, name, sort_order) VALUES
    ('gloves', '글러브', 1),
    ('headgear', '헤드기어', 2),
    ('handwraps', '핸드랩', 3),
    ('bags', '샌드백', 4),
    ('protectors', '보호대', 5),
    ('apparel', '의류', 6),
    ('shoes', '신발', 7)
ON CONFLICT (slug) DO NOTHING;
