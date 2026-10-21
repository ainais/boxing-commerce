import Image from "next/image";

export function Logo() {
  return (
    <span className="inline-flex items-center gap-2">
      <Image
        src="/brand/logo-icon.png"
        alt="복싱의모든것"
        width={36}
        height={36}
        className="h-7 w-7 shrink-0 md:h-9 md:w-9"
      />
      <span className="whitespace-nowrap text-lg font-extrabold tracking-tighter md:text-xl">
        <span className="text-[#111827]">복싱의</span>
        <span className="text-[#DC2626]">모든것</span>
      </span>
    </span>
  );
}
