/**
 * 클릭아웃(/go/[offerId]) 자리.
 * 이제 판매처 링크는 offer의 url로 직접 새 탭에서 열고, 클릭 로그는 아직 만들지 않았다.
 * API에는 offer id로 url을 찾는 엔드포인트가 없어서 지금은 항상 404를 돌려준다.
 * TODO: 클릭 로그 API가 생기면 여기서 기록한 뒤 offer url로 redirect한다.
 */
export async function GET() {
  return new Response("Not Found", { status: 404 });
}
