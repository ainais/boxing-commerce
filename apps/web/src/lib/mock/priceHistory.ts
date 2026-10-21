import type { PricePoint } from "@/lib/types";

const DAYS = 30;

// id 문자열 -> 32bit 시드 (FNV-1a)
function hashSeed(id: string): number {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

// 결정적 PRNG (mulberry32)
function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 최근 30일 일별 최저가. 오늘(daysAgo 0) 값은 항상 currentLowest와 일치한다. */
export function generatePriceHistory(productId: string, currentLowest: number): PricePoint[] {
  const rand = mulberry32(hashSeed(productId));
  const phase = rand() * Math.PI * 2;
  const points: PricePoint[] = [];
  for (let daysAgo = DAYS - 1; daysAgo >= 1; daysAgo--) {
    const trend = 0.03 * Math.sin(daysAgo / 5 + phase);
    const noise = (rand() - 0.5) * 0.12;
    // 과거에는 현재보다 다소 비싼 쪽으로 치우치게(할인 가정)
    const raw = currentLowest * (1 + 0.04 + trend + noise);
    points.push({ daysAgo, price: Math.max(100, Math.round(raw / 100) * 100) });
  }
  points.push({ daysAgo: 0, price: currentLowest });
  return points;
}
