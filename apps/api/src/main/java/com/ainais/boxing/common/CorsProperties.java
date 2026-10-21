package com.ainais.boxing.common;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

/** app.cors.allowed-origins. 기본값은 빈 목록(허용 없음) */
@ConfigurationProperties(prefix = "app.cors")
public record CorsProperties(List<String> allowedOrigins) {

    public CorsProperties {
        allowedOrigins = allowedOrigins == null
                ? List.of()
                : allowedOrigins.stream().map(String::trim).filter(s -> !s.isEmpty()).toList();
    }
}
