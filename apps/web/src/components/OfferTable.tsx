import type { Offer } from "@/lib/types";

const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

/** 총액(가격+배송비) 낮은 순 판매처 비교 표. 모바일에서는 가로 스크롤. */
export function OfferTable({ offers, lowestOfferId }: { offers: Offer[]; lowestOfferId: string }) {
  const rows = offers
    .map((o) => ({ ...o, total: o.price + o.shippingFee }))
    .sort((a, b) => a.total - b.total || a.price - b.price);
  const lowestTotalId = rows[0]?.id;

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="w-full min-w-[560px] text-sm">
        <thead className="bg-gray-50 text-left text-xs text-gray-500">
          <tr>
            <th className="px-4 py-2.5 font-medium">판매처</th>
            <th className="px-4 py-2.5 text-right font-medium">가격</th>
            <th className="px-4 py-2.5 text-right font-medium">배송비</th>
            <th className="px-4 py-2.5 text-right font-medium">총액</th>
            <th className="px-4 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((o) => (
            <tr key={o.id}>
              <td className="px-4 py-3">
                <span className="font-medium text-gray-900">{o.seller}</span>
                {o.id === lowestOfferId && (
                  <span className="ml-2 rounded bg-red-50 px-1.5 py-0.5 text-xs font-semibold text-red-600">
                    최저가
                  </span>
                )}
                {o.id === lowestTotalId && o.id !== lowestOfferId && (
                  <span className="ml-2 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-semibold text-blue-600">
                    총액 최저
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-right">{won(o.price)}</td>
              <td className="px-4 py-3 text-right text-gray-600">
                {o.shippingFee === 0 ? "무료" : won(o.shippingFee)}
              </td>
              <td className="px-4 py-3 text-right font-bold text-gray-900">{won(o.total)}</td>
              <td className="px-4 py-3 text-right">
                <a
                  href={`/go/${o.id}`}
                  target="_blank"
                  rel="noopener noreferrer sponsored"
                  className="inline-block whitespace-nowrap rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700"
                >
                  판매처로 이동
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
