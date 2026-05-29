---
name: verdict-report
plugin: agent-finance
description: >
  Produces a decision-support verdict from the filled Excel model + full research
  cache. Reads out_* DCF outputs, computes a probability-weighted fair-value range
  (Bull/Base/Bear), derives a 5-level signal (ACCUMULATE / ADD / HOLD / REDUCE /
  AVOID), and emits a structured action plan across three time horizons. Use last
  in the pipeline, after excel-financial-model has been validated and opened in
  Excel (formulas must be calculated). Never labels output as investment advice.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# verdict-report

## Purpose

Bridge the gap between the research note (`report-composer`) and a decision.
Produce a single verdict document that:

1. **Audits the Excel model** — reads every computed output cell, flags anomalies
   (TV% > 75%, checks != OK, WACC < g).
2. **Derives a fair-value range** — re-runs the model in-memory for each scenario
   to get Bull / Base / Bear value-per-share.
3. **Emits a probability-weighted signal** — uses the working-view weights from
   `bull-bear-thesis.md` to compute an expected value and compare to current price.
4. **Produces a structured action plan** — three horizons: 0–3 months, 3–12
   months, 1–3 years — with specific milestones, tripwires, and kill conditions
   sourced from the research cache.

## Hard rules

1. **Never label output as investment advice.** The disclaimer line is fixed and
   verbatim: *"This report is decision-support research only. It is not
   investment advice."*
2. **Every figure cites source.** Format: `source: <filename or URL> as-of=<date>`.
3. **Refuse delivery if model not recalculated.** If `out_value_per_share` reads
   `None` (formulas not evaluated), stop and instruct the user to open the file
   in Microsoft Excel once.
4. **Refuse delivery if bull-bear-thesis missing.** The working-view weights are
   required to compute the expected value.
5. **Never invent scenario values.** If a scenario VPS cannot be computed (e.g.
   bull/bear model inputs not available), mark it `null` with a `gap:` reason.
6. **Reporting currency stated on every monetary figure.**

## Inputs

| Input | Required | Source |
|-------|----------|--------|
| `ticker` | ✅ | CLI `--ticker` |
| Filled Excel model (recalculated) | ✅ | `${PROJECT_DIR}/output/agent-finance/models/<TICKER>_<DATE>.xlsx` |
| `bull-bear-thesis.md` | ✅ | `${PLUGIN_DATA}/companies/<TICKER>/bull-bear-thesis.md` |
| `valuation-multiples.json` | ✅ | `${PLUGIN_DATA}/companies/<TICKER>/valuation-multiples.json` |
| `model_inputs/values.json` | ✅ | Needed to re-run bull/bear scenarios |
| `model_inputs/sources.json` | ✅ | Source annotations for re-run |
| `model_inputs/peer_comps.json` | optional | Needed for comps-implied VPS |
| `risk-assessment.json` | optional | Enriches tripwires section |
| `earnings-analysis.json` | optional | Next earnings date / catalyst calendar |

## Methodology

### Step 1 — Read Excel outputs

Open the model with `openpyxl data_only=True`. Via `cell_map.json` read:

| Logical name | Meaning |
|---|---|
| `out_value_per_share` | DCF Base value per share |
| `out_upside` | (VPS / current price) − 1 |
| `out_tv_pct_ev` | Terminal value as % of EV — flag if > 0.75 |
| `out_wacc` | WACC |
| `out_enterprise_value` | Enterprise value |
| `out_equity_value` | Equity value |
| `out_comps_avg_vps` | Comps-implied average value per share |

If any of the above is `None`, abort with:
> "Excel formulas not evaluated. Open the model in Microsoft Excel once to
> recalculate, then re-run verdict-report."

### Step 2 — Derive Bull / Bear VPS

Re-invoke `fill_model.py` twice in-memory (no file save):
- **Bull**: override `in_scenario = 1`, re-read `out_value_per_share`
- **Bear**: override `in_scenario = 3`, re-read `out_value_per_share`

Fair-value range = `[vps_bear, vps_base, vps_bull]`

### Step 3 — Parse working-view weights

Regex-parse `bull-bear-thesis.md` for the working-view line:
```
bull XX% / bear YY%
```
Extract `bull_weight` and `bear_weight`. Base weight = `1 - bull_weight - bear_weight`.

