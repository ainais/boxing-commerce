package com.ainais.boxing.catalog.dto;

import java.util.List;

/**
 * 프론트 ProductDetail에 대응하는 상세 응답.
 * offers는 재고 있는 offer 먼저, 각각 가격 낮은 순(같으면 배송비 낮은 순).
 * inStock은 재고 있는 offer가 하나라도 있는지이며, lowestPrice·lowestOffer는 재고 있는 offer 기준(없으면 null).
 */
public record ProductDetailResponse(
        Long id,
        String name,
        String brand,
        String categorySlug,
        String categoryName,
        String imageUrl,
        boolean inStock,
        Integer lowestPrice,
        OfferResponse lowestOffer,
        List<OfferResponse> offers,
        List<PricePointResponse> priceHistory) {
}
