import { Suspense } from "react";
import Link from "next/link";
import { getCategories } from "@/lib/api";
import { SearchBar } from "./SearchBar";

export async function Header() {
  const categories = await getCategories();
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Link href="/" className="text-xl font-extrabold tracking-tight text-gray-900">
          Boxing<span className="text-red-600">Everything</span>
        </Link>
        <div className="order-3 w-full md:order-none md:max-w-md md:flex-1">
          <Suspense fallback={<div className="h-[38px]" />}>
            <SearchBar />
          </Suspense>
        </div>
      </div>
      <nav className="mx-auto w-full max-w-6xl overflow-x-auto px-4" aria-label="카테고리">
        <ul className="flex gap-5 whitespace-nowrap text-sm text-gray-700">
          {categories.map((c) => (
            <li key={c.slug}>
              <Link href={`/products?category=${c.slug}`} className="block py-2.5 hover:text-red-600">
                {c.name}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
