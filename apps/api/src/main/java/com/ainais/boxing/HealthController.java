package com.ainais.boxing;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class HealthController {

    public record HealthResponse(String status) {
    }

    // DB에 접근하지 않는 단순 생존 확인용 엔드포인트
    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse("ok");
    }
}
