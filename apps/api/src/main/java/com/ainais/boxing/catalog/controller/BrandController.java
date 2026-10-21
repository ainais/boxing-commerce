package com.ainais.boxing.catalog.controller;

import com.ainais.boxing.catalog.service.BrandService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "Catalog")
@RestController
@RequestMapping("/api/brands")
public class BrandController {

    private final BrandService brandService;

    public BrandController(BrandService brandService) {
        this.brandService = brandService;
    }

    @Operation(summary = "브랜드 이름 목록 (category를 주면 그 카테고리에 상품이 있는 브랜드만, 이름순)")
    @GetMapping
    public List<String> list(@RequestParam(required = false) String category) {
        return brandService.findNames(category);
    }
}
