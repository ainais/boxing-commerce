export type CategorySlug =
  | "gloves"
  | "headgear"
  | "handwraps"
  | "bags"
  | "protectors"
  | "apparel";

export interface Category {
  slug: CategorySlug;
  name: string;
}

export interface Offer {
  /** 예: p01-11st */
  id: string;
  seller: string;
  price: number;
  url: string;
  shippingFee: number;
}

export interface Product {
  id: string;
  name: string;
  brand: string;
  categorySlug: CategorySlug;
  description: string;
  /** placeholder 이미지용 색상 (hex) */
  color: string;
  popularity: number;
  offers: Offer[];
}

/** 목록/카드용: offers에서 계산한 최저가가 포함된 상품 */
export interface ProductWithPrice extends Product {
  lowestPrice: number;
  /** 최저가 offer (가격 동일 시 배송비가 낮은 쪽) */
  lowestOffer: Offer;
}

export interface PricePoint {
  /** 0 = 오늘, 29 = 29일 전 */
  daysAgo: number;
  price: number;
}

/** 상세 페이지용: offers는 최저가순, 최근 30일 일별 최저가 이력 포함 */
export interface ProductDetail extends ProductWithPrice {
  priceHistory: PricePoint[];
}
