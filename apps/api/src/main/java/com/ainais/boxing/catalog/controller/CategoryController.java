package com.ainais.boxing.catalog.controller;

import com.ainais.boxing.catalog.dto.CategoryResponse;
import com.ainais.boxing.catalog.service.CategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "Catalog")
@RestController
@RequestMapping("/api/categories")
public class CategoryController {

    private final CategoryService categoryService;

    public CategoryController(CategoryService categoryService) {
        this.categoryService = categoryService;
    }

    @Operation(summary = "카테고리 목록 (sort_order 순)")
    @GetMapping
    public List<CategoryResponse> list() {
        return categoryService.findAll();
    }
}
