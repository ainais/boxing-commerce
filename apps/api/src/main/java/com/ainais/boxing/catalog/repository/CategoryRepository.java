package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.dto.CategoryResponse;
import com.ainais.boxing.catalog.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface CategoryRepository extends JpaRepository<Category, Long> {

    @Query("""
            select new com.ainais.boxing.catalog.dto.CategoryResponse(c.slug, c.name)
            from Category c
            order by c.sortOrder asc, c.id asc
            """)
    List<CategoryResponse> findAllOrdered();
}
