package com.ainais.boxing.catalog.controller;

import com.ainais.boxing.catalog.dto.ProductDetailResponse;
import com.ainais.boxing.catalog.dto.ProductSummaryResponse;
import com.ainais.boxing.catalog.service.ProductSearchCriteria;
import com.ainais.boxing.catalog.service.ProductService;
import com.ainais.boxing.common.PageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "Catalog")
@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final ProductService productService;

    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    @Operation(summary = "상품 목록 (검색, 필터, 정렬, 페이지네이션)")
    @GetMapping
    public PageResponse<ProductSummaryResponse> list(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String category,
            @RequestParam(name = "brand", required = false) List<String> brands,
            @RequestParam(required = false) Integer minPrice,
            @RequestParam(required = false) Integer maxPrice,
            @RequestParam(required = false) String sort,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "" + ProductSearchCriteria.DEFAULT_SIZE) int size) {
        return productService.search(
                ProductSearchCriteria.of(q, category, brands, minPrice, maxPrice, sort, page, size));
    }

    @Operation(summary = "상품 상세 (판매처별 가격, 최근 30일 가격 이력)")
    @GetMapping("/{id}")
    public ProductDetailResponse detail(@PathVariable Long id) {
        return productService.getDetail(id);
    }

    @Operation(summary = "관련 상품 (같은 카테고리의 다른 상품, 인기순)")
    @GetMapping("/{id}/related")
    public List<ProductSummaryResponse> related(
            @PathVariable Long id,
            @RequestParam(defaultValue = "" + ProductService.DEFAULT_RELATED_LIMIT) int limit) {
        return productService.getRelated(id, limit);
    }
}
