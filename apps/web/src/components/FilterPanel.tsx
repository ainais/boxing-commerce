"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Category } from "@/lib/types";
import { buildProductHref, type ProductQuery } from "@/lib/productQuery";

interface Props {
  query: ProductQuery;
  categories: Category[];
  brands: string[];
}

export function FilterPanel({ query, categories, brands }: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const hasFilter =
    !!query.category || query.brands.length > 0 || query.minPrice !== undefined || query.maxPrice !== undefined;

  function apply(form: HTMLFormElement) {
    const fd = new FormData(form);
    const price = (name: string) => {
      const v = String(fd.get(name) ?? "").trim();
      return v === "" || !Number.isFinite(Number(v)) || Number(v) < 0 ? undefined : Math.floor(Number(v));
    };
    const category = String(fd.get("category") ?? "");
    router.push(
      buildProductHref({
        q: query.q,
        sort: query.sort,
        category: (category || undefined) as ProductQuery["category"],
        brands: fd.getAll("brand").map(String),
        minPrice: price("minPrice"),
        maxPrice: price("maxPrice"),
        // 필터 변경 시 page는 1로 리셋
      }),
    );
  }

  return (
    <aside className="lg:w-56 lg:shrink-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium lg:hidden"
      >
        필터{hasFilter ? " (적용 중)" : ""}
        <span aria-hidden="true">{open ? "▲" : "▼"}</span>
      </button>

      {/* key: URL이 바뀌면(초기화 등) 폼 입력값을 새 상태로 다시 그린다 */}
      <form
        key={buildProductHref(query)}
        className={`${open ? "block" : "hidden"} mt-3 space-y-5 rounded-lg border border-gray-200 bg-white p-4 lg:mt-0 lg:block`}
        onSubmit={(e) => {
          e.preventDefault();
          apply(e.currentTarget);
        }}
        onChange={(e) => {
          const t = e.target as unknown as HTMLInputElement;
          if (t.type === "radio" || t.type === "checkbox") apply(e.currentTarget);
        }}
      >
        <fieldset>
          <legend className="mb-2 text-sm font-bold text-gray-900">카테고리</legend>
          <ul className="space-y-1.5 text-sm">
            <li>
              <label className="flex items-center gap-2">
                <input type="radio" name="category" value="" defaultChecked={!query.category} />
                전체
              </label>
            </li>
            {categories.map((c) => (
              <li key={c.slug}>
                <label className="flex items-center gap-2">
                  <input type="radio" name="category" value={c.slug} defaultChecked={query.category === c.slug} />
                  {c.name}
                </label>
              </li>
            ))}
          </ul>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-bold text-gray-900">브랜드</legend>
          <ul className="space-y-1.5 text-sm">
            {brands.map((b) => (
              <li key={b}>
                <label className="flex items-center gap-2">
                  <input type="checkbox" name="brand" value={b} defaultChecked={query.brands.includes(b)} />
                  {b}
                </label>
              </li>
            ))}
          </ul>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-bold text-gray-900">가격 (원)</legend>
          <div className="flex items-center gap-1.5 text-sm">
            <input
              name="minPrice"
              type="number"
              min={0}
              inputMode="numeric"
              placeholder="최소"
              aria-label="최소 가격"
              defaultValue={query.minPrice ?? ""}
              className="w-full min-w-0 rounded border border-gray-300 px-2 py-1.5"
            />
            <span>~</span>
            <input
              name="maxPrice"
              type="number"
              min={0}
              inputMode="numeric"
              placeholder="최대"
              aria-label="최대 가격"
              defaultValue={query.maxPrice ?? ""}
              className="w-full min-w-0 rounded border border-gray-300 px-2 py-1.5"
            />
          </div>
          <button
            type="submit"
            className="mt-2 w-full rounded-md bg-gray-900 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
          >
            적용
          </button>
        </fieldset>

        <button
          type="button"
          onClick={() => router.push(buildProductHref({ q: query.q, sort: query.sort }))}
          className="w-full rounded-md border border-gray-300 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          필터 초기화
        </button>
      </form>
    </aside>
  );
}
