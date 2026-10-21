package com.ainais.boxing.catalog.repository;

import com.ainais.boxing.catalog.dto.OfferResponse;
import com.ainais.boxing.catalog.entity.Offer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface OfferRepository extends JpaRepository<Offer, Long> {

    /** 가격 낮은 순, 같으면 배송비 낮은 순 (최종 동점은 id) */
    @Query("""
            select new com.ainais.boxing.catalog.dto.OfferResponse(o.id, s.name, o.price, o.shippingFee, o.url)
            from Offer o
            join o.seller s
            where o.product.id = :productId
            order by o.price asc, o.shippingFee asc, o.id asc
            """)
    List<OfferResponse> findByProductIdOrdered(@Param("productId") Long productId);
}
