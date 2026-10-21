package com.ainais.boxing.catalog.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "offer")
public class Offer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "seller_id", nullable = false)
    private Seller seller;

    @Column(name = "external_id", nullable = false, length = 100)
    private String externalId;

    @Column(name = "url", nullable = false, length = 1000)
    private String url;

    @Column(name = "price", nullable = false)
    private int price;

    @Column(name = "shipping_fee", nullable = false)
    private int shippingFee;

    @Column(name = "in_stock", nullable = false)
    private boolean inStock;

    @Column(name = "last_seen_at", nullable = false)
    private Instant lastSeenAt;

    protected Offer() {
    }
}
