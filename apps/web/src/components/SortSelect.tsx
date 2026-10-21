"use client";

import { useRouter } from "next/navigation";
import { SORT_OPTIONS, buildProductHref, type ProductQuery } from "@/lib/productQuery";

export function SortSelect({ query }: { query: ProductQuery }) {
  const router = useRouter();
  return (
    <select
      aria-label="정렬"
      value={query.sort}
      onChange={(e) =>
        router.push(buildProductHref({ ...query, sort: e.target.value as ProductQuery["sort"], page: 1 }))
      }
      className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm"
    >
      {SORT_OPTIONS.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
