-- dev 전용 시드 데이터 (프론트 apps/web/src/lib/mock 과 동일한 데이터)
-- seed 프로파일에서만 읽히는 Flyway repeatable 마이그레이션이며 운영(prod) DB에는 적용되지 않는다.
-- 재실행해도 중복 행이 생기지 않는다 (ON CONFLICT DO NOTHING / NOT EXISTS).

INSERT INTO category (slug, name, sort_order) VALUES
    ('gloves', '글러브', 1),
    ('headgear', '헤드기어', 2),
    ('handwraps', '핸드랩', 3),
    ('bags', '샌드백', 4),
    ('protectors', '보호대', 5),
    ('apparel', '의류', 6)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO brand (name) VALUES
    ('Everlast'),
    ('Venum'),
    ('Winning'),
    ('Title'),
    ('Hayabusa'),
    ('Fairtex')
ON CONFLICT (name) DO NOTHING;

INSERT INTO seller (code, name, base_url) VALUES
    ('coupang', 'Coupang', 'https://example.com/coupang'),
    ('naver', 'Naver', 'https://example.com/naver'),
    ('11st', '11st', 'https://example.com/11st'),
    ('gmarket', 'Gmarket', 'https://example.com/gmarket'),
    ('auction', 'Auction', 'https://example.com/auction')
ON CONFLICT (code) DO NOTHING;

-- 상품: 프론트 id(p01~p28) 순서대로 삽입한다. 같은 (카테고리, 브랜드, 이름) 상품이 이미 있으면 건너뛴다.
INSERT INTO product (category_id, brand_id, name)
SELECT c.id, b.id, v.name
FROM (VALUES
    (1, 'gloves', 'Everlast', '프로 스파링 글러브 16oz'),
    (2, 'gloves', 'Venum', '트레이닝 글러브 12oz'),
    (3, 'gloves', 'Winning', '시합용 가죽 글러브 10oz'),
    (4, 'gloves', 'Title', '벨크로 스파링 글러브 14oz'),
    (5, 'gloves', 'Hayabusa', '핀치 프로 글러브 14oz'),
    (6, 'gloves', 'Fairtex', '무에타이 글러브 14oz'),
    (7, 'gloves', 'Everlast', '키즈 글러브 8oz'),
    (8, 'headgear', 'Title', '스파링 헤드기어 풀페이스'),
    (9, 'headgear', 'Everlast', '오픈페이스 헤드기어'),
    (10, 'headgear', 'Venum', '칙가드 헤드기어'),
    (11, 'headgear', 'Winning', '프리미엄 가죽 헤드기어'),
    (12, 'headgear', 'Hayabusa', '카본 헤드기어'),
    (13, 'handwraps', 'Venum', '멕시칸 핸드랩 4.5m'),
    (14, 'handwraps', 'Hayabusa', '젤 핸드랩 이너글러브'),
    (15, 'handwraps', 'Everlast', '컴프레션 핸드랩 3m'),
    (16, 'handwraps', 'Fairtex', '프로 핸드랩 5m'),
    (17, 'bags', 'Fairtex', '헤비백 120cm 스탠다드'),
    (18, 'bags', 'Everlast', '프리스탠딩 펀칭백'),
    (19, 'bags', 'Title', '스피드백 + 플랫폼 세트'),
    (20, 'bags', 'Venum', '어퍼컷 백 150cm'),
    (21, 'protectors', 'Fairtex', '정강이 보호대 쉰가드'),
    (22, 'protectors', 'Venum', '마우스피스 + 케이스'),
    (23, 'protectors', 'Hayabusa', '가슴 보호대'),
    (24, 'protectors', 'Everlast', '샅보호대 그로인가드'),
    (25, 'apparel', 'Everlast', '복싱 트렁크 쇼츠'),
    (26, 'apparel', 'Title', '복싱 슈즈 하이탑'),
    (27, 'apparel', 'Venum', '트레이닝 후디'),
    (28, 'apparel', 'Fairtex', '무에타이 쇼츠')
) AS v (seq, category_slug, brand_name, name)
JOIN category c ON c.slug = v.category_slug
JOIN brand b ON b.name = v.brand_name
WHERE NOT EXISTS (
    SELECT 1 FROM product p
    WHERE p.category_id = c.id AND p.brand_id = b.id AND p.name = v.name
)
ORDER BY v.seq;

