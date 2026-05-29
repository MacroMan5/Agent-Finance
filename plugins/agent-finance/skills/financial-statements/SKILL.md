---
description: Pulls the income statement, balance sheet, and cash flow statement. Computes leverage and liquidity ratios — net debt/EBITDA, interest coverage, current ratio, FCF, working-capital evolution. Use after company-profile, before historical-baseline and valuation-multiples.
allowed-tools: Read, Write, Grep, Glob, WebFetch, Bash
---

# financial-statements

## Purpose

Pull the three statements for the last 5 fiscal years plus the last 4
quarters. Compute the standard solvency, liquidity, and cash-generation
ratios. Output a clean, normalized dataset for downstream skills.

## Inputs

- `ticker` (required).
- `reporting_currency` from `company-profile` — used to validate consistency.

## Methodology

1. **Pull the statements** via `financial-datasets` MCP:
   - `income-statements` endpoint, annual & quarterly.
   - `balance-sheets` endpoint, annual & quarterly.
   - `cash-flow-statements` endpoint, annual & quarterly.
2. **Validate currency consistency.** All statements must report in the
   currency identified by `company-profile`. If MCP returns a different
   currency, flag it and stop.
3. **Compute ratios.**
   - `Net debt / EBITDA` (annual).
   - `Interest coverage = EBIT / Interest expense` (annual).
   - `Current ratio = Current assets / Current liabilities`.
   - `Quick ratio = (Current assets - Inventory) / Current liabilities`.
   - `FCF = CFO - CapEx` (annual & TTM).
   - `Working capital = Current assets - Current liabilities`; track delta.
   - `Gross / operating / net margin` per period.
   - `FCF yield = FCF / market cap` (annual & TTM) — requires current price
     from `valuation-multiples` if available; mark `null` with gap reason if
     not yet pulled.
   - `Maintenance capex vs growth capex` — split where disclosed in MD&A or
     footnotes. If not explicitly disclosed, derive: maintenance capex ≈
     depreciation × (1 + inflation); growth capex = total capex − maintenance.
     Label the split as `assumption:` when derived, `filing:` when disclosed.
4. **Flag one-offs.** Any line with `restructuring`, `impairment`,
   `goodwill write-down`, `litigation settlement` — itemize.

## Dependencies

- Consumes: `company-profile` (reporting currency).
- MCP: `financial-datasets` (income / balance / cash-flow endpoints).

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/financial-statements.json`:

```json
{
  "currency": "USD",
  "as_of": "2026-05-28",
  "annual": {
    "FY24": {"revenue": ..., "ebit": ..., "net_income": ..., "total_assets": ..., "fcf": ..., "source": "..."}
  },
  "quarterly": {"Q1-FY26": {...}},
  "ratios": {
    "net_debt_to_ebitda": [{"period": "FY24", "value": 1.2, "source": "..."}],
    "interest_coverage": [...],
    "fcf_margin_pct": [...],
    "fcf_yield_pct": [{"period": "TTM", "value": 3.1, "source": "..."}],
    "capex_split": [{"period": "FY25", "total": 0, "maintenance": 0, "growth": 0, "method": "disclosed | derived", "source": "..."}]
  },
  "one_offs": [{"period": "FY24", "type": "impairment", "amount": ..., "source": "..."}]
}
```

## Source citation policy

Every line of every statement carries the MCP endpoint and as-of date in
`source:`. One-offs additionally cite the filing footnote that disclosed them.
