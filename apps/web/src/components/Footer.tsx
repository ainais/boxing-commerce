import { Logo } from "./Logo";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="mx-auto max-w-6xl space-y-3 px-4 py-6">
        <Logo />
        <p className="text-xs text-gray-500">
          복싱의모든것은 가격 비교 정보를 제공하며, 주문·결제는 각 판매처에서 이루어집니다.
        </p>
      </div>
    </footer>
  );
}
