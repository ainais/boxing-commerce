/**
 * Data access layer.
 * 컴포넌트는 mock을 직접 import하지 않고 이 파일의 함수만 호출한다.
 * 나중에 API fetch로 교체할 때 이 파일의 구현만 바꾸면 된다.
 */
import type { Category, CategorySlug, Offer, Product, ProductDetail, ProductWithPrice } from "@/lib/types";
import { categories } from "@/lib/mock/categories";
import { products } from "@/lib/mock/products";
import { generatePriceHistory } from "@/lib/mock/priceHistory";

function pickLowestOffer(offers: Offer[]): Offer {
  return offers.reduce((best, cur) =>
    cur.price < best.price || (cur.price === best.price && cur.shippingFee < best.shippingFee)
      ? cur
      : best,
  );
}

function withPrice(p: Product): ProductWithPrice {
  const lowestOffer = pickLowestOffer(p.offers);
  return { ...p, lowestPrice: lowestOffer.price, lowestOffer };
}

export async function getCategories(): Promise<Category[]> {
  return categories;
}

export async function getPopularProducts(limit = 8): Promise<ProductWithPrice[]> {
  return [...products]
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, limit)
    .map(withPrice);
}

export async function getProductsByCategory(
  slug: CategorySlug,
  limit?: number,
): Promise<ProductWithPrice[]> {
  const list = products.filter((p) => p.categorySlug === slug).map(withPrice);
  return limit ? list.slice(0, limit) : list;
}

export type ProductSort = "lowestPrice" | "priceDesc" | "name";

export interface GetProductsParams {
  q?: string;
  category?: CategorySlug;
  brands?: string[];
  minPrice?: number;
  maxPrice?: number;
  sort?: ProductSort;
  page?: number;
  pageSize?: number;
}

export interface GetProductsResult {
  items: ProductWithPrice[];
  total: number;
}

const normalize = (s: string) => s.toLowerCase().replace(/\s+/g, "");

export async function getProducts(params: GetProductsParams = {}): Promise<GetProductsResult> {
  const { q, category, brands, minPrice, maxPrice, sort = "lowestPrice", page = 1, pageSize = 12 } = params;
  const nq = q ? normalize(q) : "";
  const brandSet = brands?.length ? new Set(brands) : null;

  const filtered = products
    .filter((p) => !category || p.categorySlug === category)
    .filter((p) => !brandSet || brandSet.has(p.brand))
    .filter((p) => !nq || normalize(`${p.name}${p.brand}`).includes(nq))
    .map(withPrice)
    .filter((p) => minPrice === undefined || p.lowestPrice >= minPrice)
    .filter((p) => maxPrice === undefined || p.lowestPrice <= maxPrice);

  filtered.sort((a, b) => {
    if (sort === "priceDesc") return b.lowestPrice - a.lowestPrice;
    if (sort === "name") return a.name.localeCompare(b.name, "ko");
    return a.lowestPrice - b.lowestPrice;
  });

  const safePage = Math.max(1, Math.floor(page));
  const start = (safePage - 1) * pageSize;
  return { items: filtered.slice(start, start + pageSize), total: filtered.length };
}

export async function getBrands(category?: CategorySlug): Promise<string[]> {
  const set = new Set(
    products.filter((p) => !category || p.categorySlug === category).map((p) => p.brand),
  );
  return [...set].sort((a, b) => a.localeCompare(b));
}

export async function getCategory(slug: string): Promise<Category | undefined> {
  return categories.find((c) => c.slug === slug);
}

export async function getProductIds(): Promise<string[]> {
  return products.map((p) => p.id);
}

/** offers는 가격 낮은 순(동일 시 배송비 낮은 순). 없으면 undefined */
export async function getProduct(id: string): Promise<ProductDetail | undefined> {
  const product = products.find((p) => p.id === id);
  if (!product) return undefined;
  const offers = [...product.offers].sort((a, b) => a.price - b.price || a.shippingFee - b.shippingFee);
  const priced = withPrice({ ...product, offers });
  return { ...priced, priceHistory: generatePriceHistory(product.id, priced.lowestPrice) };
}

/** 같은 카테고리의 다른 상품 (인기순) */
export async function getRelatedProducts(id: string, limit = 4): Promise<ProductWithPrice[]> {
  const base = products.find((p) => p.id === id);
  if (!base) return [];
  return products
    .filter((p) => p.categorySlug === base.categorySlug && p.id !== id)
    .sort((a, b) => b.popularity - a.popularity)
    .slice(0, limit)
    .map(withPrice);
}

export async function getOffer(offerId: string): Promise<Offer | undefined> {
  for (const p of products) {
    const offer = p.offers.find((o) => o.id === offerId);
    if (offer) return offer;
  }
  return undefined;
}
