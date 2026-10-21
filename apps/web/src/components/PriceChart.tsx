import type { PricePoint } from "@/lib/types";

const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

const W = 640;
const H = 200;
const PAD = { top: 16, right: 12, bottom: 24, left: 12 };

/** 라이브러리 없이 그리는 가벼운 인라인 SVG 꺾은선 차트 (최근 30일 최저가) */
export function PriceChart({ history }: { history: PricePoint[] }) {
  const prices = history.map((p) => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const current = history[history.length - 1].price;
  const span = max - min || 1;

  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const x = (i: number) => PAD.left + (history.length === 1 ? 0 : (i / (history.length - 1)) * innerW);
  const y = (price: number) => PAD.top + (1 - (price - min) / span) * innerH;

  const points = history.map((p, i) => `${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join(" ");
  const minIdx = prices.indexOf(min);
  const maxIdx = prices.indexOf(max);
  const last = history.length - 1;

  return (
    <div>
      <dl className="mb-3 grid grid-cols-3 gap-2 text-center text-sm">
        <div className="rounded-md bg-gray-50 p-2">
          <dt className="text-xs text-gray-500">30일 최저</dt>
          <dd className="font-semibold text-blue-600">{won(min)}</dd>
        </div>
        <div className="rounded-md bg-gray-50 p-2">
          <dt className="text-xs text-gray-500">30일 최고</dt>
          <dd className="font-semibold text-gray-900">{won(max)}</dd>
        </div>
        <div className="rounded-md bg-gray-50 p-2">
          <dt className="text-xs text-gray-500">현재</dt>
          <dd className="font-semibold text-red-600">{won(current)}</dd>
        </div>
      </dl>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label={`최근 30일 최저가 추이. 최저 ${won(min)}, 최고 ${won(max)}, 현재 ${won(current)}`}
      >
        <line x1={PAD.left} x2={W - PAD.right} y1={y(min)} y2={y(min)} stroke="#e5e7eb" strokeDasharray="4 4" />
        <line x1={PAD.left} x2={W - PAD.right} y1={y(max)} y2={y(max)} stroke="#e5e7eb" strokeDasharray="4 4" />
        <polyline points={points} fill="none" stroke="#374151" strokeWidth="2" strokeLinejoin="round" />
        <circle cx={x(minIdx)} cy={y(min)} r="4" fill="#2563eb" />
        <circle cx={x(maxIdx)} cy={y(max)} r="4" fill="#6b7280" />
        <circle cx={x(last)} cy={y(current)} r="5" fill="#dc2626" />
        <text x={PAD.left} y={H - 6} fontSize="12" fill="#6b7280">
          30일 전
        </text>
        <text x={W - PAD.right} y={H - 6} fontSize="12" fill="#6b7280" textAnchor="end">
          오늘
        </text>
      </svg>
    </div>
  );
}
