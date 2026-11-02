import { Suspense } from "react";
import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  apiErrorKind,
  getProduct,
  getRelatedProducts,
  getStaticProductIds,
  settle,
} from "@/lib/api";
import { shippingLabel, won } from "@/lib/format";
import { ErrorNotice } from "@/components/ErrorNotice";
import { OfferTable } from "@/components/OfferTable";
import { PriceChart } from "@/components/PriceChart";
import { ProductGrid } from "@/components/ProductGrid";
import { ProductImage } from "@/components/ProductImage";
import { ProductDetailSkeleton, ProductGridSkeleton } from "@/components/skeletons";

type Params = Promise<{ id: string }>;

const isProductId = (id: string) => /^\d+$/.test(id);

// Cache Components: 동적 라우트는 최소 1개 이상의 params를 prerender 해야 한다
export async function generateStaticParams() {
  return (await getStaticProductIds()).map((id) => ({ id }));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  const result = isProductId(id) ? await settle(getProduct(id)) : null;
  return {
    title: result?.data ? `${result.data.name} - 복싱의모든것` : "상품 - 복싱의모든것",
  };
}

export default function ProductDetailPage({ params }: { params: Params }) {
  return (
    // params는 요청 시점 데이터이므로 Suspense 경계 안에서 await한다
    <Suspense fallback={<ProductDetailSkeleton />}>
      <ProductDetailContent params={params} />
    </Suspense>
  );
}

/** 관련 상품은 상세와 따로 스트리밍한다. 실패하면 섹션을 숨긴다 */
async function RelatedProducts({ id }: { id: string }) {
  const related = (await settle(getRelatedProducts(id, 4))).data ?? [];
  if (related.length === 0) return null;
  return (
    <section>
      <h2 className="mb-3 text-lg font-bold text-gray-900">관련 상품</h2>
      <ProductGrid products={related} />
    </section>
  );
}

async function ProductDetailContent({ params }: { params: Params }) {
  const { id } = await params;
  if (!isProductId(id)) notFound();

  const result = await settle(getProduct(id));
  if (!result.ok) {
    // 404(없는 상품·offer 없는 상품)와 400은 not-found 페이지로, 그 외(네트워크·서버 오류)는 안내만 보여 준다
    const kind = apiErrorKind(result.error);
    if (kind === "not_found" || kind === "bad_request") notFound();
    return <ErrorNotice />;
  }
  const product = result.data;
  const inStockCount = product.offers.filter((o) => o.inStock).length;

  return (
    <div className="space-y-10">
      <section className="grid gap-6 md:grid-cols-[320px_1fr]">
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <ProductImage
            src={product.imageUrl}
            label={product.name}
            seed={product.id}
            sizes="(min-width: 768px) 320px, 100vw"
            eager
          />
        </div>
        <div>
          <p className="text-sm text-gray-500">
            <Link
              href={`/products?category=${product.categorySlug}`}
              className="hover:text-red-600 hover:underline"
            >
              {product.categoryName}
            </Link>
            {" · "}
            {product.brand}
          </p>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">{product.name}</h1>
          <div className="mt-5">
            {product.inStock && product.lowestOffer && product.lowestPrice !== null ? (
              <>
                <span className="text-sm font-semibold text-red-600">현재 최저가</span>
                <p className="text-3xl font-extrabold text-red-600">{won(product.lowestPrice)}</p>
                <p className="mt-1 text-sm text-gray-500">
                  {product.lowestOffer.seller} · {shippingLabel(product.lowestOffer.shippingFee)} ·
                  판매처 {inStockCount}곳
                </p>
              </>
            ) : (
              <p className="text-3xl font-extrabold text-gray-400">현재 품절</p>
            )}
          </div>
        </div>
      </section>

      {product.offers.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold text-gray-900">판매처별 가격 비교</h2>
          <OfferTable offers={product.offers} lowestOfferId={product.lowestOffer?.id ?? null} />
        </section>
      )}

      {product.priceHistory.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-bold text-gray-900">가격 추이 (최근 30일)</h2>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <PriceChart history={product.priceHistory} />
          </div>
        </section>
      )}

      <Suspense fallback={<ProductGridSkeleton count={4} />}>
        <RelatedProducts id={id} />
      </Suspense>
    </div>
  );
}
