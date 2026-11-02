/** apps/api 조회 API 응답 형식 (apps/api/README.md "조회 API" 참고) */

export interface Category {
  slug: string;
  name: string;
}

export interface Offer {
  id: number;
  /** 판매처 이름 */
  seller: string;
  price: number;
  shippingFee: number;
  url: string;
  /** false면 품절 */
  inStock: boolean;
}

/** 목록/카드용 상품 */
export interface ProductSummary {
  id: number;
  name: string;
  brand: string;
  categorySlug: string;
  categoryName: string;
  imageUrl: string | null;
  lowestPrice: number;
  /** 최저가 offer (가격 동일 시 배송비가 낮은 쪽) */
  lowestOffer: Offer;
  offerCount: number;
}

export interface PricePoint {
  /** 0 = 오늘, 29 = 29일 전 */
  daysAgo: number;
  price: number;
}

/**
 * 상세 페이지용: offers는 재고 있는 offer 먼저, 각각 가격 낮은 순(같으면 배송비 낮은 순).
 * lowestPrice·lowestOffer는 재고 있는 offer 기준이며 전부 품절이면 null(inStock=false).
 * priceHistory는 재고 있는 offer 기준 최근 30일 일별 최저가(전부 품절이면 빈 배열).
 */
export interface ProductDetail {
  id: number;
  name: string;
  brand: string;
  categorySlug: string;
  categoryName: string;
  imageUrl: string | null;
  /** 재고 있는 offer가 하나라도 있으면 true */
  inStock: boolean;
  lowestPrice: number | null;
  lowestOffer: Offer | null;
  offers: Offer[];
  priceHistory: PricePoint[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/** API 오류 응답 본문 */
export interface ApiErrorBody {
  code: string;
  message: string;
}
