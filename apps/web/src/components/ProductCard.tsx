import Link from "next/link";
import type { ProductWithPrice } from "@/lib/types";
import { ProductImage } from "./ProductImage";

const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

export function ProductCard({ product }: { product: ProductWithPrice }) {
  const { lowestOffer, offers } = product;
  return (
    <Link
      href={`/products/${product.id}`}
      className="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white hover:border-gray-400"
    >
      <ProductImage color={product.color} label={product.name} />
      <div className="flex flex-1 flex-col gap-1 p-3">
        <span className="text-xs text-gray-500">{product.brand}</span>
        <h3 className="line-clamp-2 text-sm font-medium text-gray-900">{product.name}</h3>
        <div className="mt-auto pt-2">
          <span className="text-xs font-semibold text-red-600">최저가</span>
          <p className="text-lg font-bold text-red-600">{won(product.lowestPrice)}</p>
          <p className="text-xs text-gray-500">
            {lowestOffer.seller} ·{" "}
            {lowestOffer.shippingFee === 0 ? "무료배송" : `배송비 ${won(lowestOffer.shippingFee)}`}
          </p>
          <p className="mt-1 text-xs text-gray-400">판매처 {offers.length}곳</p>
        </div>
      </div>
    </Link>
  );
}
