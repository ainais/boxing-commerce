import { getCategories, getPopularProducts, getProductsByCategory } from "@/lib/api";
import { ProductGrid } from "@/components/ProductGrid";
import { Section } from "@/components/Section";

export default async function Home() {
  const [popular, categories] = await Promise.all([getPopularProducts(8), getCategories()]);
  const featured = categories.filter((c) => c.slug === "gloves" || c.slug === "handwraps");
  const sections = await Promise.all(
    featured.map(async (c) => ({ category: c, products: await getProductsByCategory(c.slug, 4) })),
  );

  return (
    <>
      <Section title="인기 상품">
        <ProductGrid products={popular} />
      </Section>
      {sections.map(({ category, products }) => (
        <Section key={category.slug} title={category.name}>
          <ProductGrid products={products} />
        </Section>
      ))}
    </>
  );
}
