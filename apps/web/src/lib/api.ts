/**
 * apps/api 조회 API 클라이언트. 서버 컴포넌트에서만 호출한다(클라이언트 호출 없음).
 *
 * 캐시 (cacheComponents 사용 중이라 fetch가 아닌 "use cache"로 제어):
 * - 카테고리·브랜드·상품 목록/상세·관련 상품: 60초 (stale/revalidate 60초, 5분 뒤 만료)
 * - 검색어(q)가 있는 목록: 키가 무한히 늘어나므로 캐시하지 않고 매 요청마다 가져온다(no-store)
 */
import { cacheLife } from "next/cache";
import type { Category, Page, ProductDetail, ProductSummary } from "@/lib/types";

const API_BASE_URL = (process.env.API_BASE_URL || "http://localhost:4001").replace(/\/+$/, "");
const REQUEST_TIMEOUT_MS = 8000;

export type ApiErrorKind = "bad_request" | "not_found" | "network" | "server";

/**
 * 오류 종류를 메시지 접두어(API_<kind>:)에도 넣는다.
 * "use cache" 경계를 지나면 Error 클래스가 보존되지 않을 수 있어서 apiErrorKind()가 접두어로도 판별한다.
 */
export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(`API_${kind}: ${message}`);
    this.name = "ApiError";
  }
}

export function apiErrorKind(e: unknown): ApiErrorKind | null {
  if (e instanceof ApiError) return e.kind;
  if (e instanceof Error) {
    const m = /^API_(bad_request|not_found|network|server):/.exec(e.message);
    if (m) return m[1] as ApiErrorKind;
  }
  return null;
}

/** 사용자에게 보여 줄 수 있는 오류 메시지(400일 때 API가 준 안내 포함) */
export function apiErrorMessage(e: unknown): string {
  const kind = apiErrorKind(e);
  if (kind === "bad_request" && e instanceof Error) {
    return e.message.replace(/^API_bad_request:\s*/, "");
  }
  return "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
}

export type Settled<T> =
  | { ok: true; data: T; error?: undefined }
  | { ok: false; data?: undefined; error: unknown };

/** 페이지가 크래시하지 않고 오류 안내를 보여 줄 수 있게 결과를 값으로 돌려준다 */
export async function settle<T>(promise: Promise<T>): Promise<Settled<T>> {
  try {
    return { ok: true, data: await promise };
  } catch (error) {
    return { ok: false, error };
  }
}

async function request<T>(path: string, query: string, noStore: boolean): Promise<T> {
  const url = `${API_BASE_URL}${path}${query ? `?${query}` : ""}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      ...(noStore ? { cache: "no-store" as const } : {}),
    });
  } catch (e) {
    throw new ApiError("network", `API에 연결하지 못했습니다 (${e instanceof Error ? e.message : e})`);
  }
  if (!res.ok) {
    let message = `API 오류 (HTTP ${res.status})`;
    let code: string | undefined;
    try {
      const body = (await res.json()) as { code?: string; message?: string };
      code = body.code;
      if (body.message) message = body.message;
    } catch {
      // 본문이 JSON이 아니면 기본 메시지를 쓴다
    }
    const kind: ApiErrorKind =
      res.status === 400 ? "bad_request" : res.status === 404 ? "not_found" : "server";
    throw new ApiError(kind, message, res.status, code);
  }
  return (await res.json()) as T;
}

/** 60초 캐시 조회. 실패(throw)는 캐시되지 않는다. */
async function cachedGet<T>(path: string, query: string): Promise<T> {
  "use cache";
  cacheLife({ stale: 60, revalidate: 60, expire: 300 });
  return request<T>(path, query, false);
}

export type ProductSort = "lowestPrice" | "priceDesc" | "name" | "popular";

export interface GetProductsParams {
  q?: string;
  category?: string;
  brands?: string[];
  minPrice?: number;
  maxPrice?: number;
  sort?: ProductSort;
  page?: number;
  size?: number;
}

export async function getCategories(): Promise<Category[]> {
  return cachedGet<Category[]>("/api/categories", "");
}

export async function getBrands(category?: string): Promise<string[]> {
  const p = new URLSearchParams();
  if (category) p.set("category", category);
  return cachedGet<string[]>("/api/brands", p.toString());
}

export async function getProducts(params: GetProductsParams = {}): Promise<Page<ProductSummary>> {
  const p = new URLSearchParams();
  if (params.q) p.set("q", params.q);
  if (params.category) p.set("category", params.category);
  params.brands?.forEach((b) => p.append("brand", b));
  if (params.minPrice !== undefined) p.set("minPrice", String(params.minPrice));
  if (params.maxPrice !== undefined) p.set("maxPrice", String(params.maxPrice));
  if (params.sort) p.set("sort", params.sort);
  if (params.page) p.set("page", String(params.page));
  if (params.size) p.set("size", String(params.size));
  const query = p.toString();
  return params.q
    ? request<Page<ProductSummary>>("/api/products", query, true)
    : cachedGet<Page<ProductSummary>>("/api/products", query);
}

export async function getPopularProducts(limit = 8): Promise<ProductSummary[]> {
  return (await getProducts({ sort: "popular", size: limit })).items;
}

export async function getProductsByCategory(slug: string, limit = 4): Promise<ProductSummary[]> {
  return (await getProducts({ category: slug, sort: "popular", size: limit })).items;
}

/** 없는 상품이면 kind가 "not_found"인 ApiError를 던진다 */
export async function getProduct(id: string): Promise<ProductDetail> {
  return cachedGet<ProductDetail>(`/api/products/${encodeURIComponent(id)}`, "");
}

export async function getRelatedProducts(id: string, limit = 4): Promise<ProductSummary[]> {
  return cachedGet<ProductSummary[]>(
    `/api/products/${encodeURIComponent(id)}/related`,
    `limit=${limit}`,
  );
}

/** generateStaticParams용: prerender할 상품 id를 최소 1개 돌려준다(API를 못 쓰면 "1") */
export async function getStaticProductIds(): Promise<string[]> {
  const result = await settle(getProducts({ size: 1 }));
  const first = result.data?.items[0];
  return [String(first?.id ?? 1)];
}
