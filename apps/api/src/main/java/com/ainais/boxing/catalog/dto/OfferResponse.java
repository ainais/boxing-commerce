package com.ainais.boxing.catalog.dto;

/** 프론트 Offer와 같은 형태. seller는 판매처 이름, id는 DB 숫자 그대로 */
public record OfferResponse(Long id, String seller, int price, int shippingFee, String url) {
}
