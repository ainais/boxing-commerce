/** Suspense fallback용 스켈레톤 모음. 실제 컴포넌트와 같은 크기를 잡아 레이아웃 점프를 줄인다. */

const bar = "animate-pulse rounded bg-gray-200";

export function ProductCardSkeleton() {
  return (
    <div
      className="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white"
      aria-hidden="true"
    >
      <div className={`aspect-square w-full ${bar} rounded-none`} />
      <div className="flex flex-col gap-2 p-3">
        <div className={`h-3 w-1/3 ${bar}`} />
        <div className={`h-4 w-full ${bar}`} />
        <div className={`h-4 w-2/3 ${bar}`} />
        <div className={`mt-3 h-6 w-1/2 ${bar}`} />
        <div className={`h-3 w-3/4 ${bar}`} />
      </div>
    </div>
  );
}

/** ProductGrid와 같은 그리드. 로딩 중임을 스크린리더에도 알린다 */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
      role="status"
      aria-label="불러오는 중"
    >
      {Array.from({ length: count }, (_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}

/** 홈 섹션: 제목 자리 + 카드 그리드 */
export function SectionSkeleton({ count = 4 }: { count?: number }) {
  return (
    <section className="mb-10">
      <div className={`mb-4 h-7 w-28 ${bar}`} aria-hidden="true" />
      <ProductGridSkeleton count={count} />
    </section>
  );
}

/** 헤더 카테고리 메뉴 자리(메뉴 한 줄 높이 h-10를 유지) */
export function CategoryNavSkeleton() {
  return (
    <div className="flex h-10 items-center gap-5" aria-hidden="true">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className={`h-4 w-14 ${bar}`} />
      ))}
    </div>
  );
}

export function FilterPanelSkeleton() {
  return (
    <aside className="lg:w-56 lg:shrink-0" aria-hidden="true">
      <div className="hidden space-y-5 rounded-lg border border-gray-200 bg-white p-4 lg:block">
        {[7, 5, 2].map((rows, i) => (
          <div key={i} className="space-y-2">
            <div className={`h-4 w-16 ${bar}`} />
            {Array.from({ length: rows }, (_, j) => (
              <div key={j} className={`h-4 w-full ${bar}`} />
            ))}
          </div>
        ))}
      </div>
      <div className={`h-[38px] w-full lg:hidden ${bar}`} />
    </aside>
  );
}

/** /products 전체(searchParams를 읽기 전): 필터 + 제목 줄 + 카드 12개 */
export function ProductsPageSkeleton() {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:gap-6">
      <FilterPanelSkeleton />
      <section className="min-w-0 flex-1">
        <div className="mb-4 space-y-2">
          <div className={`h-6 w-40 ${bar}`} />
          <div className={`h-4 w-20 ${bar}`} />
        </div>
        <ProductGridSkeleton count={12} />
      </section>
    </div>
  );
}

export function ProductDetailSkeleton() {
  return (
    <div className="space-y-10" role="status" aria-label="불러오는 중">
      <section className="grid gap-6 md:grid-cols-[320px_1fr]">
        <div className={`aspect-square w-full ${bar}`} />
        <div className="space-y-3">
          <div className={`h-4 w-40 ${bar}`} />
          <div className={`h-8 w-3/4 ${bar}`} />
          <div className={`mt-5 h-4 w-20 ${bar}`} />
          <div className={`h-10 w-48 ${bar}`} />
          <div className={`h-4 w-64 ${bar}`} />
        </div>
      </section>
      <section className="space-y-3">
        <div className={`h-6 w-40 ${bar}`} />
        <div className={`h-32 w-full ${bar}`} />
      </section>
      <section className="space-y-3">
        <div className={`h-6 w-48 ${bar}`} />
        <div className={`h-48 w-full ${bar}`} />
      </section>
    </div>
  );
}
