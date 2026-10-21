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
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Clock;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    private static final Instant NOW = Instant.parse("2026-10-21T02:00:00Z");

    @Mock
    ProductRepository productRepository;
    @Mock
    ProductQueryRepository productQueryRepository;
    @Mock
    OfferRepository offerRepository;
    @Mock
    PriceHistoryRepository priceHistoryRepository;

    ProductService service;

    private static final ProductHead HEAD =
            new ProductHead(1L, "프로 스파링 글러브", "Everlast", "gloves", "글러브", null);

    @BeforeEach
    void setUp() {
        service = new ProductService(productRepository, productQueryRepository, offerRepository,
                priceHistoryRepository, Clock.fixed(NOW, ZoneOffset.UTC));
    }

    @Test
    void detailIsNotFoundWhenProductMissing() {
        when(productRepository.findHeadById(9L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.getDetail(9L))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("NOT_FOUND"));
    }

    @Test
    void detailIsNotFoundWhenProductHasNoOffers() {
        when(productRepository.findHeadById(1L)).thenReturn(Optional.of(HEAD));
        when(offerRepository.findByProductIdOrdered(1L)).thenReturn(List.of());

        assertThatThrownBy(() -> service.getDetail(1L)).isInstanceOf(ApiException.class);
        verify(priceHistoryRepository, never()).findRowsSince(any(), any());
    }

    @Test
    void detailComposesLowestOfferAndDailyHistoryEndingAtCurrentLowest() {
        OfferResponse lowest = new OfferResponse(11L, "11st", 87500, 3500, "https://example.com/11st/p01");
        OfferResponse other = new OfferResponse(10L, "Coupang", 89000, 0, "https://example.com/coupang/p01");
        when(productRepository.findHeadById(1L)).thenReturn(Optional.of(HEAD));
        when(offerRepository.findByProductIdOrdered(1L)).thenReturn(List.of(lowest, other));
        when(priceHistoryRepository.findRowsSince(eq(1L), eq(Instant.parse("2026-09-21T15:00:00Z"))))
                .thenReturn(List.of(new PriceRow(Instant.parse("2026-10-20T03:00:00Z"), 91000)));

        ProductDetailResponse detail = service.getDetail(1L);

        assertThat(detail.lowestOffer()).isEqualTo(lowest);
        assertThat(detail.lowestPrice()).isEqualTo(87500);
        assertThat(detail.offers()).containsExactly(lowest, other);
        assertThat(detail.priceHistory())
                .containsExactly(new PricePointResponse(1, 91000), new PricePointResponse(0, 87500));
    }

    @Test
    void searchSkipsListQueryWhenNothingMatches() {
        ProductSearchCriteria criteria = ProductSearchCriteria.of("zzz", null, null, null, null, null, 1, 12);
        when(productQueryRepository.count(criteria)).thenReturn(0L);

        PageResponse<ProductSummaryResponse> page = service.search(criteria);

        assertThat(page.items()).isEmpty();
        assertThat(page.total()).isZero();
        verify(productQueryRepository, never()).search(any(), any());
    }

    @Test
    void searchSkipsListQueryWhenPageIsBeyondTheEnd() {
        ProductSearchCriteria criteria = ProductSearchCriteria.of(null, null, null, null, null, null, 9, 12);
        when(productQueryRepository.count(criteria)).thenReturn(28L);

        PageResponse<ProductSummaryResponse> page = service.search(criteria);

        assertThat(page.items()).isEmpty();
        assertThat(page.total()).isEqualTo(28);
        assertThat(page.page()).isEqualTo(9);
        verify(productQueryRepository, never()).search(any(), any());
    }

    @Test
    void searchPassesThirtyDayWindowForPopularSort() {
        ProductSearchCriteria criteria = ProductSearchCriteria.of(null, null, null, null, null, "popular", 1, 12);
        when(productQueryRepository.count(criteria)).thenReturn(1L);
        when(productQueryRepository.search(eq(criteria), any())).thenReturn(List.of());

        service.search(criteria);

        verify(productQueryRepository).search(criteria,
                OffsetDateTime.ofInstant(Instant.parse("2026-09-21T02:00:00Z"), ZoneOffset.UTC));
    }

    @Test
    void relatedRejectsOutOfRangeLimit() {
        assertThatThrownBy(() -> service.getRelated(1L, 0)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.getRelated(1L, ProductService.MAX_RELATED_LIMIT + 1))
                .isInstanceOf(ApiException.class);
    }

    @Test
    void relatedIsNotFoundWhenProductMissing() {
        when(productRepository.findHeadById(9L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.getRelated(9L, 4))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCode()).isEqualTo("NOT_FOUND"));
    }

    @Test
    void relatedSearchesSameCategoryExcludingSelfWithPopularSort() {
        when(productRepository.findHeadById(1L)).thenReturn(Optional.of(HEAD));
        ProductSearchCriteria expected = ProductSearchCriteria.related("gloves", 1L, 4);
        when(productQueryRepository.count(expected)).thenReturn(0L);

        List<ProductSummaryResponse> result = service.getRelated(1L, 4);

        assertThat(result).isEmpty();
        verify(productQueryRepository).count(expected);
    }
}
