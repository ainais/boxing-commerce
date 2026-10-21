"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export function SearchBar() {
  const q = useSearchParams().get("q") ?? "";
  // URL의 검색어가 바뀌면 입력창도 새 값으로 다시 그린다
  return <SearchForm key={q} initialQuery={q} />;
}

function SearchForm({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const [q, setQ] = useState(initialQuery);

  return (
    <form
      role="search"
      className="flex w-full"
      onSubmit={(e) => {
        e.preventDefault();
        const query = q.trim();
        if (query) router.push(`/products?q=${encodeURIComponent(query)}`);
      }}
    >
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="복싱용품 검색"
        aria-label="상품 검색"
        className="min-w-0 flex-1 rounded-l-md border border-r-0 border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
      />
      <button
        type="submit"
        className="rounded-r-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        검색
      </button>
    </form>
  );
}
