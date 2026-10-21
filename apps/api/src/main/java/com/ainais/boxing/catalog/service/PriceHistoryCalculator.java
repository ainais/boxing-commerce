package com.ainais.boxing.catalog.service;

import com.ainais.boxing.catalog.dto.PricePointResponse;
import com.ainais.boxing.catalog.dto.PriceRow;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** price_history 원본 행을 일별 최저가({daysAgo, price})로 가공하는 순수 로직 */
final class PriceHistoryCalculator {

    static final int DAYS = 30;

    private PriceHistoryCalculator() {
    }

    /** 조회 시작 시각: 오늘(zone 기준) 0시에서 DAYS-1일 전 0시 */
    static Instant windowStart(Instant now, ZoneId zone) {
        LocalDate today = now.atZone(zone).toLocalDate();
        return today.minusDays(DAYS - 1).atStartOfDay(zone).toInstant();
    }

    /**
     * 날짜 경계는 zone(Asia/Seoul) 기준이다.
     * 같은 날의 모든 기록(모든 offer) 중 최저가를 그날의 값으로 쓰고, 기록이 없는 날은 건너뛴다.
     * 오늘 기록이 없으면 현재 최저가(currentLowest)를 오늘 값으로 채운다.
     * 결과는 오래된 날부터(daysAgo 큰 값 → 0) 정렬된다.
     */
    static List<PricePointResponse> dailyLowest(List<PriceRow> rows, int currentLowest, Instant now, ZoneId zone) {
        LocalDate today = now.atZone(zone).toLocalDate();
        Map<Integer, Integer> lowestByDaysAgo = new TreeMap<>(java.util.Comparator.reverseOrder());
        for (PriceRow row : rows) {
            LocalDate date = row.capturedAt().atZone(zone).toLocalDate();
            long daysAgo = ChronoUnit.DAYS.between(date, today);
            if (daysAgo < 0 || daysAgo >= DAYS) {
                continue;
            }
            lowestByDaysAgo.merge((int) daysAgo, row.price(), Math::min);
        }
        lowestByDaysAgo.putIfAbsent(0, currentLowest);

        List<PricePointResponse> result = new ArrayList<>(lowestByDaysAgo.size());
        lowestByDaysAgo.forEach((daysAgo, price) -> result.add(new PricePointResponse(daysAgo, price)));
        return result;
    }
}
