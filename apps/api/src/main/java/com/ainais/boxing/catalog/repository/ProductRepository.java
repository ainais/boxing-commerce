package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.dto.ProductHead;
import com.ainais.boxing.catalog.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface ProductRepository extends JpaRepository<Product, Long> {

    @Query("""
            select new com.ainais.boxing.catalog.dto.ProductHead(p.id, p.name, b.name, c.slug, c.name, p.imageUrl)
            from Product p
            join p.brand b
            join p.category c
            where p.id = :id
            """)
    Optional<ProductHead> findHeadById(@Param("id") Long id);
}
