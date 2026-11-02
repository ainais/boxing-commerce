import { BOXINGMALL_ORIGIN, PROXY_PREFIX } from "@/lib/boxingmallProxy";

const BOXINGMALL_IMAGE_PREFIX = `${BOXINGMALL_ORIGIN}/product_images/`;

/**
 * 화면에 쓸 이미지 주소. 복싱몰 이미지(https://www.boxingmall.co.kr/product_images/...)는
 * 같은 사이트의 프록시 경로(/img/boxingmall/product_images/...)로 바꾸고, 그 외는 그대로 돌려준다.
 */
export function toDisplayImageSrc(imageUrl: string | null): string | null {
  if (imageUrl === null) return null;
  if (!imageUrl.startsWith(BOXINGMALL_IMAGE_PREFIX)) return imageUrl;
  return `${PROXY_PREFIX}/product_images/${imageUrl.slice(BOXINGMALL_IMAGE_PREFIX.length)}`;
}

export function isProxyImageSrc(src: string): boolean {
  return src.startsWith(`${PROXY_PREFIX}/`);
}
