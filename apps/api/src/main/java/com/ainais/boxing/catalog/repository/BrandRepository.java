package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.entity.Brand;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface BrandRepository extends JpaRepository<Brand, Long> {

    @Query("select b.name from Brand b order by b.name asc")
    List<String> findAllNames();

    /** 해당 카테고리에 상품이 있는 브랜드만 */
    @Query("""
            select distinct b.name
            from Product p
            join p.brand b
            join p.category c
            where c.slug = :categorySlug
            order by b.name asc
            """)
    List<String> findNamesByCategorySlug(@Param("categorySlug") String categorySlug);
}
