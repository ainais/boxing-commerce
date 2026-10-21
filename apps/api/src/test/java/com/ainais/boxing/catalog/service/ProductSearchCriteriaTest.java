package com.ainais.boxing.catalog.service;

import com.ainais.boxing.common.ApiException;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ProductSearchCriteriaTest {

    private static ProductSearchCriteria of(Integer min, Integer max, String sort, int page, int size) {
        return ProductSearchCriteria.of(null, null, null, min, max, sort, page, size);
    }

    @Test
    void appliesDefaults() {
        ProductSearchCriteria c = ProductSearchCriteria.of(null, null, null, null, null, null, 1, 12);

        assertThat(c.sort()).isEqualTo(ProductSort.LOWEST_PRICE);
        assertThat(c.q()).isEmpty();
        assertThat(c.category()).isNull();
        assertThat(c.brands()).isEmpty();
        assertThat(c.offset()).isZero();
    }

    @Test
    void trimsAndCleansInputs() {
        ProductSearchCriteria c = ProductSearchCriteria.of(
                "  글러브 ", " gloves ", List.of(" Venum ", "", "Venum", "Title"), null, null, "name", 3, 10);

        assertThat(c.q()).isEqualTo("글러브");
        assertThat(c.category()).isEqualTo("gloves");
        assertThat(c.brands()).containsExactly("Venum", "Title");
        assertThat(c.offset()).isEqualTo(20);
    }

    @Test
    void rejectsInvalidValues() {
        assertThatThrownBy(() -> of(-1, null, null, 1, 12)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(null, -1, null, 1, 12)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(5000, 1000, null, 1, 12)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(null, null, "bogus", 1, 12)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(null, null, null, 0, 12)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(null, null, null, 1, 0)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> of(null, null, null, 1, 51)).isInstanceOf(ApiException.class);
    }

    @Test
    void acceptsBoundaryValues() {
        assertThat(of(0, 0, "popular", 1, 50).size()).isEqualTo(50);
        assertThat(of(1000, 1000, "priceDesc", 1, 1).sort()).isEqualTo(ProductSort.PRICE_DESC);
    }

    @Test
    void normalizesLikeTheFrontend() {
        assertThat(ProductSearchCriteria.normalize(" Pro  Spar ring\t")).isEqualTo("prosparring");
        assertThat(ProductSearchCriteria.likePattern("100%_a!")).isEqualTo("%100!%!_a!!%");
    }

    @Test
    void everySortOrderEndsWithIdAscendingForStablePaging() {
        for (ProductSort sort : ProductSort.values()) {
            assertThat(sort.orderBy()).endsWith("p.id ASC");
        }
    }

    @Test
    void popularSortUsesClicksThenOfferCountThenId() {
        assertThat(ProductSort.POPULAR.orderBy())
                .isEqualTo("COALESCE(pop.clicks, 0) DESC, agg.offer_count DESC, p.id ASC");
        assertThat(ProductSort.from("popular")).isEqualTo(ProductSort.POPULAR);
    }

    @Test
    void relatedCriteriaUsesPopularSortAndExcludesSelf() {
        ProductSearchCriteria c = ProductSearchCriteria.related("gloves", 7L, 4);

        assertThat(c.sort()).isEqualTo(ProductSort.POPULAR);
        assertThat(c.category()).isEqualTo("gloves");
        assertThat(c.excludeProductId()).isEqualTo(7L);
        assertThat(c.size()).isEqualTo(4);
        assertThat(c.page()).isEqualTo(1);
    }
}
