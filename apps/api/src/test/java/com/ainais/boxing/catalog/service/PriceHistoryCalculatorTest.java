package com.ainais.boxing.catalog.service;

import com.ainais.boxing.catalog.dto.PricePointResponse;
import com.ainais.boxing.catalog.dto.PriceRow;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.time.ZoneId;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class PriceHistoryCalculatorTest {

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");
    /** 2026-10-21 11:00 KST */
    private static final Instant NOW = Instant.parse("2026-10-21T02:00:00Z");

    private static PriceRow row(String instant, int price) {
        return new PriceRow(Instant.parse(instant), price);
    }

    @Test
    void splitsDaysAtKstMidnightNotUtc() {
        List<PriceRow> rows = List.of(
                row("2026-10-20T14:59:59Z", 100), // 10/20 23:59:59 KST -> 어제
                row("2026-10-20T15:00:00Z", 90)); // 10/21 00:00:00 KST -> 오늘

        List<PricePointResponse> result = PriceHistoryCalculator.dailyLowest(rows, 90, NOW, KST);

        assertThat(result).containsExactly(new PricePointResponse(1, 100), new PricePointResponse(0, 90));
    }

    @Test
    void picksLowestPriceAcrossAllRowsOfTheSameDay() {
        List<PriceRow> rows = List.of(
                row("2026-10-19T01:00:00Z", 120),
                row("2026-10-19T05:00:00Z", 100),
                row("2026-10-19T09:00:00Z", 110),
                row("2026-10-21T01:00:00Z", 95));

        List<PricePointResponse> result = PriceHistoryCalculator.dailyLowest(rows, 95, NOW, KST);

        assertThat(result).containsExactly(new PricePointResponse(2, 100), new PricePointResponse(0, 95));
    }

    @Test
    void fillsTodayWithCurrentLowestWhenNoRowToday() {
        List<PriceRow> rows = List.of(row("2026-10-20T03:00:00Z", 110));

        List<PricePointResponse> result = PriceHistoryCalculator.dailyLowest(rows, 105, NOW, KST);

        assertThat(result).containsExactly(new PricePointResponse(1, 110), new PricePointResponse(0, 105));
    }

    @Test
    void returnsOnlyTodayWhenThereIsNoHistory() {
        assertThat(PriceHistoryCalculator.dailyLowest(List.of(), 77, NOW, KST))
                .containsExactly(new PricePointResponse(0, 77));
    }

    @Test
    void ignoresRowsOutsideThe30DayWindowAndInTheFuture() {
        List<PriceRow> rows = List.of(
                row("2026-09-21T14:59:59Z", 1),   // 09/21 23:59:59 KST -> 30일 전, 범위 밖
                row("2026-09-21T15:00:00Z", 200), // 09/22 00:00 KST -> 29일 전, 범위 안
                row("2026-10-22T00:00:00Z", 1));  // 미래

        List<PricePointResponse> result = PriceHistoryCalculator.dailyLowest(rows, 150, NOW, KST);

        assertThat(result).containsExactly(new PricePointResponse(29, 200), new PricePointResponse(0, 150));
    }

    @Test
    void ordersOldestFirstEndingWithToday() {
        List<PriceRow> rows = List.of(
                row("2026-10-21T01:00:00Z", 90),
                row("2026-10-18T01:00:00Z", 120),
                row("2026-10-20T01:00:00Z", 100));

        List<PricePointResponse> result = PriceHistoryCalculator.dailyLowest(rows, 90, NOW, KST);

        assertThat(result).extracting(PricePointResponse::daysAgo).containsExactly(3, 1, 0);
    }

    @Test
    void windowStartIsKstMidnight29DaysAgo() {
        // 오늘 10/21 KST -> 29일 전 09/22 00:00 KST = 09/21 15:00 UTC
        assertThat(PriceHistoryCalculator.windowStart(NOW, KST)).isEqualTo(Instant.parse("2026-09-21T15:00:00Z"));
    }
}
