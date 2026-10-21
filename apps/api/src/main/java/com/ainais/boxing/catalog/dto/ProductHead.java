package com.ainais.boxing.catalog.dto;

/** 상세 조회용 상품 기본 정보 projection (브랜드·카테고리 포함) */
public record ProductHead(
        Long id,
        String name,
        String brand,
        String categorySlug,
        String categoryName,
        String imageUrl) {
}
