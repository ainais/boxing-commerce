# BoxingEverything (web)

복싱용품 가격 비교 사이트의 프론트엔드입니다. 상품별 판매처 가격을 비교하고, 구매는 판매처 링크로 연결합니다(주문/결제 기능 없음).

> 현재는 `src/lib/mock/`의 **mock 데이터**로 동작합니다. 데이터 접근은 `src/lib/api.ts` 한 곳에 모여 있어, 이후 백엔드 API 연동 시 이 파일의 구현만 교체할 예정입니다.

## 스택

- Next.js (App Router, Cache Components) / React / TypeScript
- Tailwind CSS
- 패키지 매니저: pnpm
- 폰트: Pretendard (CDN)

## 실행 방법

```bash
pnpm install
pnpm dev      # http://localhost:3000
```

```bash
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

`NEXT_DIST_DIR` 환경변수로 빌드 산출물 경로를 바꿀 수 있습니다(기본값 `.next`).

## 주요 화면

| 경로 | 설명 |
| --- | --- |
| `/` | 인기 상품, 카테고리별 섹션 |
| `/products` | 검색·카테고리·브랜드·가격 필터, 정렬, 페이지네이션 (상태는 URL searchParams) |
| `/products/[id]` | 판매처별 가격 비교, 30일 가격 추이, 관련 상품 |
| `/go/[offerId]` | 판매처 이동용 redirect (추후 클릭 로그 기록 예정) |
