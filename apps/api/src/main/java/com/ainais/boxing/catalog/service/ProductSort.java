package com.ainais.boxing.catalog.service;

import com.ainais.boxing.common.ApiException;

import java.util.Arrays;

/** 정렬 기준. 동점일 때 마지막에 항상 p.id 오름차순을 둬서 페이지가 흔들리지 않게 한다. */
public enum ProductSort {
    LOWEST_PRICE("lowestPrice", "agg.lowest_price ASC, p.id ASC"),
    PRICE_DESC("priceDesc", "agg.lowest_price DESC, p.id ASC"),
    NAME("name", "p.name ASC, p.id ASC"),
    /** 최근 30일 클릭 수 내림차순, offer 수 내림차순, id 오름차순 */
    POPULAR("popular", "COALESCE(pop.clicks, 0) DESC, agg.offer_count DESC, p.id ASC");

    private final String value;
    private final String orderBy;

    ProductSort(String value, String orderBy) {
        this.value = value;
        this.orderBy = orderBy;
    }

    public String value() {
        return value;
    }

    public String orderBy() {
        return orderBy;
    }

    public static ProductSort from(String value) {
        return Arrays.stream(values())
                .filter(s -> s.value.equals(value))
                .findFirst()
                .orElseThrow(() -> ApiException.invalidParameter(
                        "sort는 lowestPrice, priceDesc, name, popular 중 하나여야 합니다."));
    }
}
