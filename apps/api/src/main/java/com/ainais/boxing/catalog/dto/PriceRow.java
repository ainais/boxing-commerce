package com.ainais.boxing.catalog.dto;

import java.time.Instant;

/** price_history 원본 한 행 (일별 최저가 계산용 projection) */
public record PriceRow(Instant capturedAt, int price) {
}
