import { Suspense } from "react";
import { getCategories, getPopularProducts, getProductsByCategory, settle } from "@/lib/api";
import { ErrorNotice } from "@/components/ErrorNotice";
import { ProductGrid } from "@/components/ProductGrid";
import { Section } from "@/components/Section";
import { SectionSkeleton } from "@/components/skeletons";

const FEATURED_SLUGS = ["gloves", "handwraps"];

// 각 섹션이 데이터를 따로 기다리므로 독립 Suspense로 감싸 따로 스트리밍한다.
// (cacheLife의 stale이 5분 미만이면 App Shell에 포함되지 않아, Suspense 밖에서 읽으면 prerender가 막힌다)
export default function Home() {
  return (
    <>
      <Suspense fallback={<SectionSkeleton count={8} />}>
        <PopularSection />
      </Suspense>
      {FEATURED_SLUGS.map((slug) => (
        <Suspense key={slug} fallback={<SectionSkeleton />}>
          <FeaturedSection slug={slug} />
        </Suspense>
      ))}
    </>
  );
}

async function PopularSection() {
  const popular = await settle(getPopularProducts(8));
  return (
    <Section title="인기 상품">
      {/* 첫 줄(4개)은 above-the-fold라 이미지를 eager로 불러온다 */}
      {popular.ok ? <ProductGrid products={popular.data} eagerCount={4} /> : <ErrorNotice />}
    </Section>
  );
}

async function FeaturedSection({ slug }: { slug: string }) {
  const [categories, products] = await Promise.all([
    settle(getCategories()),
    settle(getProductsByCategory(slug, 4)),
  ]);
  const category = categories.ok ? categories.data.find((c) => c.slug === slug) : undefined;
  // 카테고리를 못 찾으면(오류 또는 DB에 없음) 섹션을 그리지 않는다
  if (!category) return null;
  return (
    <Section title={category.name}>
      {products.ok ? <ProductGrid products={products.data} /> : <ErrorNotice />}
    </Section>
  );
}
