package com.ainais.boxing.catalog.service;

import com.ainais.boxing.common.ApiException;

import java.util.List;
import java.util.Locale;

/** 목록 조회 조건. of()에서 파라미터를 검증한다(잘못되면 400). */
public record ProductSearchCriteria(
        String q,
        String category,
        List<String> brands,
        Integer minPrice,
        Integer maxPrice,
        ProductSort sort,
        int page,
        int size,
        Long excludeProductId) {

    public static final int DEFAULT_SIZE = 12;
    public static final int MAX_SIZE = 50;

    public static ProductSearchCriteria of(
            String q, String category, List<String> brands,
            Integer minPrice, Integer maxPrice, String sort, int page, int size) {
        if (page < 1) {
            throw ApiException.invalidParameter("page는 1 이상이어야 합니다.");
        }
        if (size < 1 || size > MAX_SIZE) {
            throw ApiException.invalidParameter("size는 1 이상 " + MAX_SIZE + " 이하여야 합니다.");
        }
        if (minPrice != null && minPrice < 0) {
            throw ApiException.invalidParameter("minPrice는 0 이상이어야 합니다.");
        }
        if (maxPrice != null && maxPrice < 0) {
            throw ApiException.invalidParameter("maxPrice는 0 이상이어야 합니다.");
        }
        if (minPrice != null && maxPrice != null && minPrice > maxPrice) {
            throw ApiException.invalidParameter("minPrice는 maxPrice보다 클 수 없습니다.");
        }
        List<String> cleanBrands = brands == null
                ? List.of()
                : brands.stream().map(String::trim).filter(s -> !s.isEmpty()).distinct().toList();
        return new ProductSearchCriteria(
                q == null ? "" : q.trim(),
                category == null || category.isBlank() ? null : category.trim(),
                cleanBrands,
                minPrice,
                maxPrice,
                sort == null ? ProductSort.LOWEST_PRICE : ProductSort.from(sort),
                page,
                size,
                null);
    }

    /** 관련 상품용: 같은 카테고리의 다른 상품을 popular 규칙으로 */
    public static ProductSearchCriteria related(String categorySlug, Long excludeProductId, int limit) {
        return new ProductSearchCriteria(
                "", categorySlug, List.of(), null, null, ProductSort.POPULAR, 1, limit, excludeProductId);
    }

    /** 프론트 normalize와 같은 규칙: 소문자 + 모든 공백 제거 */
    public static String normalize(String text) {
        return text.toLowerCase(Locale.ROOT).replaceAll("\\s+", "");
    }

    /** LIKE 패턴용 이스케이프 (escape 문자는 느낌표) */
    public static String likePattern(String normalized) {
        String escaped = normalized.replace("!", "!!").replace("%", "!%").replace("_", "!_");
        return "%" + escaped + "%";
    }

    public long offset() {
        return (long) (page - 1) * size;
    }
}
