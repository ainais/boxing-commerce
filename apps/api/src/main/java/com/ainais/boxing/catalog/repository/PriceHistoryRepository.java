package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.dto.PriceRow;
import com.ainais.boxing.catalog.entity.PriceHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.List;

public interface PriceHistoryRepository extends JpaRepository<PriceHistory, Long> {

    /** 상품의 모든 offer에 대한 since 이후 가격 기록 (일별 최저가는 서비스에서 계산) */
    @Query("""
            select new com.ainais.boxing.catalog.dto.PriceRow(ph.capturedAt, ph.price)
            from PriceHistory ph
            where ph.offer.product.id = :productId
              and ph.capturedAt >= :since
            """)
    List<PriceRow> findRowsSince(@Param("productId") Long productId, @Param("since") Instant since);
}
