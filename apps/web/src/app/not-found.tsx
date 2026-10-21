import Image from "next/image";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center py-12 text-center">
      <Image
        src="/brand/mascot.png"
        alt="복싱 글러브를 낀 고양이 마스코트"
        width={240}
        height={240}
        className="h-auto w-48 md:w-60"
      />
      <h1 className="mt-4 text-xl font-bold text-gray-900">페이지를 찾을 수 없어요</h1>
      <p className="mt-1 text-sm text-gray-500">주소가 바뀌었거나 없는 상품일 수 있어요</p>
      <Link
        href="/"
        className="mt-5 inline-block rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        홈으로 가기
      </Link>
    </div>
  );
}
