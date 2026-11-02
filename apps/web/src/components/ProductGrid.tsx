import type { ProductSummary } from "@/lib/types";
import { ProductCard } from "./ProductCard";

/** eagerCount: 앞에서부터 이 개수만큼은 이미지를 eager로 불러온다(above-the-fold 첫 줄용) */
export function ProductGrid({
  products,
  eagerCount = 0,
}: {
  products: ProductSummary[];
  eagerCount?: number;
}) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} eagerImage={i < eagerCount} />
      ))}
    </div>
  );
}