-- 시드 offer 원본 (이 스크립트 안에서만 쓰는 임시 테이블)
CREATE TEMP TABLE seed_offer (
    seller_code  varchar(30)   NOT NULL,
    external_id  varchar(100)  NOT NULL,
    product_name varchar(200)  NOT NULL,
    brand_name   varchar(200)  NOT NULL,
    price        integer       NOT NULL,
    shipping_fee integer       NOT NULL,
    url          varchar(1000) NOT NULL
) ON COMMIT DROP;

INSERT INTO seed_offer (seller_code, external_id, product_name, brand_name, price, shipping_fee, url) VALUES
    ('coupang', 'p01', '프로 스파링 글러브 16oz', 'Everlast', 89000, 0, 'https://example.com/coupang/p01'),
    ('naver', 'p01', '프로 스파링 글러브 16oz', 'Everlast', 92000, 3000, 'https://example.com/naver/p01'),
    ('11st', 'p01', '프로 스파링 글러브 16oz', 'Everlast', 87500, 3500, 'https://example.com/11st/p01'),
    ('coupang', 'p02', '트레이닝 글러브 12oz', 'Venum', 64000, 0, 'https://example.com/coupang/p02'),
    ('gmarket', 'p02', '트레이닝 글러브 12oz', 'Venum', 61000, 3000, 'https://example.com/gmarket/p02'),
    ('naver', 'p03', '시합용 가죽 글러브 10oz', 'Winning', 289000, 0, 'https://example.com/naver/p03'),
    ('coupang', 'p03', '시합용 가죽 글러브 10oz', 'Winning', 295000, 0, 'https://example.com/coupang/p03'),
    ('auction', 'p03', '시합용 가죽 글러브 10oz', 'Winning', 279000, 5000, 'https://example.com/auction/p03'),
    ('coupang', 'p04', '벨크로 스파링 글러브 14oz', 'Title', 72000, 0, 'https://example.com/coupang/p04'),
    ('naver', 'p04', '벨크로 스파링 글러브 14oz', 'Title', 70000, 3000, 'https://example.com/naver/p04'),
    ('gmarket', 'p04', '벨크로 스파링 글러브 14oz', 'Title', 74500, 0, 'https://example.com/gmarket/p04'),
    ('naver', 'p05', '핀치 프로 글러브 14oz', 'Hayabusa', 158000, 0, 'https://example.com/naver/p05'),
    ('coupang', 'p05', '핀치 프로 글러브 14oz', 'Hayabusa', 162000, 0, 'https://example.com/coupang/p05'),
    ('11st', 'p06', '무에타이 글러브 14oz', 'Fairtex', 135000, 3000, 'https://example.com/11st/p06'),
    ('coupang', 'p06', '무에타이 글러브 14oz', 'Fairtex', 139000, 0, 'https://example.com/coupang/p06'),
    ('auction', 'p06', '무에타이 글러브 14oz', 'Fairtex', 132000, 5000, 'https://example.com/auction/p06'),
    ('naver', 'p06', '무에타이 글러브 14oz', 'Fairtex', 140000, 0, 'https://example.com/naver/p06'),
    ('coupang', 'p07', '키즈 글러브 8oz', 'Everlast', 33000, 0, 'https://example.com/coupang/p07'),
    ('gmarket', 'p07', '키즈 글러브 8oz', 'Everlast', 31500, 3000, 'https://example.com/gmarket/p07'),
    ('coupang', 'p08', '스파링 헤드기어 풀페이스', 'Title', 78000, 0, 'https://example.com/coupang/p08'),
    ('11st', 'p08', '스파링 헤드기어 풀페이스', 'Title', 75000, 3000, 'https://example.com/11st/p08'),
    ('naver', 'p08', '스파링 헤드기어 풀페이스', 'Title', 79500, 0, 'https://example.com/naver/p08'),
    ('gmarket', 'p09', '오픈페이스 헤드기어', 'Everlast', 52000, 3000, 'https://example.com/gmarket/p09'),
    ('coupang', 'p09', '오픈페이스 헤드기어', 'Everlast', 54500, 0, 'https://example.com/coupang/p09'),
    ('naver', 'p10', '칙가드 헤드기어', 'Venum', 96000, 0, 'https://example.com/naver/p10'),
    ('coupang', 'p10', '칙가드 헤드기어', 'Venum', 98000, 0, 'https://example.com/coupang/p10'),
    ('11st', 'p10', '칙가드 헤드기어', 'Venum', 93500, 3000, 'https://example.com/11st/p10'),
    ('naver', 'p11', '프리미엄 가죽 헤드기어', 'Winning', 228000, 0, 'https://example.com/naver/p11'),
    ('auction', 'p11', '프리미엄 가죽 헤드기어', 'Winning', 219000, 5000, 'https://example.com/auction/p11'),
    ('coupang', 'p12', '카본 헤드기어', 'Hayabusa', 118000, 0, 'https://example.com/coupang/p12'),
    ('naver', 'p12', '카본 헤드기어', 'Hayabusa', 121000, 0, 'https://example.com/naver/p12'),
    ('gmarket', 'p12', '카본 헤드기어', 'Hayabusa', 115000, 3000, 'https://example.com/gmarket/p12'),
    ('coupang', 'p13', '멕시칸 핸드랩 4.5m', 'Venum', 9900, 3000, 'https://example.com/coupang/p13'),
    ('naver', 'p13', '멕시칸 핸드랩 4.5m', 'Venum', 10500, 2500, 'https://example.com/naver/p13'),
    ('11st', 'p13', '멕시칸 핸드랩 4.5m', 'Venum', 9500, 3000, 'https://example.com/11st/p13'),
    ('auction', 'p13', '멕시칸 핸드랩 4.5m', 'Venum', 11000, 0, 'https://example.com/auction/p13'),
    ('naver', 'p14', '젤 핸드랩 이너글러브', 'Hayabusa', 23000, 3000, 'https://example.com/naver/p14'),
    ('coupang', 'p14', '젤 핸드랩 이너글러브', 'Hayabusa', 24500, 0, 'https://example.com/coupang/p14'),
    ('coupang', 'p15', '컴프레션 핸드랩 3m', 'Everlast', 7500, 3000, 'https://example.com/coupang/p15'),
    ('gmarket', 'p15', '컴프레션 핸드랩 3m', 'Everlast', 7200, 3000, 'https://example.com/gmarket/p15'),
    ('naver', 'p15', '컴프레션 핸드랩 3m', 'Everlast', 8000, 2500, 'https://example.com/naver/p15'),
    ('11st', 'p16', '프로 핸드랩 5m', 'Fairtex', 11800, 3000, 'https://example.com/11st/p16'),
    ('coupang', 'p16', '프로 핸드랩 5m', 'Fairtex', 12500, 0, 'https://example.com/coupang/p16'),
    ('naver', 'p17', '헤비백 120cm 스탠다드', 'Fairtex', 135000, 0, 'https://example.com/naver/p17'),
    ('gmarket', 'p17', '헤비백 120cm 스탠다드', 'Fairtex', 128000, 8000, 'https://example.com/gmarket/p17'),
    ('coupang', 'p17', '헤비백 120cm 스탠다드', 'Fairtex', 139000, 0, 'https://example.com/coupang/p17'),
    ('11st', 'p18', '프리스탠딩 펀칭백', 'Everlast', 189000, 10000, 'https://example.com/11st/p18'),
    ('coupang', 'p18', '프리스탠딩 펀칭백', 'Everlast', 199000, 0, 'https://example.com/coupang/p18'),
    ('naver', 'p19', '스피드백 + 플랫폼 세트', 'Title', 64000, 3000, 'https://example.com/naver/p19'),
    ('coupang', 'p19', '스피드백 + 플랫폼 세트', 'Title', 66000, 0, 'https://example.com/coupang/p19'),
    ('auction', 'p19', '스피드백 + 플랫폼 세트', 'Title', 62000, 5000, 'https://example.com/auction/p19'),
    ('coupang', 'p20', '어퍼컷 백 150cm', 'Venum', 175000, 0, 'https://example.com/coupang/p20'),
    ('naver', 'p20', '어퍼컷 백 150cm', 'Venum', 172000, 4000, 'https://example.com/naver/p20'),
    ('coupang', 'p21', '정강이 보호대 쉰가드', 'Fairtex', 58000, 0, 'https://example.com/coupang/p21'),
    ('auction', 'p21', '정강이 보호대 쉰가드', 'Fairtex', 55000, 3000, 'https://example.com/auction/p21'),
    ('naver', 'p21', '정강이 보호대 쉰가드', 'Fairtex', 59000, 0, 'https://example.com/naver/p21'),
    ('coupang', 'p22', '마우스피스 + 케이스', 'Venum', 12000, 3000, 'https://example.com/coupang/p22'),
    ('gmarket', 'p22', '마우스피스 + 케이스', 'Venum', 11500, 3000, 'https://example.com/gmarket/p22'),
    ('naver', 'p23', '가슴 보호대', 'Hayabusa', 86000, 0, 'https://example.com/naver/p23'),
    ('coupang', 'p23', '가슴 보호대', 'Hayabusa', 89000, 0, 'https://example.com/coupang/p23'),
    ('11st', 'p23', '가슴 보호대', 'Hayabusa', 84000, 3000, 'https://example.com/11st/p23'),
    ('coupang', 'p24', '샅보호대 그로인가드', 'Everlast', 28000, 0, 'https://example.com/coupang/p24'),
    ('gmarket', 'p24', '샅보호대 그로인가드', 'Everlast', 26500, 3000, 'https://example.com/gmarket/p24'),
    ('naver', 'p25', '복싱 트렁크 쇼츠', 'Everlast', 39000, 3000, 'https://example.com/naver/p25'),
    ('coupang', 'p25', '복싱 트렁크 쇼츠', 'Everlast', 41000, 0, 'https://example.com/coupang/p25'),
    ('11st', 'p25', '복싱 트렁크 쇼츠', 'Everlast', 37900, 3000, 'https://example.com/11st/p25'),
    ('coupang', 'p26', '복싱 슈즈 하이탑', 'Title', 98000, 0, 'https://example.com/coupang/p26'),
    ('naver', 'p26', '복싱 슈즈 하이탑', 'Title', 95000, 3000, 'https://example.com/naver/p26'),
    ('auction', 'p26', '복싱 슈즈 하이탑', 'Title', 93500, 3500, 'https://example.com/auction/p26'),
    ('naver', 'p27', '트레이닝 후디', 'Venum', 59000, 3000, 'https://example.com/naver/p27'),
    ('coupang', 'p27', '트레이닝 후디', 'Venum', 61000, 0, 'https://example.com/coupang/p27'),
    ('11st', 'p28', '무에타이 쇼츠', 'Fairtex', 45000, 3000, 'https://example.com/11st/p28'),
    ('coupang', 'p28', '무에타이 쇼츠', 'Fairtex', 47500, 0, 'https://example.com/coupang/p28'),
    ('gmarket', 'p28', '무에타이 쇼츠', 'Fairtex', 44000, 3000, 'https://example.com/gmarket/p28');

