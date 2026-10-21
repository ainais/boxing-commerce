/** 외부 이미지 대신 쓰는 placeholder (색 블록 + 단순 SVG 아이콘) */
export function ProductImage({ color, label }: { color: string; label: string }) {
  return (
    <div
      className="flex aspect-square w-full items-center justify-center"
      style={{ backgroundColor: color }}
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
