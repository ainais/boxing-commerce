package com.ainais.boxing.catalog.service;

import com.ainais.boxing.catalog.dto.OfferResponse;
import com.ainais.boxing.catalog.dto.PricePointResponse;
import com.ainais.boxing.catalog.dto.PriceRow;
import com.ainais.boxing.catalog.dto.ProductDetailResponse;
import com.ainais.boxing.catalog.dto.ProductHead;
import com.ainais.boxing.catalog.dto.ProductSummaryResponse;
import com.ainais.boxing.catalog.repository.OfferRepository;
import com.ainais.boxing.catalog.repository.PriceHistoryRepository;
import com.ainais.boxing.catalog.repository.ProductQueryRepository;
import com.ainais.boxing.catalog.repository.ProductRepository;
import com.ainais.boxing.common.ApiException;
import com.ainais.boxing.common.PageResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;

@Service
@Transactional(readOnly = true)
public class ProductService {

    /** 날짜 경계 기준 시간대 (가격 이력의 일별 구분) */
    static final ZoneId ZONE = ZoneId.of("Asia/Seoul");
    private static final Duration POPULAR_WINDOW = Duration.ofDays(30);
    public static final int DEFAULT_RELATED_LIMIT = 4;
    public static final int MAX_RELATED_LIMIT = 12;

    private final ProductRepository productRepository;
    private final ProductQueryRepository productQueryRepository;
    private final OfferRepository offerRepository;
    private final PriceHistoryRepository priceHistoryRepository;
    private final Clock clock;

    public ProductService(
            ProductRepository productRepository,
            ProductQueryRepository productQueryRepository,
            OfferRepository offerRepository,
            PriceHistoryRepository priceHistoryRepository,
            Clock clock) {
        this.productRepository = productRepository;
        this.productQueryRepository = productQueryRepository;
        this.offerRepository = offerRepository;
        this.priceHistoryRepository = priceHistoryRepository;
        this.clock = clock;
    }

    /** 쿼리 2개: count + 목록 */
    public PageResponse<ProductSummaryResponse> search(ProductSearchCriteria criteria) {
        long total = productQueryRepository.count(criteria);
        List<ProductSummaryResponse> items = total == 0 || criteria.offset() >= total
                ? List.of()
                : productQueryRepository.search(criteria, popularSince());
        return new PageResponse<>(items, total, criteria.page(), criteria.size());
    }

    /** 쿼리 3개: 상품 기본 정보, offers, 가격 기록 */
    public ProductDetailResponse getDetail(Long id) {
        ProductHead head = productRepository.findHeadById(id)
                .orElseThrow(() -> ApiException.notFound("상품을 찾을 수 없습니다. id=" + id));
        List<OfferResponse> offers = offerRepository.findByProductIdOrdered(id);
        if (offers.isEmpty()) {
            throw ApiException.notFound("판매처 정보가 없는 상품입니다. id=" + id);
        }
        OfferResponse lowestOffer = offers.get(0);

        Instant now = clock.instant();
        List<PriceRow> rows = priceHistoryRepository.findRowsSince(id, PriceHistoryCalculator.windowStart(now, ZONE));
        List<PricePointResponse> history =
                PriceHistoryCalculator.dailyLowest(rows, lowestOffer.price(), now, ZONE);

        return new ProductDetailResponse(
                head.id(), head.name(), head.brand(), head.categorySlug(), head.categoryName(),
                head.imageUrl(), lowestOffer.price(), lowestOffer, offers, history);
    }

    /** 같은 카테고리의 다른 상품 (popular 규칙). 쿼리 3개: 기본 정보, count, 목록 */
    public List<ProductSummaryResponse> getRelated(Long id, int limit) {
        if (limit < 1 || limit > MAX_RELATED_LIMIT) {
            throw ApiException.invalidParameter("limit은 1 이상 " + MAX_RELATED_LIMIT + " 이하여야 합니다.");
        }
        ProductHead head = productRepository.findHeadById(id)
                .orElseThrow(() -> ApiException.notFound("상품을 찾을 수 없습니다. id=" + id));
        return search(ProductSearchCriteria.related(head.categorySlug(), id, limit)).items();
    }

    private OffsetDateTime popularSince() {
        return OffsetDateTime.ofInstant(clock.instant().minus(POPULAR_WINDOW), ZoneOffset.UTC);
    }
}
