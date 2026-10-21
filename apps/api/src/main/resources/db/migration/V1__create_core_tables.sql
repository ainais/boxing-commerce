CREATE TABLE category (
    id         bigint GENERATED ALWAYS AS IDENTITY,
    slug       varchar(50)  NOT NULL,
    name       varchar(200) NOT NULL,
    sort_order integer      NOT NULL DEFAULT 0,
    CONSTRAINT pk_category PRIMARY KEY (id),
    CONSTRAINT uq_category_slug UNIQUE (slug)
);

CREATE TABLE brand (
    id   bigint GENERATED ALWAYS AS IDENTITY,
    name varchar(200) NOT NULL,
    CONSTRAINT pk_brand PRIMARY KEY (id),
    CONSTRAINT uq_brand_name UNIQUE (name)
);

CREATE TABLE product (
    id          bigint GENERATED ALWAYS AS IDENTITY,
    category_id bigint       NOT NULL,
    brand_id    bigint       NOT NULL,
    name        varchar(200) NOT NULL,
    image_url   varchar(1000),
    created_at  timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_product PRIMARY KEY (id),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id),
    CONSTRAINT fk_product_brand FOREIGN KEY (brand_id) REFERENCES brand (id)
);

CREATE TABLE seller (
    id       bigint GENERATED ALWAYS AS IDENTITY,
    code     varchar(30)   NOT NULL,
    name     varchar(200)  NOT NULL,
    base_url varchar(1000) NOT NULL,
    active   boolean       NOT NULL DEFAULT true,
    CONSTRAINT pk_seller PRIMARY KEY (id),
    CONSTRAINT uq_seller_code UNIQUE (code)
);

CREATE TABLE offer (
    id           bigint GENERATED ALWAYS AS IDENTITY,
    product_id   bigint        NOT NULL,
    seller_id    bigint        NOT NULL,
    external_id  varchar(100)  NOT NULL,
    url          varchar(1000) NOT NULL,
    price        integer       NOT NULL,
    shipping_fee integer       NOT NULL DEFAULT 0,
    in_stock     boolean       NOT NULL DEFAULT true,
    last_seen_at timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT pk_offer PRIMARY KEY (id),
    CONSTRAINT fk_offer_product FOREIGN KEY (product_id) REFERENCES product (id),
    CONSTRAINT fk_offer_seller FOREIGN KEY (seller_id) REFERENCES seller (id),
    CONSTRAINT uq_offer_seller_external UNIQUE (seller_id, external_id),
    CONSTRAINT ck_offer_price CHECK (price >= 0),
    CONSTRAINT ck_offer_shipping_fee CHECK (shipping_fee >= 0)
);

CREATE TABLE price_history (
    id           bigint GENERATED ALWAYS AS IDENTITY,
    offer_id     bigint      NOT NULL,
    price        integer     NOT NULL,
    shipping_fee integer     NOT NULL DEFAULT 0,
    captured_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_price_history PRIMARY KEY (id),
    CONSTRAINT fk_price_history_offer FOREIGN KEY (offer_id) REFERENCES offer (id),
    CONSTRAINT ck_price_history_price CHECK (price >= 0),
    CONSTRAINT ck_price_history_shipping_fee CHECK (shipping_fee >= 0)
);

CREATE TABLE click_log (
    id           bigint GENERATED ALWAYS AS IDENTITY,
    offer_id     bigint      NOT NULL,
    clicked_at   timestamptz NOT NULL DEFAULT now(),
    referrer     varchar(1000),
    visitor_hash varchar(64),
    CONSTRAINT pk_click_log PRIMARY KEY (id),
    CONSTRAINT fk_click_log_offer FOREIGN KEY (offer_id) REFERENCES offer (id)
);

CREATE INDEX idx_product_category_brand ON product (category_id, brand_id);
CREATE INDEX idx_product_brand ON product (brand_id);
CREATE INDEX idx_offer_product_price ON offer (product_id, price);
CREATE INDEX idx_price_history_offer_captured ON price_history (offer_id, captured_at);
CREATE INDEX idx_click_log_offer_clicked ON click_log (offer_id, clicked_at);
