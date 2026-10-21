import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-lg font-bold text-gray-900">페이지를 찾을 수 없습니다.</h1>
      <p className="mt-1 text-sm text-gray-500">주소가 잘못되었거나 상품이 더 이상 없습니다.</p>
      <Link
        href="/products"
        className="mt-4 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        상품 목록으로
      </Link>
    </div>
  );
}
