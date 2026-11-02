INSERT INTO seller (code, name, base_url) VALUES
    ('boxingmall', '복싱몰', 'https://www.boxingmall.co.kr')
ON CONFLICT (code) DO NOTHING;
