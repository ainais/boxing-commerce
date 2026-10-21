package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.dto.OfferResponse;
import com.ainais.boxing.catalog.dto.ProductSummaryResponse;
import com.ainais.boxing.catalog.service.ProductSearchCriteria;
import com.ainais.boxing.catalog.service.ProductSort;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 상품 목록 조회 (네이티브 SQL, DTO projection).
 * 최저가·offer 수는 offer 집계 서브쿼리로, 최저가 offer는 LATERAL 서브쿼리로 한 번에 가져와 N+1을 피한다.
 * 쿼리는 총 2개(count, 목록)이다. offer가 하나도 없는 상품은 목록에서 제외된다.
 */
@Repository
public class ProductQueryRepository {

    private static final String BASE_FROM = """
            FROM product p
            JOIN category c ON c.id = p.category_id
            JOIN brand b ON b.id = p.brand_id
            JOIN (SELECT product_id, MIN(price) AS lowest_price, COUNT(*) AS offer_count
                  FROM offer GROUP BY product_id) agg ON agg.product_id = p.id
            """;

    private static final String LOWEST_OFFER_JOIN = """
            JOIN LATERAL (SELECT o.id, o.seller_id, o.price, o.shipping_fee, o.url
                          FROM offer o
                          WHERE o.product_id = p.id
                          ORDER BY o.price, o.shipping_fee, o.id
                          LIMIT 1) lo ON TRUE
            JOIN seller s ON s.id = lo.seller_id
            """;

    private static final String POPULARITY_JOIN = """
            LEFT JOIN (SELECT o.product_id, COUNT(*) AS clicks
                       FROM click_log cl
                       JOIN offer o ON o.id = cl.offer_id
                       WHERE cl.clicked_at >= :since
                       GROUP BY o.product_id) pop ON pop.product_id = p.id
            """;

    private final JdbcClient jdbc;

    public ProductQueryRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    public long count(ProductSearchCriteria criteria) {
        Map<String, Object> params = new HashMap<>();
        String where = buildWhere(criteria, params);
        return jdbc.sql("SELECT COUNT(*) " + BASE_FROM + where)
                .params(params)
                .query(Long.class)
                .single();
    }

    /** popularSince: popular 정렬에서 클릭 수를 세기 시작하는 시각 */
    public List<ProductSummaryResponse> search(ProductSearchCriteria criteria, OffsetDateTime popularSince) {
        Map<String, Object> params = new HashMap<>();
        String where = buildWhere(criteria, params);
        boolean popular = criteria.sort() == ProductSort.POPULAR;
        if (popular) {
            params.put("since", popularSince);
        }
        params.put("limit", criteria.size());
        params.put("offset", criteria.offset());

        String sql = "SELECT p.id, p.name, p.image_url, b.name AS brand_name,"
                + " c.slug AS category_slug, c.name AS category_name,"
                + " agg.lowest_price, agg.offer_count,"
                + " lo.id AS offer_id, s.name AS seller_name, lo.price AS offer_price,"
                + " lo.shipping_fee AS offer_shipping_fee, lo.url AS offer_url "
                + BASE_FROM + LOWEST_OFFER_JOIN + (popular ? POPULARITY_JOIN : "")
                + where
                + " ORDER BY " + criteria.sort().orderBy()
                + " LIMIT :limit OFFSET :offset";

        return jdbc.sql(sql)
                .params(params)
                .query((rs, rowNum) -> new ProductSummaryResponse(
                        rs.getLong("id"),
                        rs.getString("name"),
                        rs.getString("brand_name"),
                        rs.getString("category_slug"),
                        rs.getString("category_name"),
                        rs.getString("image_url"),
                        rs.getInt("lowest_price"),
                        new OfferResponse(
                                rs.getLong("offer_id"),
                                rs.getString("seller_name"),
                                rs.getInt("offer_price"),
                                rs.getInt("offer_shipping_fee"),
                                rs.getString("offer_url")),
                        rs.getInt("offer_count")))
                .list();
    }

    private String buildWhere(ProductSearchCriteria criteria, Map<String, Object> params) {
        StringBuilder where = new StringBuilder(" WHERE 1 = 1");
        if (criteria.category() != null) {
            where.append(" AND c.slug = :category");
            params.put("category", criteria.category());
        }
        if (criteria.excludeProductId() != null) {
            where.append(" AND p.id <> :excludeId");
            params.put("excludeId", criteria.excludeProductId());
        }
        if (!criteria.brands().isEmpty()) {
            where.append(" AND b.name IN (:brands)");
            params.put("brands", criteria.brands());
        }
        if (!criteria.q().isEmpty()) {
            // 프론트와 같은 규칙: 상품명+브랜드를 소문자로 바꾸고 공백을 제거한 문자열에 대한 부분 일치
            where.append(" AND regexp_replace(lower(p.name || b.name), '[[:space:]]+', '', 'g')")
                    .append(" LIKE :q ESCAPE '!'");
            params.put("q", ProductSearchCriteria.likePattern(ProductSearchCriteria.normalize(criteria.q())));
        }
        if (criteria.minPrice() != null) {
            where.append(" AND agg.lowest_price >= :minPrice");
            params.put("minPrice", criteria.minPrice());
        }
        if (criteria.maxPrice() != null) {
            where.append(" AND agg.lowest_price <= :maxPrice");
            params.put("maxPrice", criteria.maxPrice());
        }
        return where.toString();
    }
}
