package com.ainais.boxing.catalog.dto;

/** 프론트 PricePoint와 같은 형태. daysAgo 0 = 오늘 */
public record PricePointResponse(int daysAgo, int price) {
}
