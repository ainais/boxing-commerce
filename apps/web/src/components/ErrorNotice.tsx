/** API 오류 시 페이지가 크래시하는 대신 보여 주는 안내 */
export function ErrorNotice({
  message = "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
}: {
  message?: string;
}) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-gray-200 bg-white px-4 py-10 text-center text-sm text-gray-600"
    >
      {message}
    </div>
  );
}
