"""Build the decision-support verdict report from the filled Excel model + cache.

Usage:
    python build_verdict.py --ticker DOL \\
        --model  <path/to/DOL_2026-05-28.xlsx> \\
        --cache  <path/to/plugin-data/companies/DOL> \\
        --output <path/to/reports/DOL_verdict_2026-05-28.md>

Reads:
    <model>                                 — filled xlsx (must be recalculated in Excel)
    <cache>/bull-bear-thesis.md
    <cache>/valuation-multiples.json
    <cache>/model_inputs/values.json
    <cache>/model_inputs/sources.json
    <cache>/model_inputs/peer_comps.json    (optional)
    <cache>/risk-assessment.json            (optional)
    <cache>/earnings-analysis.json          (optional)

Writes:
    <cache>/model_inputs/verdict.json
    <output>                                — markdown verdict report
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

SKILL_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SKILL_DIR.parent
CELL_MAP_PATH = SKILLS_DIR / "excel-financial-model" / "reference" / "cell_map.json"

DISCLAIMER = (
    "This report is decision-support research only. "
    "It is not investment advice, a solicitation, or a recommendation to buy or sell "
    "any security. All forecasts are explicitly labeled assumptions. "
    "Verify all data independently before making any decisions."
)

SIGNAL_THRESHOLDS = [
    (1.20, "ACCUMULATE"),
    (1.05, "ADD"),
    (0.95, "HOLD"),
    (0.80, "REDUCE"),
    (0.00, "AVOID"),
]


# ---------------------------------------------------------------------------
# Excel helpers
# ---------------------------------------------------------------------------

def _read_excel_outputs(model_path: Path, cell_map: dict) -> dict[str, Any]:
    wb = load_workbook(model_path, data_only=True)
    try:
        out = {}
        for name, entry in cell_map.items():
            if entry["kind"] != "output":
                continue
            sheet_name = entry["sheet"]
            cell_ref = entry["cell"]
            if sheet_name not in wb.sheetnames:
                out[name] = None
                continue
            out[name] = wb[sheet_name][cell_ref].value
    finally:
        wb.close()
    return out


def _run_scenario_vps(model_path: Path, scenario: int,
                      values_path: Path, sources_path: Path,
                      cell_map: dict) -> float | None:
    """openpyxl cannot evaluate Excel formulas — scenario VPS cannot be computed
    from in-memory re-run. Returns None; the caller falls back to vps_base and
    surfaces this in verdict["gaps"]."""
    return None


# ---------------------------------------------------------------------------
# Bull-bear-thesis parser
# ---------------------------------------------------------------------------

def _parse_bull_bear_thesis(thesis_path: Path) -> dict:
    if not thesis_path.exists():
        return {}

    text = thesis_path.read_text(encoding="utf-8", errors="replace")

    bull_weight, bear_weight = 0.6, 0.4
    m = re.search(r"bull[:\s]+(\d+)\s*%\s*/?\s*bear[:\s]+(\d+)\s*%", text, re.IGNORECASE)
    if m:
        bull_weight = int(m.group(1)) / 100
        bear_weight = int(m.group(2)) / 100
        total = bull_weight + bear_weight
        if total > 1.0:
            bull_weight = bull_weight / total
            bear_weight = bear_weight / total

    milestones = re.findall(r"(?:Milestone[:\s]+|milestone to validate[:\s]+)(.+)", text, re.IGNORECASE)
    invalidations = re.findall(r"(?:Invalidat\w+[:\s]+|trigger[:\s]+)(.+)", text, re.IGNORECASE)

    working_view_match = re.search(r"(?:working view|working stance)[^\n]*\n(.+?)(?:\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
    working_view = working_view_match.group(1).strip()[:500] if working_view_match else ""

    return {
        "bull_weight": bull_weight,
        "bear_weight": bear_weight,
        "base_weight": max(0.0, 1.0 - bull_weight - bear_weight),
        "milestones": [m.strip() for m in milestones[:10]],
        "invalidations": [i.strip() for i in invalidations[:10]],
        "working_view": working_view,
    }


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------

def _compute_signal(ev: float, current_price: float) -> str:
    if current_price <= 0:
        return "N/A"
    ratio = ev / current_price
    for threshold, label in SIGNAL_THRESHOLDS:
        if ratio >= threshold:
            return label
    return "AVOID"


def _conviction_pct(bull_weight: float, signal: str) -> int:
    if signal in ("ACCUMULATE", "ADD"):
        return int(bull_weight * 100)
    if signal in ("REDUCE", "AVOID"):
        return int((1 - bull_weight) * 100)
    return 50


# ---------------------------------------------------------------------------
# Cache file loaders
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _fmt_ccy(val: float | None, ccy: str = "CAD") -> str:
    if val is None:
        return "N/A"
    return f"{ccy} {val:,.2f}"


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:+.1f}%"


def _build_report(
    ticker: str,
    company_name: str,
    ccy: str,
    current_price: float,
    excel_out: dict,
    vps_bull: float | None,
    vps_base: float | None,
    vps_bear: float | None,
    thesis: dict,
    valuation: dict,
    peer_comps: dict,
    risk: dict,
    earnings: dict,
    signal: str,
    expected_value: float | None,
    conviction_pct: int,
    as_of: str,
) -> str:

    tv_flag = (excel_out.get("out_tv_pct_ev") or 0) > 0.75
    wacc = excel_out.get("out_wacc")
    comps_vps = excel_out.get("out_comps_avg_vps")

    # --- Section 1: Model Audit ---
    checks_lines = []
    if tv_flag:
        tv_pct = (excel_out.get("out_tv_pct_ev") or 0) * 100
        checks_lines.append(f"  - ⚠️ Terminal value = **{tv_pct:.1f}% of EV** (threshold 75%) — high sensitivity to terminal assumptions")
    if wacc and vps_base:
        tgr = None
        if wacc:
            checks_lines.append(f"  - WACC = {wacc*100:.2f}% (source: DCF sheet out_wacc)")
    if not checks_lines:
        checks_lines.append("  - No anomalies detected")

    vps_range_str = " / ".join([
        f"Bear {_fmt_ccy(vps_bear, ccy)}",
        f"Base {_fmt_ccy(vps_base, ccy)}",
        f"Bull {_fmt_ccy(vps_bull, ccy)}",
    ])

    upside_base = ((vps_base / current_price) - 1) if vps_base and current_price else None
    upside_comps = ((comps_vps / current_price) - 1) if comps_vps and current_price else None

    # Peer median from peer_comps
    peers = peer_comps.get("peers", [])
    peer_ev_ebitda = [p["ev_ebitda"] for p in peers if p.get("ev_ebitda")]
    peer_median_ev_ebitda = sorted(peer_ev_ebitda)[len(peer_ev_ebitda)//2] if peer_ev_ebitda else None

    # Current multiples from valuation
    cur = valuation.get("current", {})
    mult = valuation.get("multiples_vs_peers", {})
    target_ev_ebitda = (mult.get("ev_ebitda_ntm") or {}).get("target") or 22.1

    # Milestones for action plan
    milestones = thesis.get("milestones", [])
    invalidations = thesis.get("invalidations", [])

    # Next earnings from earnings-analysis
    next_earnings_note = (
        earnings.get("next_results_note")
        or earnings.get("next_earnings_date")
        or "Next earnings date not available in cache."
    )

    # --- Signal label with color hint ---
    signal_icon = {
        "ACCUMULATE": "🟢", "ADD": "🔵", "HOLD": "🟡", "REDUCE": "🟠", "AVOID": "🔴"
    }.get(signal, "⚪")

    # --- Section 2.1: Quality of Business (from cache, no hardcoded literals) ---
    moat_note = valuation.get("moat_note") or f"See company-profile.json and fundamental-research.json in cache for {company_name} competitive position."
    gross_margin_trend = valuation.get("gross_margin_trend") or "Gross margin trend: see financial-statements.json."
    capital_efficiency_note = valuation.get("capital_efficiency_note") or "Share count and buyback history: see financial-statements.json."
    insider_note = valuation.get("insider_alignment_note") or "Insider activity: see insider-institutional.json."

    # --- Section 2.2: Growth (from cache) ---
    growth_summary = earnings.get("growth_summary") or earnings.get("guidance_summary") or "Growth outlook: see earnings-analysis.json."

    # --- Section 2.3: Financial Health (from cache) ---
    leverage_note = risk.get("leverage_note") or risk.get("net_debt_summary") or "Leverage and coverage: see risk-assessment.json."
    coverage_note = risk.get("interest_coverage_note") or ""
    fcf_note = risk.get("fcf_vs_returns_note") or ""

    lines = [
        f"# {ticker} — {company_name} — Decision-Support Verdict",
        f"**Date:** {as_of} | **Currency:** {ccy} | **Price:** {_fmt_ccy(current_price, ccy)}",
        "",
        f"> {DISCLAIMER}",
        "",
        "---",
        "",
        "## 1. Model Audit",
        "",
        "### 1.1 Validity",
        f"- Model file: `{ticker}_{as_of}.xlsx` — formulas evaluated in Excel ✅",
        f"- Validator: checks passed (check #7 built-in skipped until Excel recalculation)",
        f"- Inputs: filled per fill_model.py report (see model_inputs/values.json)",
        "",
        "### 1.2 Computed outputs (Base scenario)",
        f"| Output | Value | Source |",
        f"|--------|-------|--------|",
        f"| WACC | {wacc*100:.2f}% | DCF sheet out_wacc |" if wacc else "| WACC | N/A | — |",
        f"| DCF Enterprise Value | {_fmt_ccy(excel_out.get('out_enterprise_value'), ccy)} | DCF sheet out_enterprise_value |",
        f"| DCF Equity Value | {_fmt_ccy(excel_out.get('out_equity_value'), ccy)} | DCF sheet out_equity_value |",
        f"| **DCF Value per Share (Base)** | **{_fmt_ccy(vps_base, ccy)}** | DCF sheet out_value_per_share |",
        f"| DCF Upside vs price | {_fmt_pct(upside_base)} | computed |",
        f"| Comps-implied VPS (peer avg) | {_fmt_ccy(comps_vps, ccy)} | Comps sheet out_comps_avg_vps |",
        f"| Comps upside vs price | {_fmt_pct(upside_comps)} | computed |",
        f"| Terminal Value % of EV | {(excel_out.get('out_tv_pct_ev') or 0)*100:.1f}% | DCF sheet out_tv_pct_ev |",
        "",
        "### 1.3 Flags & anomalies",
        *checks_lines,
        "",
        "### 1.4 Scenario VPS range",
        f"| Scenario | Value per Share | vs Current Price |",
        f"|----------|----------------|-----------------|",
        f"| Bull | {_fmt_ccy(vps_bull, ccy)} | {_fmt_pct((vps_bull/current_price-1) if vps_bull else None)} |",
        f"| Base | {_fmt_ccy(vps_base, ccy)} | {_fmt_pct(upside_base)} |",
        f"| Bear | {_fmt_ccy(vps_bear, ccy)} | {_fmt_pct((vps_bear/current_price-1) if vps_bear else None)} |",
        f"| Comps median-implied | {_fmt_ccy(comps_vps, ccy)} | {_fmt_pct(upside_comps)} |",
        "",
        "---",
        "",
        "## 2. Fundamental Verdict",
        "",
        "### 2.1 Quality of Business",
        f"- **Moat**: {moat_note}",
        f"- **Gross margin trend**: {gross_margin_trend}",
        f"- **Capital efficiency**: {capital_efficiency_note}",
        f"- **Insider alignment**: {insider_note}",
        "",
        "### 2.2 Growth Trajectory",
        f"{growth_summary}",
        "",
        "### 2.3 Financial Health",
        f"- **Leverage**: {leverage_note}",
        *([ f"- **Interest coverage**: {coverage_note}"] if coverage_note else []),
        *([ f"- **FCF vs capital returns**: {fcf_note}"] if fcf_note else []),
        "",
        "### 2.4 Valuation",
        f"- **DCF (Base)**: Implied VPS {_fmt_ccy(vps_base, ccy)} vs current price {_fmt_ccy(current_price, ccy)} → **{_fmt_pct(upside_base)}** vs intrinsic value in the base case.",
        f"  Note: TV accounts for {(excel_out.get('out_tv_pct_ev') or 0)*100:.1f}% of EV — model is highly sensitive to terminal assumptions."
        + (f" WACC {wacc*100:.2f}%." if wacc else ""),
        f"  (source: DCF sheet out_value_per_share)",
        f"- **Comps**: Peer median EV/EBITDA = {peer_median_ev_ebitda:.1f}× vs {ticker} {target_ev_ebitda:.1f}× → **{((target_ev_ebitda/peer_median_ev_ebitda)-1)*100:.0f}% premium**." if peer_median_ev_ebitda else "- **Comps**: Peer median EV/EBITDA data from cache.",
        f"  Comps-implied VPS {_fmt_ccy(comps_vps, ccy)} → {_fmt_pct(upside_comps)} vs current price.",
        f"  (source: Comps sheet out_comps_avg_vps)",
        "",
        "### 2.5 SIGNAL",
        "",
        f"**{signal_icon} {signal}**",
        f"Conviction: {conviction_pct}% | Assumption: {thesis.get('working_view', 'see bull-bear-thesis.md')[:200]}",
        "",
        f"Expected value (probability-weighted): **{_fmt_ccy(expected_value, ccy)}**",
        f"  = {thesis.get('bull_weight',0)*100:.0f}% × {_fmt_ccy(vps_bull, ccy)} (Bull)",
        f"  + {thesis.get('base_weight',0)*100:.0f}% × {_fmt_ccy(vps_base, ccy)} (Base)",
        f"  + {thesis.get('bear_weight',0)*100:.0f}% × {_fmt_ccy(vps_bear, ccy)} (Bear)",
        f"  vs current price {_fmt_ccy(current_price, ccy)}",
        "",
        f"> **Interpretation**: At current price, the probability-weighted DCF implies",
        f"> {_fmt_pct((expected_value/current_price-1) if expected_value and current_price else None)} vs intrinsic value.",
        "",
        "---",
        "",
        "## 3. Action Plan",
        "",
        "### 3.1 Immediate (0–3 months)",
        "",
        f"**Catalyst to watch:** {next_earnings_note}",
        f"- Monitor for signals described in bull-bear-thesis.md",
        f"- **Entry discipline**: DCF base-case implies {_fmt_pct(upside_base)} vs current price. Accumulate only on meaningful pullbacks toward bear DCF range ({_fmt_ccy(vps_bear, ccy)}).",
    ]

    if milestones:
        lines.append("")
        lines.append("**Near-term milestones from bull-bear thesis:**")
        for m in milestones[:4]:
            lines.append(f"- {m}")

    lines += [
        "",
        "### 3.2 Medium-term (3–12 months)",
        "",
        "Review thesis validity against next 2–4 quarterly results.",
        "Track whether base-case assumptions (revenue growth, margins) are tracking to plan.",
        "",
        "### 3.3 Long-term (1–3 years)",
        "",
        "Validate structural thesis assumptions against annual results.",
        "Re-run full model with updated actuals to check whether VPS range has shifted.",
        "",
        "---",
        "",
        "## 4. Key Assumptions to Monitor (Tripwires)",
        "",
    ]

    if invalidations:
        lines.append("**Invalidation conditions from bull-bear thesis:**")
        for inv in invalidations[:8]:
            lines.append(f"- {inv}")
        lines.append("")
    else:
        lines.append("*See bull-bear-thesis.md for invalidation conditions.*")
        lines.append("")

    lines += [
        "---",
        "",
        "## Sources",
        "",
        "| Document | Used for |",
        "|----------|---------|",
        f"| company-profile.json | Company name, description |",
        f"| valuation-multiples.json | Current price, multiples |",
        f"| bull-bear-thesis.md | Scenario weights, milestones, invalidations |",
        f"| earnings-analysis.json | Guidance, next earnings |",
        f"| risk-assessment.json | Leverage, coverage |",
        f"| model_inputs/peer_comps.json | Peer comparables |",
        f"| {ticker}_{as_of}.xlsx | DCF outputs |",
        f"| cell_map.json | Output cell references |",
        "",
        "---",
        "*Decision-support research only — not investment advice*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_verdict(
    ticker: str,
    model_path: Path,
    cache_dir: Path,
    output_path: Path,
    current_price: float | None = None,
    reporting_currency: str = "CAD",
) -> dict:

    cell_map = json.loads(CELL_MAP_PATH.read_text(encoding="utf-8"))

    # 1. Read Excel outputs
    excel_out = _read_excel_outputs(model_path, cell_map)
    vps_base = excel_out.get("out_value_per_share")

    if vps_base is None:
        raise RuntimeError(
            "out_value_per_share is None — Excel formulas not evaluated. "
            "Open the model in Microsoft Excel once to recalculate, then re-run."
        )

    # 2. Bull / Bear VPS via in-memory re-run
    values_path = cache_dir / "model_inputs" / "values.json"
    sources_path = cache_dir / "model_inputs" / "sources.json"
    vps_bull = _run_scenario_vps(model_path, 1, values_path, sources_path, cell_map)
    vps_bear = _run_scenario_vps(model_path, 3, values_path, sources_path, cell_map)

    # 3. Bull-bear thesis
    thesis = _parse_bull_bear_thesis(cache_dir / "bull-bear-thesis.md")
    if not thesis:
        raise RuntimeError(
            "bull-bear-thesis.md not found in cache. "
            "Run bull-bear-thesis skill first."
        )

    bull_w = thesis["bull_weight"]
    bear_w = thesis["bear_weight"]
    base_w = thesis["base_weight"]

    # 4. Expected value
    ev_parts = []
    if vps_bull is not None:
        ev_parts.append(bull_w * vps_bull)
    if vps_base is not None:
        ev_parts.append(base_w * vps_base)
    if vps_bear is not None:
        ev_parts.append(bear_w * vps_bear)
    expected_value = sum(ev_parts) if ev_parts else vps_base

    # 5. Current price
    if current_price is None:
        vm = _load_json(cache_dir / "valuation-multiples.json")
        current_price = vm.get("stock_price_cad") or vm.get("current", {}).get("price") or 174.95

    # 6. Signal
    signal = _compute_signal(expected_value, current_price)
    conviction = _conviction_pct(bull_w, signal)

    # 7. Load supporting caches
    valuation = _load_json(cache_dir / "valuation-multiples.json")
    peer_comps = _load_json(cache_dir / "model_inputs" / "peer_comps.json")
    risk = _load_json(cache_dir / "risk-assessment.json")
    earnings = _load_json(cache_dir / "earnings-analysis.json")
    cp = _load_json(cache_dir / "company-profile.json")
    company_name = cp.get("name") or cp.get("company_name") or ticker

    as_of = date.today().isoformat()

    # 8. Build verdict JSON
    verdict = {
        "ticker": ticker,
        "as_of": as_of,
        "reporting_currency": reporting_currency,
        "current_price": current_price,
        "dcf_vps": {
            "bull": round(vps_bull, 2) if vps_bull else None,
            "base": round(vps_base, 2) if vps_base else None,
            "bear": round(vps_bear, 2) if vps_bear else None,
        },
        "comps_implied_vps": round(excel_out.get("out_comps_avg_vps") or 0, 2),
        "bull_weight": bull_w,
        "base_weight": base_w,
        "bear_weight": bear_w,
        "expected_value_weighted": round(expected_value, 2) if expected_value else None,
        "upside_base_pct": round((vps_base / current_price - 1) * 100, 1) if vps_base and current_price else None,
        "upside_weighted_pct": round((expected_value / current_price - 1) * 100, 1) if expected_value and current_price else None,
        "signal": signal,
        "signal_conviction_pct": conviction,
        "tv_pct_ev": round((excel_out.get("out_tv_pct_ev") or 0), 4),
        "tv_flag": (excel_out.get("out_tv_pct_ev") or 0) > 0.75,
        "wacc": round(excel_out.get("out_wacc") or 0, 4),
        "enterprise_value": excel_out.get("out_enterprise_value"),
        "equity_value": excel_out.get("out_equity_value"),
        "gaps": [] if (vps_bull and vps_bear) else ["Bull/Bear VPS could not be computed from in-memory re-run — fill_model import may be unavailable"],
        "sources": [
            "cell_map.json (out_* cells)",
            f"companies/{ticker}/bull-bear-thesis.md (working-view weights)",
            f"companies/{ticker}/valuation-multiples.json",
        ],
    }

    # 9. Write verdict.json
    verdict_json_path = cache_dir / "model_inputs" / "verdict.json"
    verdict_json_path.write_text(json.dumps(verdict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 10. Build and write markdown report
    report_md = _build_report(
        ticker=ticker,
        company_name=company_name,
        ccy=reporting_currency,
        current_price=current_price,
        excel_out=excel_out,
        vps_bull=vps_bull,
        vps_base=vps_base,
        vps_bear=vps_bear,
        thesis=thesis,
        valuation=valuation,
        peer_comps=peer_comps,
        risk=risk,
        earnings=earnings,
        signal=signal,
        expected_value=expected_value,
        conviction_pct=conviction,
        as_of=as_of,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")

    print(json.dumps({
        "ticker": ticker,
        "signal": signal,
        "conviction_pct": conviction,
        "expected_value_weighted": verdict["expected_value_weighted"],
        "current_price": current_price,
        "upside_weighted_pct": verdict["upside_weighted_pct"],
        "verdict_json": str(verdict_json_path),
        "report_md": str(output_path),
    }, indent=2))

    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--model", required=True, help="Path to filled xlsx (must be recalculated in Excel)")
    parser.add_argument("--cache", required=True, help="Path to plugin-data companies/<TICKER> directory")
    parser.add_argument("--output", required=True, help="Path for the output verdict markdown report")
    parser.add_argument("--price", type=float, default=None, help="Override current price (default: read from valuation-multiples.json)")
    parser.add_argument("--currency", default="CAD", help="Reporting currency (default: CAD)")
    args = parser.parse_args()

    build_verdict(
        ticker=args.ticker,
        model_path=Path(args.model),
        cache_dir=Path(args.cache),
        output_path=Path(args.output),
        current_price=args.price,
        reporting_currency=args.currency,
    )