-- offer: (seller_id, external_id)가 이미 있으면 건너뛴다. external_id는 프론트 상품 id(p01~p28).
INSERT INTO offer (product_id, seller_id, external_id, url, price, shipping_fee)
SELECT p.id, s.id, so.external_id, so.url, so.price, so.shipping_fee
FROM seed_offer so
JOIN seller s ON s.code = so.seller_code
JOIN brand b ON b.name = so.brand_name
JOIN product p ON p.brand_id = b.id AND p.name = so.product_name
ON CONFLICT (seller_id, external_id) DO NOTHING;

-- price_history: 가격 이력이 아직 없는 시드 offer에만 최근 30일치 일별 가격을 만든다.
--   days_ago = 0 (오늘): 현재 offer 가격·배송비 그대로
--   days_ago = 1~29: 현재가 x (1 + 0.04 + 0.03*sin(days_ago/5 + phase) + (noise-0.5)*0.12), 100원 단위 반올림
--   phase와 noise는 판매처 코드 + external_id + 일자의 md5에서 뽑아 결정적이다 (난수 함수 미사용).
INSERT INTO price_history (offer_id, price, shipping_fee, captured_at)
SELECT g.offer_id,
       CASE WHEN g.days_ago = 0 THEN g.price
            ELSE greatest(100, (round(g.price * (1 + 0.04
                    + 0.03 * sin(g.days_ago / 5.0 + g.phase)
                    + (g.noise - 0.5) * 0.12) / 100.0) * 100)::integer)
       END,
       g.shipping_fee,
       now() - g.days_ago * interval '1 day'
FROM (
    SELECT o.id AS offer_id,
           o.price,
           o.shipping_fee,
           d.days_ago,
           (('x' || substr(md5(so.seller_code || ':' || so.external_id), 1, 8))::bit(32)::bigint
               / 4294967296.0) * 2 * pi() AS phase,
           ('x' || substr(md5(so.seller_code || ':' || so.external_id || ':' || d.days_ago), 1, 8))::bit(32)::bigint
               / 4294967296.0 AS noise
    FROM seed_offer so
    JOIN seller s ON s.code = so.seller_code
    JOIN offer o ON o.seller_id = s.id AND o.external_id = so.external_id
    CROSS JOIN generate_series(0, 29) AS d (days_ago)
    WHERE NOT EXISTS (SELECT 1 FROM price_history ph WHERE ph.offer_id = o.id)
) g;

DROP TABLE seed_offer;
