# 복싱의모든것 (web)

복싱용품 가격 비교 사이트의 프론트엔드입니다. 상품별 판매처 가격을 비교하고, 구매는 판매처 링크로 연결합니다(주문/결제 기능 없음).

> 데이터는 `apps/api`의 조회 API에서 가져옵니다. API 호출은 `src/lib/api.ts` 한 곳에 모여 있고, 서버 컴포넌트에서만 호출합니다.

## 스택

- Next.js (App Router, Cache Components) / React / TypeScript
- Tailwind CSS
- 패키지 매니저: pnpm
- 폰트: Pretendard (CDN)

## 실행 방법

API(`apps/api`, 기본 http://localhost:4001)를 먼저 띄운 뒤 web을 실행합니다.

```bash
pnpm install
pnpm dev      # http://localhost:4000
```

- API 주소는 환경변수 `API_BASE_URL`(기본값 `http://localhost:4001`)로 바꿉니다. `.env.example`을 참고해 `.env.local`을 만드세요.
- API가 꺼져 있으면 "데이터를 불러오지 못했습니다" 안내가 보입니다.
- 상품 이미지는 판매처 외부 주소(`goldenchamps.co.kr/web/product/**`)이며 `next.config.ts`의 `images.remotePatterns`에 허용돼 있습니다. 다른 판매처를 추가하면 여기에 호스트를 더해야 합니다.
- 배송비 표시는 `src/lib/format.ts` 한 곳에서 정합니다(0원이면 "판매처 확인").

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
| `/go/[offerId]` | 클릭 로그용 자리. 지금은 404만 돌려줍니다(판매처 링크는 offer url로 직접 이동) |
