package com.ainais.boxing.catalog.controller;

import com.ainais.boxing.catalog.dto.CategoryResponse;
import com.ainais.boxing.catalog.dto.OfferResponse;
import com.ainais.boxing.catalog.dto.PricePointResponse;
import com.ainais.boxing.catalog.dto.ProductDetailResponse;
import com.ainais.boxing.catalog.dto.ProductSummaryResponse;
import com.ainais.boxing.catalog.service.BrandService;
import com.ainais.boxing.catalog.service.CategoryService;
import com.ainais.boxing.catalog.service.ProductSearchCriteria;
import com.ainais.boxing.catalog.service.ProductService;
import com.ainais.boxing.catalog.service.ProductSort;
import com.ainais.boxing.common.ApiException;
import com.ainais.boxing.common.PageResponse;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = {CategoryController.class, BrandController.class, ProductController.class})
class CatalogControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockitoBean
    CategoryService categoryService;

    @MockitoBean
    BrandService brandService;

    @MockitoBean
    ProductService productService;

    private static ProductSummaryResponse summary(long id) {
        return new ProductSummaryResponse(id, "프로 스파링 글러브", "Everlast", "gloves", "글러브", null,
                87500, new OfferResponse(11L, "11st", 87500, 3500, "https://example.com/11st/p01"), 3);
    }

    @Test
    void categoriesReturnsSlugAndName() throws Exception {
        when(categoryService.findAll()).thenReturn(List.of(new CategoryResponse("gloves", "글러브")));

        mockMvc.perform(get("/api/categories"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].slug").value("gloves"))
                .andExpect(jsonPath("$[0].name").value("글러브"));
    }

    @Test
    void brandsPassesCategoryAndReturnsNames() throws Exception {
        when(brandService.findNames("gloves")).thenReturn(List.of("Everlast", "Venum"));

        mockMvc.perform(get("/api/brands").param("category", "gloves"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0]").value("Everlast"))
                .andExpect(jsonPath("$[1]").value("Venum"));
    }

    @Test
    void productsReturnsPageShapeWithDefaults() throws Exception {
        when(productService.search(any())).thenReturn(new PageResponse<>(List.of(summary(1L)), 28, 1, 12));

        mockMvc.perform(get("/api/products"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(28))
                .andExpect(jsonPath("$.page").value(1))
                .andExpect(jsonPath("$.size").value(12))
                .andExpect(jsonPath("$.items[0].id").value(1))
                .andExpect(jsonPath("$.items[0].brand").value("Everlast"))
                .andExpect(jsonPath("$.items[0].categorySlug").value("gloves"))
                .andExpect(jsonPath("$.items[0].lowestPrice").value(87500))
                .andExpect(jsonPath("$.items[0].lowestOffer.seller").value("11st"))
                .andExpect(jsonPath("$.items[0].offerCount").value(3));

        ArgumentCaptor<ProductSearchCriteria> captor = ArgumentCaptor.forClass(ProductSearchCriteria.class);
        verify(productService).search(captor.capture());
        assertThat(captor.getValue().sort()).isEqualTo(ProductSort.LOWEST_PRICE);
        assertThat(captor.getValue().page()).isEqualTo(1);
        assertThat(captor.getValue().size()).isEqualTo(12);
    }

    @Test
    void productsBindsFilters() throws Exception {
        when(productService.search(any())).thenReturn(new PageResponse<>(List.of(), 0, 2, 20));

        mockMvc.perform(get("/api/products")
                        .param("q", "글러브")
                        .param("category", "gloves")
                        .param("brand", "Everlast")
                        .param("brand", "Venum")
                        .param("minPrice", "1000")
                        .param("maxPrice", "90000")
                        .param("sort", "popular")
                        .param("page", "2")
                        .param("size", "20"))
                .andExpect(status().isOk());

        ArgumentCaptor<ProductSearchCriteria> captor = ArgumentCaptor.forClass(ProductSearchCriteria.class);
        verify(productService).search(captor.capture());
        ProductSearchCriteria c = captor.getValue();
        assertThat(c.q()).isEqualTo("글러브");
        assertThat(c.category()).isEqualTo("gloves");
        assertThat(c.brands()).containsExactly("Everlast", "Venum");
        assertThat(c.minPrice()).isEqualTo(1000);
        assertThat(c.maxPrice()).isEqualTo(90000);
        assertThat(c.sort()).isEqualTo(ProductSort.POPULAR);
        assertThat(c.page()).isEqualTo(2);
        assertThat(c.size()).isEqualTo(20);
    }

    @Test
    void productsRejectsInvalidParameters() throws Exception {
        String[][] bad = {
                {"sort", "bogus"},
                {"minPrice", "-1"},
                {"maxPrice", "-5"},
                {"size", "51"},
                {"size", "0"},
                {"page", "0"},
                {"minPrice", "abc"},
        };
        for (String[] p : bad) {
            mockMvc.perform(get("/api/products").param(p[0], p[1]))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.code").value("INVALID_PARAMETER"))
                    .andExpect(jsonPath("$.message").isNotEmpty());
        }
    }

    @Test
    void productsRejectsMinPriceGreaterThanMaxPrice() throws Exception {
        mockMvc.perform(get("/api/products").param("minPrice", "10000").param("maxPrice", "5000"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_PARAMETER"));
    }

    @Test
    void detailReturnsOffersAndPriceHistory() throws Exception {
        OfferResponse lowest = new OfferResponse(11L, "11st", 87500, 3500, "https://example.com/11st/p01");
        when(productService.getDetail(1L)).thenReturn(new ProductDetailResponse(
                1L, "프로 스파링 글러브", "Everlast", "gloves", "글러브", null, 87500, lowest,
                List.of(lowest, new OfferResponse(10L, "Coupang", 89000, 0, "https://example.com/coupang/p01")),
                List.of(new PricePointResponse(1, 91000), new PricePointResponse(0, 87500))));

        mockMvc.perform(get("/api/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.lowestPrice").value(87500))
                .andExpect(jsonPath("$.lowestOffer.id").value(11))
                .andExpect(jsonPath("$.offers[0].seller").value("11st"))
                .andExpect(jsonPath("$.offers[1].seller").value("Coupang"))
                .andExpect(jsonPath("$.priceHistory[0].daysAgo").value(1))
                .andExpect(jsonPath("$.priceHistory[1].daysAgo").value(0))
                .andExpect(jsonPath("$.priceHistory[1].price").value(87500));
    }

    @Test
    void detailReturns404ForUnknownProduct() throws Exception {
        when(productService.getDetail(999L)).thenThrow(ApiException.notFound("상품을 찾을 수 없습니다. id=999"));

        mockMvc.perform(get("/api/products/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("NOT_FOUND"))
                .andExpect(jsonPath("$.message").isNotEmpty());
    }

    @Test
    void detailRejectsNonNumericId() throws Exception {
        mockMvc.perform(get("/api/products/p01"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_PARAMETER"));
    }

    @Test
    void relatedUsesDefaultLimitAndReturnsList() throws Exception {
        when(productService.getRelated(eq(1L), eq(4))).thenReturn(List.of(summary(2L), summary(3L)));

        mockMvc.perform(get("/api/products/1/related"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].id").value(2));
    }

    @Test
    void relatedReturns404ForUnknownProduct() throws Exception {
        when(productService.getRelated(eq(999L), eq(4))).thenThrow(ApiException.notFound("상품을 찾을 수 없습니다."));

        mockMvc.perform(get("/api/products/999/related"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }

    @Test
    void unknownPathReturns404WithApiError() throws Exception {
        mockMvc.perform(get("/api/nothing-here"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("NOT_FOUND"));
    }
}
