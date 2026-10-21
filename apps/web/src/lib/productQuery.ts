import type { CategorySlug } from "@/lib/types";
import type { ProductSort } from "@/lib/api";

/** /products URL searchParams <-> 목록 상태 변환 (서버/클라이언트 공용) */
export interface ProductQuery {
  q: string;
  category?: CategorySlug;
  brands: string[];
  minPrice?: number;
  maxPrice?: number;
  sort: ProductSort;
  page: number;
}

export const PAGE_SIZE = 12;

export const SORT_OPTIONS: { value: ProductSort; label: string }[] = [
  { value: "lowestPrice", label: "최저가 낮은 순" },
  { value: "priceDesc", label: "최저가 높은 순" },
  { value: "name", label: "상품명 순" },
];

type RawParams = Record<string, string | string[] | undefined>;

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

function toPrice(v: string | string[] | undefined): number | undefined {
  const s = first(v);
  if (!s) return undefined;
  const n = Number(s);
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : undefined;
}

export function parseProductQuery(raw: RawParams, validCategories: string[]): ProductQuery {
  const category = first(raw.category);
  const sort = first(raw.sort);
  const page = Number(first(raw.page));
  const brand = raw.brand;
  return {
    q: (first(raw.q) ?? "").trim(),
    category: category && validCategories.includes(category) ? (category as CategorySlug) : undefined,
    brands: (Array.isArray(brand) ? brand : brand ? [brand] : []).filter(Boolean),
    minPrice: toPrice(raw.minPrice),
    maxPrice: toPrice(raw.maxPrice),
    sort: SORT_OPTIONS.some((o) => o.value === sort) ? (sort as ProductSort) : "lowestPrice",
    page: Number.isInteger(page) && page > 0 ? page : 1,
  };
}

/** 기본값은 URL에서 생략한다. */
export function buildProductHref(query: Partial<ProductQuery>): string {
  const p = new URLSearchParams();
  if (query.q) p.set("q", query.q);
  if (query.category) p.set("category", query.category);
  query.brands?.forEach((b) => p.append("brand", b));
  if (query.minPrice !== undefined) p.set("minPrice", String(query.minPrice));
  if (query.maxPrice !== undefined) p.set("maxPrice", String(query.maxPrice));
  if (query.sort && query.sort !== "lowestPrice") p.set("sort", query.sort);
  if (query.page && query.page > 1) p.set("page", String(query.page));
  const s = p.toString();
  return s ? `/products?${s}` : "/products";
}
