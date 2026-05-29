---
description: Builds a filled 3-statement (IS+BS+CF) financial model with DCF and Scenario & Sensitivity tabs in Excel. Reads inputs from values.json + sources.json produced by model-input-builder; writes cells exclusively via cell_map.json (no literal coordinates). Validates the filled model against 9 blocking checks. Use after model-input-builder has produced its JSON outputs.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# excel-financial-model

## Purpose

Produce a filled copy of `fundamental_model_template_v2.xlsx` — an 11-sheet,
3-statement + DCF + Scenario & Sensitivity model — from the structured outputs
of `model-input-builder`, with **non-negotiable** cohesion guarantees enforced
by `validate_model.py`.

## Hard rules

1. **Never write a cell by literal coordinate.** Always resolve through
   `cell_map.json`. `fill_model.py` enforces this — no path accepts a
   `"C15"`-style coordinate from the caller.
2. **No hardcoded numbers inside Excel formulas.** Every input lives on the
   `Assumptions` tab and is referenced by named range.
3. **Source annotation is mandatory.** Any value written must carry a non-empty
   source. `fill_model.py` refuses to run if a source is missing.
4. **Validation is blocking.** A filled model is not delivered if
   `validate_model.py` exits non-zero.
5. **MISSING data is never silently substituted.** If a value is
   `{"missing": "<reason>"}`, the cell stays blank and column L of that row
   receives `"MISSING: <reason>"`. The validator blocks delivery on critical
   MISSING inputs.

## Repository layout

```
${CLAUDE_PLUGIN_ROOT}/skills/excel-financial-model/
├── SKILL.md                  (this file)
├── extract_cell_map.py       (regenerates cell_map.json from the v2 xlsx)
├── fill_model.py             (writes input values via cell_map.json)
├── validate_model.py         (9 blocking checks)
├── build_template.py         (legacy — superseded by v2 template)
├── template/
│   └── model_template.xlsx   (v2 template, bundled with the plugin)
├── reference/
│   ├── cell_map.json         (86 entries, generated from template named ranges)
│   └── assumptions.md        (human-readable input dictionary for the v2 model)
└── tests/
    ├── test_pipeline.py      (3 integration tests — happy path, MISSING, formula preserve)
    └── fixtures/AAPL/*.json  (offline MCP cache fixtures)
```

## Template v2 — sheet inventory

| Sheet | Role |
|---|---|
| Assumptions | All writeable inputs (named ranges prefixed `in_*`) |
| Income Statement | IS formulas driven by Assumptions |
| Balance Sheet | BS formulas |
| Cash Flow | CF formulas |
| PP&E Schedule | PP&E roll-forward |
| Debt Schedule | Term loan + revolver |
| WC Schedule | Working capital |
| DCF | WACC, UFCF, terminal value, equity value per share |
| Comps | Comparable-company multiples |
| Scenario & Sensitivity | Scenario switcher + sensitivity grid |
| Checks | 7 built-in `chk_*` validation cells |

## cell_map.json — entry kinds

| Kind | Prefix | Writeable | Notes |
|---|---|---|---|
| `input` | `in_*` | Yes | 37 entries; bull/base/bear scenario suffix where applicable |
| `output` | `out_*` | No | 7 read-only output cells (DCF results, Comps avg) |
| `check` | `chk_*` | No | 7 validation cells on the Checks sheet |
| `active_row` | `rng_*_row` | No | Multi-cell formula rows driven by scenario selector |
| `range` | `rng_*` | No | Single-cell formula drivers |

Regenerate after changing the template:

```bash
python extract_cell_map.py
```

## Source annotation — column L

All source strings are written to **column L** (column 12) of the same row
as the input cell, on whichever sheet the named range lives. Column L is
outside the data range (C:J) on the Assumptions tab and is not used by any
formula in the template.

Source format accepted:

```
"financial-datasets:income-statements ticker=AAPL as-of=2026-05-28"
"derived from in_rev_growth_base +200bps (bull scenario)"
"MISSING: earnings-analysis.json returned null for revenue_growth_next_year"
"constant: 2=Base (default)"
```

## Workflow

### Step 1 — Pull MCP data (upstream skills)

Run the relevant skills to build the JSON caches under
`${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`:

```
financial-statements, valuation-multiples, earnings-analysis,
fundamental-research, macro-context
```

### Step 2 — Build inputs (model-input-builder)

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/model-input-builder/build_inputs.py" \
    --ticker AAPL
```

Outputs `values.json` and `sources.json` to
`${CLAUDE_PLUGIN_DATA}/companies/AAPL/model_inputs/`.

### Step 3 — Fill the model

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/excel-financial-model/fill_model.py" \
    --template "$CLAUDE_PLUGIN_ROOT/skills/excel-financial-model/template/model_template.xlsx" \
    --output   "$CLAUDE_PROJECT_DIR/output/agent-finance/models/AAPL_2026-05-28.xlsx" \
    --values   "${CLAUDE_PLUGIN_DATA}/companies/AAPL/model_inputs/values.json" \
    --sources  "${CLAUDE_PLUGIN_DATA}/companies/AAPL/model_inputs/sources.json" \
    --comps    "${CLAUDE_PLUGIN_DATA}/companies/AAPL/model_inputs/peer_comps.json"
```

`--comps` is optional but **strongly recommended** — without it the Comps tab
ships with placeholder peer data. `valuation-multiples` produces
`peer_comps.json` automatically when run before `excel-financial-model`.

`fill_model.py` returns a JSON report: `{written, skipped, missing}`.

### Step 4 — Validate before delivery

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/excel-financial-model/validate_model.py" \
    "$CLAUDE_PROJECT_DIR/output/agent-finance/models/AAPL_2026-05-28.xlsx"
```

Exit code must be 0. If non-zero, read the JSON report on stdout, fix the
inputs, and re-run from Step 2. Do not deliver a model that fails validation.

## The 9 validation checks

| # | Check | Fails when |
|---|---|---|
| 1 | Balance-sheet identity | Assets ≠ Liabilities + Equity (any period) |
| 2 | Cash-flow tie-out | Δcash on CF ≠ Δcash on BS (any forecast year) |
| 3 | No error cells | Any cell contains `#REF!`, `#DIV/0!`, `#VALUE!`, etc. |
| 4 | Segment sums | Vacuously satisfied (no segment breakdown in v2) |
| 5 | Plausibility bounds | Margins outside 0–100%, growth outside −50%–200% |
| 6 | Source traceability | Any written input cell has no source in column L |
| 7 | Template built-in checks | Any `chk_*` cell ≠ TRUE/0 (skipped if xlsx never opened in Excel) |
| 8 | MISSING critical inputs | Any critical input has `MISSING:` annotation |
| 9 | Scenario coverage | A metric's bull/base/bear triplet is partially filled |

Checks 1–2 pass vacuously on an unfilled template (all zeros balance). Check 7
is skipped when the workbook has never been opened in Excel (openpyxl `data_only`
reads `None` for formula cells). Open in Excel once to force recalculation.

## Running the integration tests

```bash
pytest plugins/agent-finance/skills/excel-financial-model/tests/test_pipeline.py -v
```

Three offline tests (no real MCP calls):

1. **Happy path** — all fixtures present → validator passes checks 3, 6, 8, 9.
2. **MISSING data** — beta removed from fixture → validator fails check #8.
3. **Formula preservation** — fill does not overwrite any formula on IS/BS/CF/DCF/Comps.
