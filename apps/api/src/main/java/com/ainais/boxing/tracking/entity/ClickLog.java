package com.ainais.boxing.tracking.entity;

import com.ainais.boxing.catalog.entity.Offer;
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

/** 클릭 로그 매핑만 있다. 기록(쓰기)과 /go 연동은 아직 구현하지 않았다. */
@Entity
@Table(name = "click_log")
public class ClickLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "offer_id", nullable = false)
    private Offer offer;

    @Column(name = "clicked_at", nullable = false)
    private Instant clickedAt;

    @Column(name = "referrer", length = 1000)
    private String referrer;

    @Column(name = "visitor_hash", length = 64)
    private String visitorHash;

    protected ClickLog() {
    }
}
