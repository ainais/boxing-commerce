import type { Offer } from "@/lib/types";
import { isShippingKnown, shippingValue, won } from "@/lib/format";

/**
 * 총액(가격+배송비) 낮은 순 판매처 비교 표. 재고 있는 offer가 먼저, 품절은 아래에 흐리게 표시한다.
 * 품절 offer는 "최저가"·"총액 최저" 배지 계산에서 제외한다. 모바일에서는 가로 스크롤.
 */
export function OfferTable({ offers, lowestOfferId }: { offers: Offer[]; lowestOfferId: number | null }) {
  const rows = offers
    .map((o) => ({ ...o, total: o.price + o.shippingFee }))
    .sort((a, b) => Number(b.inStock) - Number(a.inStock) || a.total - b.total || a.price - b.price);
  const lowestTotalId = rows.find((o) => o.inStock)?.id;

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
            <tr key={o.id} className={o.inStock ? undefined : "opacity-50"}>
              <td className="px-4 py-3">
                <span className="font-medium text-gray-900">{o.seller}</span>
                {!o.inStock && (
                  <span className="ml-2 rounded bg-gray-100 px-1.5 py-0.5 text-xs font-semibold text-gray-600">
                    품절
                  </span>
                )}
                {o.inStock && o.id === lowestOfferId && (
                  <span className="ml-2 rounded bg-red-50 px-1.5 py-0.5 text-xs font-semibold text-red-600">
                    최저가
                  </span>
                )}
                {o.inStock && o.id === lowestTotalId && o.id !== lowestOfferId && (
                  <span className="ml-2 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-semibold text-blue-600">
                    총액 최저
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-right">{won(o.price)}</td>
              <td className="px-4 py-3 text-right text-gray-600">{shippingValue(o.shippingFee)}</td>
              <td className="px-4 py-3 text-right font-bold text-gray-900">
                {won(o.total)}
                {!isShippingKnown(o.shippingFee) && (
                  <span className="block text-xs font-normal text-gray-400">배송비 제외</span>
                )}
              </td>
              <td className="px-4 py-3 text-right">
                {o.inStock ? (
                  <a
                    href={o.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block whitespace-nowrap rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700"
                  >
                    판매처로 이동
                  </a>
                ) : (
                  <span
                    aria-disabled="true"
                    className="inline-block cursor-not-allowed whitespace-nowrap rounded-md bg-gray-200 px-3 py-1.5 text-xs font-medium text-gray-500"
                  >
                    품절
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
