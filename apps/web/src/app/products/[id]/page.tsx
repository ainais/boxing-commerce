import { Suspense } from "react";
import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getCategory, getProduct, getProductIds, getRelatedProducts } from "@/lib/api";
import { OfferTable } from "@/components/OfferTable";
import { PriceChart } from "@/components/PriceChart";
import { ProductGrid } from "@/components/ProductGrid";
import { ProductImage } from "@/components/ProductImage";

type Params = Promise<{ id: string }>;

const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

// Cache Components: 동적 라우트는 최소 1개 이상의 params를 prerender 해야 한다
export async function generateStaticParams() {
  return (await getProductIds()).map((id) => ({ id }));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const product = await getProduct((await params).id);
  return { title: product ? `${product.name} - BoxingEverything` : "상품을 찾을 수 없음" };
}

export default function ProductDetailPage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<p className="py-20 text-center text-sm text-gray-500">불러오는 중...</p>}>
      <ProductDetailContent params={params} />
    </Suspense>
  );
}

async function ProductDetailContent({ params }: { params: Params }) {
  const { id } = await params;
  const product = await getProduct(id);
  if (!product) notFound();

  const [category, related] = await Promise.all([
    getCategory(product.categorySlug),
    getRelatedProducts(id, 4),
  ]);

  return (
    <div className="space-y-10">
      <section className="grid gap-6 md:grid-cols-[320px_1fr]">
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <ProductImage color={product.color} label={product.name} />
        </div>
        <div>
          <p className="text-sm text-gray-500">
            {category && (
              <Link href={`/products?category=${category.slug}`} className="hover:text-red-600 hover:underline">
                {category.name}
              </Link>
            )}
            {category && " · "}
            {product.brand}
          </p>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{product.name}</h1>
          <p className="mt-2 text-sm text-gray-600">{product.description}</p>
          <div className="mt-5">
            <span className="text-sm font-semibold text-red-600">현재 최저가</span>
            <p className="text-3xl font-extrabold text-red-600">{won(product.lowestPrice)}</p>
            <p className="mt-1 text-sm text-gray-500">
              {product.lowestOffer.seller} ·{" "}
              {product.lowestOffer.shippingFee === 0
                ? "무료배송"
                : `배송비 ${won(product.lowestOffer.shippingFee)}`}{" "}
              · 판매처 {product.offers.length}곳
            </p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold text-gray-900">판매처별 가격 비교</h2>
        <OfferTable offers={product.offers} lowestOfferId={product.lowestOffer.id} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold text-gray-900">가격 추이 (최근 30일)</h2>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <PriceChart history={product.priceHistory} />
        </div>
      </section>

      {related.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold text-gray-900">관련 상품</h2>
          <ProductGrid products={related} />
        </section>
      )}
    </div>
  );
}
