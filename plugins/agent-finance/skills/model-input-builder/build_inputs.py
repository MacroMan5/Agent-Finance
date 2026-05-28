"""Transform MCP JSON caches into values.json + sources.json for fill_model.py.

Usage:
    python build_inputs.py --ticker AAPL [--cache-dir PATH] [--output-dir PATH]

Reads from:
    <cache_dir>/financial-statements.json
    <cache_dir>/valuation-multiples.json
    <cache_dir>/earnings-analysis.json
    <cache_dir>/fundamental-research.json
    <cache_dir>/macro-context.json

Writes to:
    <output_dir>/values.json
    <output_dir>/sources.json

MISSING values are never silently substituted. Every gap is recorded
explicitly as {"missing": "<reason>"} in values.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent
EXCEL_SKILL_DIR = SKILL_DIR.parent / "excel-financial-model"
CELL_MAP_PATH = EXCEL_SKILL_DIR / "reference" / "cell_map.json"
MCP_TO_LOGICAL_PATH = SKILL_DIR / "reference" / "mcp_to_logical.json"
SCENARIO_DELTAS_PATH = SKILL_DIR / "reference" / "scenario_deltas.json"

PLUGIN_DATA = Path(os.environ.get("CLAUDE_PLUGIN_DATA", Path.home() / ".claude" / "data" / "agent-finance"))
RUN_DATE = os.environ.get("RUN_DATE", "")


def _cache_dir(ticker: str, override: str | None) -> Path:
    if override:
        return Path(override)
    return PLUGIN_DATA / "companies" / ticker.upper()


def _output_dir(ticker: str, override: str | None) -> Path:
    if override:
        return Path(override)
    return PLUGIN_DATA / "companies" / ticker.upper() / "model_inputs"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _resolve_path(data: Any, path_expr: str) -> Any:
    """Navigate a JSON structure using a simple path like 'annual[-1].gross_margin'.

    Supports:
        key.subkey
        array[-1]  (negative indexing on lists)
        array[0]
        mean(array[*].field)  — arithmetic mean of a field across all list items
    """
    if path_expr is None:
        return None

    # mean(array[*].field) pattern
    m = re.match(r"^mean\((.+)\[[\*]\]\.(.+)\)$", path_expr)
    if m:
        arr_path = m.group(1)
        field = m.group(2)
        arr = _resolve_path(data, arr_path)
        if not isinstance(arr, list):
            return None
        vals = [item.get(field) for item in arr if isinstance(item, dict) and item.get(field) is not None]
        if not vals:
            return None
        return statistics.mean(float(v) for v in vals)

    parts = path_expr.split(".")
    current = data
    for part in parts:
        if current is None:
            return None
        idx_m = re.match(r"^(.+)\[(-?\d+)\]$", part)
        if idx_m:
            key = idx_m.group(1)
            idx = int(idx_m.group(2))
            current = current.get(key) if isinstance(current, dict) else None
            if isinstance(current, list):
                try:
                    current = current[idx]
                except IndexError:
                    current = None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _apply_transform(value: Any, transform: str) -> Any:
    if value is None:
        return None
    if transform == "identity":
        return float(value)
    if transform == "pct":
        # If value looks like it's already in decimal form (< 1.0), keep it.
        v = float(value)
        return v / 100.0 if v > 1.5 else v
    return value


def build_inputs(ticker: str, cache_dir_override: str | None = None, output_dir_override: str | None = None) -> dict:
    cache_dir = _cache_dir(ticker, cache_dir_override)
    output_dir = _output_dir(ticker, output_dir_override)

    cell_map = json.loads(CELL_MAP_PATH.read_text(encoding="utf-8"))
    mcp_map = json.loads(MCP_TO_LOGICAL_PATH.read_text(encoding="utf-8"))
    deltas = json.loads(SCENARIO_DELTAS_PATH.read_text(encoding="utf-8"))

    # Load all cache files (missing files produce None, not errors).
    caches: dict[str, Any] = {}
    for fname in [
        "financial-statements.json",
        "valuation-multiples.json",
        "earnings-analysis.json",
        "fundamental-research.json",
        "macro-context.json",
    ]:
        caches[fname] = _load_json(cache_dir / fname)

    base_values: dict[str, Any] = {}
    base_sources: dict[str, str] = {}

    # --- Resolve base inputs ---
    for name, mapping in mcp_map.items():
        if name not in cell_map or cell_map[name]["kind"] != "input":
            continue

        # Constant values (no MCP lookup needed).
        if mapping.get("transform") == "constant":
            base_values[name] = mapping["constant_value"]
            base_sources[name] = mapping.get("note", "constant")
            continue

        src_file = mapping.get("source_file")
        if src_file is None:
            continue

        cache_data = caches.get(src_file)
        raw = None

        if cache_data is not None:
            raw = _resolve_path(cache_data, mapping["json_path"])

        # Try fallback if primary path failed.
        if raw is None and mapping.get("fallback"):
            fallback = mapping["fallback"]
            if fallback.startswith("mean("):
                raw = _resolve_path(cache_data, fallback) if cache_data else None
            else:
                try:
                    raw = float(fallback)
                except (ValueError, TypeError):
                    raw = None

        if raw is None:
            reason = (
                f"{src_file} not found in cache"
                if cache_data is None
                else f"{mapping['json_path']} returned null in {src_file}"
            )
            base_values[name] = {"missing": reason}
            base_sources[name] = f"MISSING: {reason}"
        else:
            transformed = _apply_transform(raw, mapping.get("transform", "identity"))
            base_values[name] = transformed
            base_sources[name] = (
                f"financial-datasets:{src_file.replace('.json','')} "
                f"ticker={ticker.upper()} as-of={RUN_DATE or 'latest'}"
            )

    # --- Derive bull/bear from base ---
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}

    for name, entry in cell_map.items():
        if entry["kind"] != "input":
            continue
        scenario = entry.get("scenario")
        metric = entry.get("metric", "")

        if scenario == "base" or scenario is None:
            values[name] = base_values.get(name, {"missing": "not in mcp_to_logical.json"})
            sources[name] = base_sources.get(name, f"MISSING: {name} not in mcp_to_logical.json")
        elif scenario in ("bull", "bear"):
            base_name = name.replace(f"_{scenario}", "_base")
            base_val = base_values.get(base_name)

            if isinstance(base_val, dict) and "missing" in base_val:
                # Base is missing — bull/bear are also missing.
                reason = f"base ({base_name}) is MISSING: {base_val['missing']}"
                values[name] = {"missing": reason}
                sources[name] = f"MISSING: {reason}"
                continue

            if base_val is None:
                reason = f"base input {base_name} not mapped"
                values[name] = {"missing": reason}
                sources[name] = f"MISSING: {reason}"
                continue

            # Find delta for this metric.
            delta_entry = deltas.get(metric)
            if delta_entry is None:
                # No delta configured — use base value for both scenarios.
                values[name] = base_val
                sources[name] = f"derived from {base_name} (no delta configured, using base)"
            else:
                sign = 1 if scenario == "bull" else -1
                # Bull uses delta["bull"], bear uses delta["bear"] (bear deltas
                # are already negative for adverse metrics).
                delta = delta_entry[scenario]
                values[name] = round(float(base_val) + float(delta), 8)
                bps = int(abs(float(delta)) * 10000)
                direction = f"+{bps}bps" if float(delta) >= 0 else f"{float(delta)*10000:.0f}bps"
                sources[name] = f"derived from {base_name} {direction} ({scenario} scenario)"

    # Ensure in_scenario is set.
    if "in_scenario" not in values:
        values["in_scenario"] = 2
        sources["in_scenario"] = "constant: 2=Base (default)"

    # Write outputs.
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "values.json").write_text(json.dumps(values, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "sources.json").write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    missing_critical = [
        v["missing"] if isinstance(values[k], dict) else None
        for k, v_entry in mcp_map.items()
        if v_entry.get("critical") and k in values and isinstance(values[k], dict) and "missing" in values[k]
        for v in [values[k]]
    ]
    missing_critical = [m for m in missing_critical if m]

    report = {
        "ticker": ticker.upper(),
        "inputs_total": len([k for k, e in cell_map.items() if e["kind"] == "input"]),
        "inputs_mapped": len([k for k, v in values.items() if not (isinstance(v, dict) and "missing" in v)]),
        "missing_count": len([v for v in values.values() if isinstance(v, dict) and "missing" in v]),
        "missing_critical_count": len(missing_critical),
        "output_dir": str(output_dir),
    }

    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--cache-dir", default=None, help="Override cache directory")
    parser.add_argument("--output-dir", default=None, help="Override output directory")
    args = parser.parse_args()

    build_inputs(args.ticker, args.cache_dir, args.output_dir)
