package com.ainais.boxing.catalog.dto;

/** 프론트 Category({slug, name})와 같은 형태 */
public record CategoryResponse(String slug, String name) {
}
