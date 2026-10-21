package com.ainais.boxing.catalog.service;

import com.ainais.boxing.catalog.repository.BrandRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional(readOnly = true)
public class BrandService {

    private final BrandRepository brandRepository;

    public BrandService(BrandRepository brandRepository) {
        this.brandRepository = brandRepository;
    }

    /** category가 없으면 전체 브랜드, 있으면 그 카테고리에 상품이 있는 브랜드 (이름순) */
    public List<String> findNames(String categorySlug) {
        if (categorySlug == null || categorySlug.isBlank()) {
            return brandRepository.findAllNames();
        }
        return brandRepository.findNamesByCategorySlug(categorySlug.trim());
    }
}
