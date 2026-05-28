"""Generate cell_map.json from the v2 Excel template's defined names.

Usage:
    python extract_cell_map.py [--template PATH] [--output PATH]

Defaults:
    template = ../../../fundamental_model_template_v2.xlsx  (repo root)
    output   = reference/cell_map.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from openpyxl import load_workbook

SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent  # Agent-Finance/
DEFAULT_TEMPLATE = REPO_ROOT / "fundamental_model_template_v2.xlsx"
DEFAULT_OUTPUT = SKILL_DIR / "reference" / "cell_map.json"

_SCENARIO_SUFFIX = re.compile(r"_(bull|base|bear)$")
_UNITS_HINTS = {
    "growth": "pct",
    "margin": "pct",
    "pct": "pct",
    "rate": "pct",
    "tgr": "pct",
    "erp": "pct",
    "beta": "ratio",
    "mult": "x",
    "life": "years",
    "amort": "usd",
    "open": "usd",
    "cash": "usd",
    "shares": "units",
    "price": "usd",
    "payout": "pct",
}


def _infer_units(metric: str) -> str:
    for hint, unit in _UNITS_HINTS.items():
        if hint in metric:
            return unit
    return "value"


def _parse_cell_ref(attr_text: str) -> tuple[str, str] | None:
    """Return (sheet, cell) from a defined-name attr_text like Sheet!$C$15."""
    # Strip workbook-level qualifier if present (e.g. [0]Sheet!...)
    text = re.sub(r"^\[\d+\]", "", attr_text)
    # Handle quoted sheet names like 'PP&E Schedule'!$C$11
    m = re.match(r"^'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)(?::\$?[A-Z]+\$?\d+)?$", text)
    if not m:
        return None
    sheet = m.group(1)
    col = m.group(2)
    row = m.group(3)
    return sheet, f"{col}{row}"


def _parse_range_ref(attr_text: str) -> tuple[str, str] | None:
    """Return (sheet, range_str) for multi-cell ranges like Sheet!$C$18:$J$18."""
    text = re.sub(r"^\[\d+\]", "", attr_text)
    m = re.match(
        r"^'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+):\$?([A-Z]+)\$?(\d+)$", text
    )
    if not m:
        return None
    sheet = m.group(1)
    return sheet, f"{m.group(2)}{m.group(3)}:{m.group(4)}{m.group(5)}"


def build_cell_map(template_path: Path) -> dict:
    wb = load_workbook(template_path, data_only=False)
    cell_map: dict[str, dict] = {}

    for name in sorted(wb.defined_names):
        defn = wb.defined_names[name]
        attr = defn.attr_text

        if name.startswith("in_"):
            # Writeable input — parse scenario suffix if present
            m_scen = _SCENARIO_SUFFIX.search(name)
            scenario = m_scen.group(1) if m_scen else None
            metric = _SCENARIO_SUFFIX.sub("", name[len("in_"):]) if m_scen else name[len("in_"):]

            parsed = _parse_cell_ref(attr)
            if parsed is None:
                continue
            sheet, cell = parsed
            entry: dict = {
                "named_range": name,
                "sheet": sheet,
                "cell": cell,
                "kind": "input",
                "fill_strategy": "mcp_or_delta" if scenario else "direct",
            }
            if scenario:
                entry["scenario"] = scenario
                entry["metric"] = metric
            else:
                entry["metric"] = metric
            entry["units"] = _infer_units(metric)
            cell_map[name] = entry

        elif name.startswith("out_"):
            parsed = _parse_cell_ref(attr)
            if parsed is None:
                continue
            sheet, cell = parsed
            cell_map[name] = {
                "named_range": name,
                "sheet": sheet,
                "cell": cell,
                "kind": "output",
            }

        elif name.startswith("chk_"):
            parsed = _parse_cell_ref(attr)
            if parsed is None:
                continue
            sheet, cell = parsed
            cell_map[name] = {
                "named_range": name,
                "sheet": sheet,
                "cell": cell,
                "kind": "check",
            }

        elif name.startswith("rng_"):
            # Try multi-cell range first, then single cell
            parsed_range = _parse_range_ref(attr)
            if parsed_range:
                sheet, cell_range = parsed_range
                kind = "active_row" if "row" in name else "range"
                cell_map[name] = {
                    "named_range": name,
                    "sheet": sheet,
                    "cell": cell_range,
                    "kind": kind,
                }
            else:
                parsed = _parse_cell_ref(attr)
                if parsed:
                    sheet, cell = parsed
                    cell_map[name] = {
                        "named_range": name,
                        "sheet": sheet,
                        "cell": cell,
                        "kind": "range",
                    }

    return cell_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    template_path = Path(args.template)
    output_path = Path(args.output)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    cell_map = build_cell_map(template_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(cell_map, f, indent=2, ensure_ascii=False)
        f.write("\n")

    kinds = {}
    for e in cell_map.values():
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    print(f"Wrote {len(cell_map)} entries to {output_path}")
    print(f"Breakdown: {kinds}")


if __name__ == "__main__":
    main()
