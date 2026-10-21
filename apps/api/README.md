# boxing-api

복싱의모든것 백엔드 (Spring Boot).

## 스택

- Java 21 (Gradle toolchain이 설치된 JDK 21을 자동 감지), Spring Boot 4.1, Gradle
- Spring Web, Data JPA, Validation, Flyway, PostgreSQL, springdoc-openapi

## 프로파일

- 기본(프로파일 없음)·prod: `db/migration`만 적용합니다.
- dev: `src/main/resources/application-dev.yml`(추적됨)이 `db/seed`(데모 시드)를 추가로 적용합니다.
- DB 접속 정보는 `config/application-dev.yml`(git 제외)에 둡니다. 같은 프로파일의 두 파일은 합쳐지고 `config/` 쪽이 우선합니다.
- 배포(prod)는 `config/` 파일 대신 환경변수 `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`로 주입합니다. prod에서 Swagger UI와 API 문서는 기본 비활성이고 `SWAGGER_ENABLED=true`로 켭니다.

## 로컬 실행

1. `config/application-dev.example.yml`을 같은 폴더의 `application-dev.yml`로 복사해 DB 접속 정보를 채웁니다.
2. `apps/api`에서 `./gradlew bootRun --args='--spring.profiles.active=dev'`

JDK 21이 설치되어 있어야 합니다. Swagger UI는 `/swagger-ui.html`입니다.

## 현재 상태

- `GET /api/health`와 Flyway 마이그레이션 V1(핵심 7개 테이블), dev 시드 데이터가 있습니다. 도메인 API는 아직 없습니다.
