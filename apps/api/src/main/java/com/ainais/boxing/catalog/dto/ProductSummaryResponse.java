package com.ainais.boxing.catalog.dto;

/** 프론트 ProductWithPrice에 대응하는 목록용 상품. offers 전체 대신 최저가 offer와 개수만 담는다. */
public record ProductSummaryResponse(
        Long id,
        String name,
        String brand,
        String categorySlug,
        String categoryName,
        String imageUrl,
        int lowestPrice,
        OfferResponse lowestOffer,
        int offerCount) {
}
