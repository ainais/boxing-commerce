"use client";

import Image from "next/image";
import { useState } from "react";

const PLACEHOLDER_COLORS = [
  "#b91c1c",
  "#1d4ed8",
  "#047857",
  "#7c3aed",
  "#b45309",
  "#0f766e",
  "#be185d",
  "#4b5563",
];

interface Props {
  /** 외부 상품 이미지 주소. null이거나 로드에 실패하면 placeholder를 보여 준다 */
  src: string | null;
  label: string;
  /** placeholder 색 선택용(상품 id) */
  seed: number;
  sizes?: string;
  /** above-the-fold 이미지(LCP 후보)만 true. 나머지는 lazy 유지 */
  eager?: boolean;
}

/** 상품 이미지. 없거나 실패하면 색 블록 + 단순 SVG 아이콘 placeholder */
export function ProductImage({
  src,
  label,
  seed,
  sizes = "(min-width: 1024px) 25vw, 50vw",
  eager = false,
}: Props) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);

  if (src && failedSrc !== src) {
    return (
      <div className="relative aspect-square w-full bg-white">
        <Image
          src={src}
          alt={label}
          fill
          sizes={sizes}
          loading={eager ? "eager" : "lazy"}
          className="object-contain"
          onError={() => setFailedSrc(src)}
        />
      </div>
    );
  }

  return (
    <div
      className="flex aspect-square w-full items-center justify-center"
      style={{ backgroundColor: PLACEHOLDER_COLORS[Math.abs(seed) % PLACEHOLDER_COLORS.length] }}
      role="img"
      aria-label={label}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-1/3 w-1/3 text-white/70"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
      >
        <path d="M7 11V6a3 3 0 0 1 6 0v1h2a4 4 0 0 1 4 4v4a5 5 0 0 1-5 5h-3a5 5 0 0 1-5-5v-3z" />
      </svg>
    </div>
  );
}
