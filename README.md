# 복싱의모든것 (boxing-commerce)

복싱용품 가격 비교 서비스입니다.

- 글러브, 헤드기어, 핸드랩 등 복싱용품의 판매처별 가격을 한눈에 비교합니다 (다나와 스타일).
- 주문·결제는 직접 처리하지 않고, 판매처 링크로 연결합니다.
- web과 api를 한 레포에서 관리하는 monorepo입니다.

## 핵심 기능

web은 **mock 데이터 기반 프로토타입**입니다.

- 홈: 인기 상품, 카테고리별 섹션
- 상품 목록: 검색, 카테고리·브랜드·가격 필터, 정렬, 페이지네이션 (상태는 URL searchParams)
- 상품 상세: 판매처별 가격 비교, 30일 가격 이력
- 클릭아웃: 내부 `/go/[offerId]` route를 거쳐 판매처로 redirect
- 404 및 검색 결과 없음 화면

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| web | Next.js 16.4.2 (App Router), React 19.3.0, TypeScript 5, Tailwind CSS 4, pnpm |
| api | Java 21, Spring Boot 4.1.1, Spring Data JPA (Hibernate), Flyway, PostgreSQL, springdoc-openapi 3.1.1 (Swagger UI), Gradle 8.14.6 |

## 구조

```text
boxing-commerce/
├── apps/
│   ├── web/    Next.js 프론트엔드
│   └── api/    Spring Boot 백엔드
├── docs/       설계 문서 (ERD)
└── brand/      브랜드 원본 이미지
```

## 설계 결정

- 주문·결제 없이 판매처로 연결합니다. 이동은 내부 `/go/[offerId]` route를 거쳐 redirect하며, 클릭 로그는 이 지점에서 기록할 예정입니다.
- 스키마의 단일 출처는 Flyway SQL 마이그레이션입니다. Hibernate는 `ddl-auto=validate`로 엔티티와 스키마가 일치하는지만 검증합니다.
- 시드 데이터는 dev 프로파일에서만 적용합니다 (`db/seed`, repeatable migration). prod는 DB 접속 정보를 환경변수로만 주입합니다.
- 크롤링 수집 원본(`raw_listing`)과 판매처별 현재 상태(`offer`)를 분리하는 설계입니다. 크롤링 단계에서 구현할 예정입니다.
- 금액은 KRW 정수로, 시각은 `timestamptz`로 저장합니다.
- Java 21, Spring Boot 4.1.x를 사용합니다.

자세한 내용은 [DB 설계 (ERD)](docs/erd.md)를 참고하세요.

## 진행 상태

- [x] web 프론트엔드 (mock 기반 프로토타입)
- [x] ERD 설계
- [x] api 뼈대와 DB 마이그레이션·시드 (health 엔드포인트, Flyway V1 핵심 테이블 7개, dev 전용 시드)
- [ ] 조회 API
- [ ] web mock → API 연동
- [ ] 클릭 로그 기록
- [ ] 크롤링 수집

web과 api는 아직 연결되어 있지 않습니다.

## 실행 방법

### web

```bash
cd apps/web
pnpm install
pnpm dev
```

### api

JDK 21이 필요합니다.

1. `apps/api/config/application-dev.example.yml`을 같은 폴더의 `application-dev.yml`로 복사하고 DB 접속 정보를 채웁니다.
2. `apps/api`에서 실행합니다.

```bash
./gradlew bootRun --args='--spring.profiles.active=dev'
```

- 서버 기본 포트는 8080입니다.
- health 확인: http://localhost:8080/api/health
- Swagger UI: http://localhost:8080/swagger-ui/index.html

배포(prod)는 환경변수 `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`로 접속 정보를 주입합니다.

## 로드맵

1. 1단계: 가격 비교
2. 2단계: 주문 처리 (PG 테스트 모드)
