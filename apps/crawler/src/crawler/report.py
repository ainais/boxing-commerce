"""수집 JSONL 분류 리포트: uv run python -m crawler.report --input <jsonl 경로>"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from crawler.classify import PROMOTABLE, UNMATCHED, classify, dedupe


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _counter_lines(counter: Counter, indent: str = "  ") -> list[str]:
    items = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return [f"{indent}{k}: {v}개" for k, v in items]


def _matrix(rows: list[tuple[str, str]]) -> list[str]:
    brands = sorted({b for b, _ in rows})
    cats = sorted({c for _, c in rows})
    counts = Counter(rows)
    width = max([len(b) for b in brands] + [6])
    header = "  " + "brand".ljust(width) + "".join(f" {c:>11}" for c in cats) + f" {'합계':>6}"
    lines = [header]
    for b in brands:
        cells = "".join(f" {counts[(b, c)]:>11}" for c in cats)
        lines.append("  " + b.ljust(width) + cells + f" {sum(counts[(b, c)] for c in cats):>6}")
    return lines


def build_report(
    records: list[dict], samples: int = 15, show_unmatched: str | None = None
) -> str:
    unique = dedupe(records)
    results = [classify(p) for p in unique]
    out: list[str] = []

    out += [
        "== 입력 ==",
        f"입력 행 수: {len(records)}",
        f"dedupe 후 고유 상품 수: {len(unique)}",
        "",
    ]

    promotable = [r for r in results if r.status == PROMOTABLE]
    unmatched = [r for r in results if r.status == UNMATCHED]
    reasons = Counter(r.unmatched_reason for r in unmatched)
    out += ["== 상태 요약 ==", f"PROMOTABLE: {len(promotable)}개", f"UNMATCHED: {len(unmatched)}개"]
    out += _counter_lines(reasons) + [""]

    out += ["== PROMOTABLE 분포 =="]
    out += ["category_slug별:"] + _counter_lines(Counter(r.category_slug for r in promotable))
    out += ["brand별:"] + _counter_lines(Counter(r.brand for r in promotable))
    out += ["brand × category:"]
    out += _matrix([(r.brand or "", r.category_slug or "") for r in promotable]) + [""]

    kinds = Counter(r.category_reason.split(":")[0] for r in promotable)
    out += ["== 분류 근거 (PROMOTABLE) =="] + _counter_lines(kinds) + [""]

    with_code = sum(1 for r in results if r.model_code)
    changed = sum(1 for p, r in zip(unique, results, strict=True) if r.name != p["name"])
    out += [
        "== 모델 코드·정규화 ==",
        f"모델 코드 추출률: {with_code} / {len(results)}",
        f"이름 정규화로 바뀐 상품 수: {changed}",
        "",
    ]

    out += [f"== UNMATCHED 샘플 (사유별 최대 {samples}개) =="]
    for reason in sorted(reasons, key=lambda k: (-reasons[k], str(k))):
        out.append(f"[{reason}] {reasons[reason]}개")
        shown = [
            f"  {p.get('category_no')} | {r.name}"
            for p, r in zip(unique, results, strict=True)
            if r.unmatched_reason == reason
        ][:samples]
        out += shown
    out.append("")

    sold = [(p, r) for p, r in zip(unique, results, strict=True) if p.get("sold_out")]
    out += [
        "== 품절 ==",
        f"품절 상품 수: {len(sold)}",
        f"그중 PROMOTABLE: {sum(1 for _, r in sold if r.status == PROMOTABLE)}",
    ]

    if show_unmatched:
        out += ["", f"== UNMATCHED 전체: {show_unmatched} =="]
        out += [
            f"{p.get('category_no')} | {r.name}"
            for p, r in zip(unique, results, strict=True)
            if r.unmatched_reason == show_unmatched
        ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="crawler.report", description="수집 JSONL 분류 리포트")
    p.add_argument("--input", required=True, type=Path, help="ScrapedProduct JSONL 경로")
    p.add_argument("--samples", type=int, default=15, help="사유별 샘플 개수(기본 15)")
    p.add_argument(
        "--show-unmatched",
        choices=["excluded_accessory", "unknown_brand", "unknown_category"],
        help="해당 사유의 UNMATCHED 전체 목록 출력",
    )
    args = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(_read(args.input), args.samples, args.show_unmatched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
