/** 복싱몰 이미지 프록시(/img/boxingmall/...)의 경로 검증과 주소 상수. 순수 함수라 route.ts 밖에서도 쓴다. */

/** 상위 서버. 요청 값으로 바꿀 수 없도록 상수로 고정한다 */
export const BOXINGMALL_ORIGIN = "https://www.boxingmall.co.kr";
export const BOXINGMALL_HOST = "www.boxingmall.co.kr";

/** 이 프록시가 서비스하는 내부 경로 접두사 */
export const PROXY_PREFIX = "/img/boxingmall";

const ALLOWED_PATH = /^\/product_images\/[A-Za-z0-9/_.-]+\.(?:jpg|jpeg|png|gif|webp)$/;

/**
 * [...path] 조각을 상위 서버 경로로 합쳐 검증한다. 허용되면 "/product_images/..." 경로를, 아니면 null을 돌려준다.
 * ".."·연속 슬래시·허용 문자 밖(쿼리, 인코딩 문자 등)·허용 확장자 밖·다른 디렉터리는 모두 거부한다.
 */
export function validateProxyPath(segments: readonly string[]): string | null {
  const path = "/" + segments.join("/");
  if (path.includes("..") || path.includes("//")) return null;
  return ALLOWED_PATH.test(path) ? path : null;
}
