import { getOffer } from "@/lib/api";

/**
 * 클릭아웃: 판매처 외부 URL로 가기 전에 반드시 이 핸들러를 거친다.
 * TODO: 나중에 여기서 클릭 로그(offerId, referrer 등)를 API에 남긴다. 지금은 redirect만 수행.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ offerId: string }> },
) {
  const { offerId } = await params;
  const offer = await getOffer(offerId);
  if (!offer) {
    return new Response("Not Found", { status: 404 });
  }
  return Response.redirect(offer.url, 302);
}
