# boxing-commerce

**복싱의모든것**은 복싱용품 가격 비교 정보 제공 플랫폼입니다 (다나와 스타일). 주문/결제는 직접 처리하지 않고, 판매처 링크로 연결합니다.

## 구조

모노레포입니다.

- `apps/web` — Next.js, TypeScript, Tailwind CSS
- `apps/api` — Spring Boot (예정)

## 진행 상태

- [x] web 프론트엔드 (mock 데이터 기반 프로토타입)
  - 홈: 인기 상품, 카테고리별 섹션
  - 상품 목록: 검색, 카테고리·브랜드·가격 필터, 정렬, 페이지네이션
  - 상품 상세: 판매처별 가격 비교, 30일 가격 이력
  - 클릭아웃: 판매처 이동 시 내부 route를 거쳐 redirect
- [ ] DB 설계 (ERD)
- [ ] api 서버 (Spring Boot)
- [ ] 크롤링 수집
- [ ] web mock → API 연동

## 로드맵

1. 가격 비교
2. 주문 처리 (PG 테스트 모드)

## 설계 문서

- [DB 설계 (ERD)](docs/erd.md)

## 실행 방법

```bash
cd apps/web
pnpm install
pnpm dev
```
