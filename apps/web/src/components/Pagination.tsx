import Link from "next/link";
import { buildProductHref, type ProductQuery } from "@/lib/productQuery";

export function Pagination({
  query,
  total,
  pageSize,
}: {
  query: ProductQuery;
  total: number;
  pageSize: number;
}) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  const current = Math.min(query.page, totalPages);
  const href = (page: number) => buildProductHref({ ...query, page });
  const base = "flex h-9 min-w-9 items-center justify-center rounded-md border px-2 text-sm";

  return (
    <nav aria-label="페이지" className="mt-8 flex flex-wrap items-center justify-center gap-1.5">
      {current > 1 && (
        <Link href={href(current - 1)} className={`${base} border-gray-300 bg-white hover:bg-gray-50`}>
          이전
        </Link>
      )}
      {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
        <Link
          key={p}
          href={href(p)}
          aria-current={p === current ? "page" : undefined}
          className={`${base} ${
            p === current
              ? "border-gray-900 bg-gray-900 font-semibold text-white"
              : "border-gray-300 bg-white hover:bg-gray-50"
          }`}
        >
          {p}
        </Link>
      ))}
      {current < totalPages && (
        <Link href={href(current + 1)} className={`${base} border-gray-300 bg-white hover:bg-gray-50`}>
          다음
        </Link>
      )}
    </nav>
  );
}
