import { Suspense } from "react";
import Image from "next/image";
import Link from "next/link";
import { apiErrorMessage, getBrands, getCategories, getProducts, settle } from "@/lib/api";
import {
  PAGE_SIZE,
  buildProductHref,
  parseProductQuery,
  type ProductQuery,
} from "@/lib/productQuery";
import type { Category } from "@/lib/types";
import { ErrorNotice } from "@/components/ErrorNotice";
import { FilterPanel } from "@/components/FilterPanel";
import { Pagination } from "@/components/Pagination";
import { ProductGrid } from "@/components/ProductGrid";
import { SortSelect } from "@/components/SortSelect";
import {
  FilterPanelSkeleton,
  ProductGridSkeleton,
  ProductsPageSkeleton,
} from "@/components/skeletons";

export const metadata = { title: "상품 목록 - 복싱의모든것" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function ProductsPage(props: { searchParams: SearchParams }) {
  // searchParams는 요청 시점 데이터이므로 Suspense 경계 안에서 읽는다
  return (
    <Suspense fallback={<ProductsPageSkeleton />}>
      <ProductsContent searchParams={props.searchParams} />
    </Suspense>
  );
}

async function ProductsContent({ searchParams }: { searchParams: SearchParams }) {
  const categoriesResult = await settle(getCategories());
  if (!categoriesResult.ok) return <ErrorNotice />;
  const categories = categoriesResult.data;
  const query = parseProductQuery(await searchParams, categories.map((c) => c.slug));
  const categoryName = categories.find((c) => c.slug === query.category)?.name;
  const title = query.q ? `'${query.q}' 검색 결과` : (categoryName ?? "전체 상품");

  // 필터(브랜드 목록)와 상품 영역은 각자 Suspense로 따로 스트리밍한다
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:gap-6">
      <Suspense fallback={<FilterPanelSkeleton />}>
        <FilterSection query={query} categories={categories} />
      </Suspense>

      <section className="min-w-0 flex-1">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-lg font-bold text-gray-900">
            {title}
            {query.q && categoryName ? (
              <span className="ml-2 text-sm font-normal text-gray-500">in {categoryName}</span>
            ) : null}
          </h1>
          <SortSelect query={query} />
        </div>

        <Suspense fallback={<ProductGridSkeleton count={PAGE_SIZE} />}>
          <ProductResults query={query} />
        </Suspense>
      </section>
    </div>
  );
}

async function FilterSection({ query, categories }: { query: ProductQuery; categories: Category[] }) {
  const brands = (await settle(getBrands(query.category))).data ?? [];
  return <FilterPanel query={query} categories={categories} brands={brands} />;
}

async function ProductResults({ query }: { query: ProductQuery }) {
  const result = await settle(getProducts({ ...query, size: PAGE_SIZE }));
  if (!result.ok) return <ErrorNotice message={apiErrorMessage(result.error)} />;
  const { items, total } = result.data;

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center rounded-lg border border-gray-200 bg-white py-12 text-center">
        <Image
          src="/brand/mascot.png"
          alt="복싱 글러브를 낀 고양이 마스코트"
          width={160}
          height={160}
          className="mb-3 h-auto w-40"
        />
        <p className="font-medium text-gray-900">조건에 맞는 상품이 없어요</p>
        <p className="mt-1 text-sm text-gray-500">검색어나 필터를 바꿔 보세요.</p>
        <Link
          href={buildProductHref({})}
          className="mt-4 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          필터 초기화
        </Link>
      </div>
    );
  }

  return (
    <>
      <p className="mb-3 text-sm text-gray-500">총 {total.toLocaleString("ko-KR")}개</p>
      <ProductGrid products={items} />
      <Pagination query={query} total={total} pageSize={PAGE_SIZE} />
    </>
  );
}