### Step 4 — Expected value & signal

```
ev = bull_weight × vps_bull + base_weight × vps_base + bear_weight × vps_bear
```

Signal thresholds (vs current price `p`):

| Condition | Signal |
|-----------|--------|
| `ev > p × 1.20` | **ACCUMULATE** |
| `ev > p × 1.05` | **ADD** |
| `p × 0.95 ≤ ev ≤ p × 1.05` | **HOLD** |
| `ev < p × 0.95` | **REDUCE** |
| `ev < p × 0.80` | **AVOID** |

### Step 5 — Catalyst calendar

Parse milestones from `bull-bear-thesis.md` (lines starting with "Milestone:").
Tag each as Q1/Q2/Q3/Q4 or year-based. Sort by proximity to today.

### Step 6 — Action plan (3 horizons)

Combine milestones, tripwires from `risk-assessment.json`, and guidance check
points from `earnings-analysis.json` into three horizon buckets.

### Step 7 — Write outputs

1. `${PLUGIN_DATA}/companies/<TICKER>/model_inputs/verdict.json` — machine-readable
2. `${PROJECT_DIR}/output/agent-finance/reports/<TICKER>_verdict_<DATE>.md` — human report

## Output schema

### verdict.json

```json
{
  "ticker": "DOL",
  "as_of": "2026-05-28",
  "reporting_currency": "CAD",
  "current_price": 174.95,
  "dcf_vps": {
    "bull": null,
    "base": 60.94,
    "bear": null
  },
  "comps_implied_vps": 26.78,
  "bull_weight": 0.60,
  "base_weight": 0.0,
  "bear_weight": 0.40,
  "expected_value_weighted": 0.0,
  "signal": "HOLD",
  "signal_conviction_pct": 60,
  "upside_base_pct": -65.1,
  "tv_pct_ev": 0.889,
  "tv_flag": true,
  "wacc": 0.0581,
  "gaps": [],
  "sources": [
    "cell_map.json",
    "bull-bear-thesis.md",
    "valuation-multiples.json"
  ]
}
```

### <TICKER>_verdict_<DATE>.md — fixed section order

```
# <TICKER> — <Company> — Decision-Support Verdict
> This report is decision-support research only. It is not investment advice.
> Reporting currency: <CCY>. As-of: <DATE>.

## 1. Model Audit
### 1.1 Validity
### 1.2 Computed outputs
### 1.3 Flags & anomalies

## 2. Fundamental Verdict
### 2.1 Quality of business
### 2.2 Growth trajectory
### 2.3 Financial health
### 2.4 Valuation (DCF range + comps)
### 2.5 SIGNAL
**[ACCUMULATE | ADD | HOLD | REDUCE | AVOID]**
Conviction: XX% | Assumption: [working-view label]

## 3. Action Plan
### 3.1 Immediate (0–3 months)
### 3.2 Medium-term (3–12 months)
### 3.3 Long-term (1–3 years)

## 4. Key Assumptions to Monitor (Tripwires)
[If X changes → signal flips to Y]

## Sources
```

## Invocation

```bash
python "$CLAUDE_PLUGIN_ROOT/skills/verdict-report/build_verdict.py" \
  --ticker DOL \
  --model "$CLAUDE_PROJECT_DIR/output/agent-finance/models/DOL_2026-05-28.xlsx" \
  --cache "$CLAUDE_PLUGIN_DATA/companies/DOL" \
  --output "$CLAUDE_PROJECT_DIR/output/agent-finance/reports/DOL_verdict_2026-05-28.md"
```

Or via the orchestrator when the user asks for a "verdict", "moves",
"recommendation", "buy or sell", or "que faire sur".

## Pipeline position

```
company-profile → ... → bull-bear-thesis → model-input-builder →
excel-financial-model → report-composer → [verdict-report]
```

`verdict-report` is **optional and on-demand**. The pipeline delivers without
it; it is triggered explicitly by user intent.

## Dependencies

- `excel-financial-model` must have run and the xlsx must have been opened in
  Excel once (formulas evaluated).
- `bull-bear-thesis` must have produced `bull-bear-thesis.md` with a working-view
  section containing explicit bull/bear weights.
- `fill_model.py` is imported directly for in-memory scenario re-runs.
