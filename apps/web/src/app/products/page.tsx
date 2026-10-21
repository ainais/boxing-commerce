import { Suspense } from "react";
import Link from "next/link";
import { getBrands, getCategories, getProducts } from "@/lib/api";
import { PAGE_SIZE, buildProductHref, parseProductQuery } from "@/lib/productQuery";
import { FilterPanel } from "@/components/FilterPanel";
import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductGrid";
import { SortSelect } from "@/components/SortSelect";

export const metadata = { title: "상품 목록 - BoxingEverything" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function ProductsPage(props: { searchParams: SearchParams }) {
  // searchParams는 요청 시점 API이므로 Suspense 경계 안에서 읽는다
  return (
    <Suspense fallback={<p className="py-20 text-center text-sm text-gray-500">불러오는 중...</p>}>
      <ProductsContent searchParams={props.searchParams} />
    </Suspense>
  );
}

async function ProductsContent({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const categories = await getCategories();
  const query = parseProductQuery(await searchParams, categories.map((c) => c.slug));

  const [brands, { items, total }] = await Promise.all([
    getBrands(query.category),
    getProducts({ ...query, pageSize: PAGE_SIZE }),
  ]);
  const categoryName = categories.find((c) => c.slug === query.category)?.name;

  const title = query.q ? `'${query.q}' 검색 결과` : (categoryName ?? "전체 상품");

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:gap-6">
      <FilterPanel query={query} categories={categories} brands={brands} />

      <section className="min-w-0 flex-1">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-lg font-bold text-gray-900">
              {title}
              {query.q && categoryName ? <span className="ml-2 text-sm font-normal text-gray-500">in {categoryName}</span> : null}
            </h1>
            <p className="text-sm text-gray-500">총 {total.toLocaleString("ko-KR")}개</p>
          </div>
          <SortSelect query={query} />
        </div>

        {items.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white py-16 text-center">
            <p className="font-medium text-gray-900">조건에 맞는 상품이 없습니다.</p>
            <p className="mt-1 text-sm text-gray-500">검색어나 필터를 바꿔 보세요.</p>
            <Link
              href={buildProductHref({})}
              className="mt-4 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
            >
              필터 초기화
            </Link>
          </div>
        ) : (
          <>
            <ProductGrid products={items} />
            <Pagination query={query} total={total} pageSize={PAGE_SIZE} />
          </>
        )}
      </section>
    </div>
  );
}
