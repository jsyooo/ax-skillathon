#!/usr/bin/env python3
"""Read campaign CSV exports without changing them and print a Markdown review."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path


ALIASES = {
    "campaign": ("Campaign", "캠페인"),
    "ad_group": ("Ad group", "광고그룹"),
    "search_term": ("Search term", "검색어"),
    "cost": ("Cost", "비용"),
    "clicks": ("Clicks", "클릭수"),
    "conversions": ("Conversions", "전환수"),
    "impressions": ("Impressions", "노출수"),
    "budget": ("Budget", "일예산"),
}
REQUIRED = ("campaign", "cost", "clicks", "conversions")


def numeric(value: str | None) -> float:
    cleaned = (value or "").replace(",", "").replace("₩", "").replace("원", "").strip()
    return float(cleaned or 0)


def canonical_headers(headers: list[str]) -> dict[str, str]:
    result = {}
    for field, aliases in ALIASES.items():
        found = next((header for header in headers if header.strip() in aliases), None)
        if found:
            result[field] = found
    return result


def read_rows(path: Path) -> list[dict]:
    if path.suffix.lower() != ".csv":
        raise ValueError(f"CSV만 직접 분석합니다: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    headers = list(rows[0]) if rows else []
    fields = canonical_headers(headers)
    missing = [field for field in REQUIRED if field not in fields]
    if missing:
        raise ValueError(f"필수 열 누락 ({path.name}): {', '.join(missing)}")
    platform = "naver_search_ads" if any("캠페인" in header for header in headers) else "google_ads"
    normalized = []
    for raw in rows:
        row = {field: raw.get(header, "") for field, header in fields.items()}
        row.update({"platform": platform, "source": path.name})
        for field in ("cost", "clicks", "conversions", "impressions", "budget"):
            row[field] = numeric(row.get(field))
        normalized.append(row)
    return normalized


def summary(rows: list[dict]) -> dict:
    return {key: sum(row[key] for row in rows) for key in ("cost", "clicks", "conversions", "budget")}


def candidate_actions(rows: list[dict]) -> list[dict]:
    candidates = []
    by_platform = defaultdict(list)
    for row in rows:
        by_platform[row["platform"]].append(row)
    for platform, items in by_platform.items():
        spend_median = statistics.median([row["cost"] for row in items])
        cvrs = [row["conversions"] / row["clicks"] for row in items if row["clicks"] > 0]
        cvr_median = statistics.median(cvrs) if cvrs else 0
        for row in items:
            target = " > ".join(part for part in (row.get("campaign"), row.get("ad_group"), row.get("search_term")) if part)
            cvr = row["conversions"] / row["clicks"] if row["clicks"] else 0
            if row.get("search_term") and row["cost"] >= spend_median and row["conversions"] == 0:
                candidates.append({"priority": "높음", "target": target, "action": "제외 검토", "evidence": f"{platform} 내부 중앙값보다 높은 비용 {row['cost']:,.0f}, 전환 0", "effect": "낭비 비용 축소 후 전환 가능 검색어에 재배분", "caution": "사업 의도·브랜드 검색어인지 사람 확인", "kpi": "다음 주 비용과 전환수"})
            elif row.get("search_term") and row["conversions"] > 0 and cvr >= cvr_median:
                candidates.append({"priority": "중간", "target": target, "action": "확장 검토", "evidence": f"{platform} 내부 CVR {cvr:.1%}, 전환 {row['conversions']:,.0f}", "effect": "유사 고의도 검색어에서 전환 확대 가능", "caution": "검색 의도와 랜딩페이지 적합성 확인", "kpi": "검색어별 전환수와 CVR"})
    order = {"높음": 0, "중간": 1, "낮음": 2}
    return sorted(candidates, key=lambda item: order[item["priority"]])[:5]


def render(period: str, current: list[dict], previous: list[dict]) -> str:
    now, before = summary(current), summary(previous) if previous else ({}, {})
    conversion_change = "비교 데이터 없음" if not previous else f"{now['conversions'] - before['conversions']:+,.0f}"
    title = "핵심 요약" if period == "weekly" else "월간 추세"
    lines = [f"# {period} 리드 캠페인 분석", "", f"## {title}", f"- 전환수: {now['conversions']:,.0f} (이전 기간 대비 {conversion_change})", f"- 비용: {now['cost']:,.0f}", "- 제약: 총예산 유지", "- 원칙: 플랫폼 간 CPC/CPA 직접 비교 금지", "", "## 추천 액션", "", "| 우선순위 | 대상 | 권장 조치 | 근거 | 기대 효과 | 주의점 | 다음 확인 KPI |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for item in candidate_actions(current):
        lines.append("| {priority} | {target} | {action} | {evidence} | {effect} | {caution} | {kpi} |".format(**item))
    if len(lines) == 10:
        lines.append("| 낮음 | 전체 계정 | 관찰 지속 | 충분한 액션 후보 없음 | 다음 기간 판단 근거 확보 | 데이터 기간과 전환 지연 확인 | 전환수·비용 |")
    lines.extend(["", "## 사람 검토", "- 추천은 실행하지 않는다. 검색어 의도, 사업 제약, 전환 정의를 검토한 뒤 사람이 반영한다.", "- 예산 증액은 내부 재배분·검색어 정리·구조 개선 뒤에만 마지막 대안으로 검토한다."])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=("weekly", "monthly"), required=True)
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--previous", nargs="*")
    args = parser.parse_args()
    try:
        current = [row for item in args.input for row in read_rows(Path(item))]
        previous = [row for item in (args.previous or []) for row in read_rows(Path(item))]
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    print(render(args.period, current, previous))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
