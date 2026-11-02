import { Suspense } from "react";
import Link from "next/link";
import { getCategories, settle } from "@/lib/api";
import { Logo } from "./Logo";
import { CategoryNavSkeleton } from "./skeletons";
import { SearchBar } from "./SearchBar";

/** 카테고리 메뉴: 데이터를 기다리는 부분이라 Header에서 Suspense로 감싼다 */
async function CategoryNav() {
  // API 장애 시에도 헤더는 그려지고 카테고리 메뉴만 비어 있게 한다
  const categories = (await settle(getCategories())).data ?? [];
  return (
    <ul className="flex gap-5 whitespace-nowrap text-sm text-gray-700">
      {categories.map((c) => (
        <li key={c.slug}>
          <Link href={`/products?category=${c.slug}`} className="block py-2.5 hover:text-red-600">
            {c.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Link href="/" aria-label="복싱의모든것 홈" className="shrink-0">
          <Logo />
        </Link>
        <div className="order-3 w-full md:order-none md:max-w-md md:flex-1">
          <Suspense fallback={<div className="h-[38px]" />}>
            <SearchBar />
          </Suspense>
        </div>
      </div>
      <nav className="mx-auto w-full max-w-6xl overflow-x-auto px-4" aria-label="카테고리">
        <Suspense fallback={<CategoryNavSkeleton />}>
          <CategoryNav />
        </Suspense>
      </nav>
    </header>
  );
}
