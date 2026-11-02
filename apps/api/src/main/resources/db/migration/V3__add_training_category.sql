INSERT INTO category (slug, name, sort_order) VALUES
    ('training', '훈련용품', 8)
ON CONFLICT (slug) DO NOTHING;
