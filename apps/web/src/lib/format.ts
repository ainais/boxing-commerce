export const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

/**
 * 배송비 표시 규칙 (한 곳에서만 정의).
 * 지금 수집 상품의 배송비는 0으로 들어오지만 실제 정책을 모르는 상태라, 0은 "무료"가 아니라 "판매처 확인"으로 보여 준다.
 * 배송비 정책이 정해지면 이 파일만 고치면 된다.
 */
export const isShippingKnown = (fee: number) => fee > 0;

/** 값만 (표의 배송비 칸 등): "판매처 확인" | "3,000원" */
export const shippingValue = (fee: number) => (isShippingKnown(fee) ? won(fee) : "판매처 확인");

/** 문장형 (카드, 상세): "배송비 판매처 확인" | "배송비 3,000원" */
export const shippingLabel = (fee: number) => `배송비 ${shippingValue(fee)}`;
