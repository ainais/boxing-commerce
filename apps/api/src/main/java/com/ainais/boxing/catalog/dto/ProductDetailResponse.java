package com.ainais.boxing.catalog.dto;

import java.util.List;

/** 프론트 ProductDetail에 대응하는 상세 응답. offers는 가격 낮은 순(같으면 배송비 낮은 순). */
public record ProductDetailResponse(
        Long id,
        String name,
        String brand,
        String categorySlug,
        String categoryName,
        String imageUrl,
        int lowestPrice,
        OfferResponse lowestOffer,
        List<OfferResponse> offers,
        List<PricePointResponse> priceHistory) {
}
