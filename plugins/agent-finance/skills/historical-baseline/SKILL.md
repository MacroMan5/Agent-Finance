---
description: Builds a 5–10 year historical series of the company's revenue, margins, FCF, and capital structure to normalize figures and flag trends or anomalies. Use after financial-statements, before valuation-multiples and bull-bear-thesis.
allowed-tools: Read, Write, Grep, Glob, WebFetch, Bash
---

# historical-baseline

## Purpose

Provide the long-window context that one or two recent quarters cannot. Used
to detect whether the latest print is a continuation, an inflection, or an
outlier.

## Inputs

- `ticker` (required).
- Output of `financial-statements` (already covers 5y; this skill extends to
  10y where available).

## Methodology

1. **Extend the series to 10y** where the data is available — pull older
   annual statements via `financial-datasets` MCP. If only 5y are available,
   state that explicitly.
2. **Compute trends.**
   - Revenue CAGR over 5y and 10y.
   - Margin trajectory — slope of the linear fit on operating margin.
   - FCF stability — coefficient of variation of FCF / revenue.
   - Capital structure drift — net debt / equity over time.
3. **Flag anomalies.** Any year with a > 2σ deviation from the rolling
   3y mean on revenue growth, operating margin, or FCF margin. State the
   plausible cause from filings (acquisition, divestiture, one-off).
4. **Normalize.** Compute a "through-cycle" version of margins by removing
   the flagged one-off years. This normalized figure is what
   `valuation-multiples` and `bull-bear-thesis` should reference.

## Dependencies

- Consumes: `financial-statements`, `company-profile`.
- MCP: `financial-datasets` (extended history).

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/historical-baseline.json`:

```json
{
  "history_years": 10,
  "revenue_cagr_5y_pct": 8.3,
  "revenue_cagr_10y_pct": 11.2,
  "operating_margin_slope_pp_per_year": 0.4,
  "fcf_cv_pct": 12.0,
  "anomalies": [{"fy": "FY20", "metric": "operating_margin", "deviation_sigma": 2.7, "cause": "...", "source": "..."}],
  "normalized": {"operating_margin_pct": 25.0, "fcf_margin_pct": 22.0, "method": "5y mean ex-FY20", "source": "..."}
}
```

## Source citation policy

Every datapoint cites the underlying filing or MCP endpoint. The
normalization method is stated in plain English and is a labeled
`assumption:`.
