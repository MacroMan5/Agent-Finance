---
description: Builds the fundamental investment thesis — economic moat, ROIC, structural margins, TAM, competitive advantage, and unit economics. Use after company-profile and financial-statements, before valuation-multiples.
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# fundamental-research

## Purpose

Translate the raw financial picture into a structured thesis. Answers: what
is this business *worth* protecting, and why does that protection persist?

## Inputs

- `ticker` (required).
- Output of `company-profile` and `financial-statements` for the same ticker.

## Methodology

1. **Moat assessment.** Classify the moat as one of: network effects, scale,
   intangible assets (brand / IP / regulatory), switching costs, cost
   advantage, efficient scale. Cite evidence — pricing power data, market-share
   trajectory, regulatory barriers.
2. **ROIC computation.** `ROIC = NOPAT / Invested Capital`, computed over
   the last 5 fiscal years. Compare to a conservative cost of capital. Sustained
   ROIC > WACC is the moat's quantitative signature.
3. **Margin structure.** Decompose gross, operating, and net margins. Flag
   one-offs and the trend over 5y.
4. **TAM.** Cite the company's stated TAM, then a third-party estimate
   (analyst report, industry data). Note the gap. State the assumption used in
   any forward projection.
5. **Competitive position.** Where in the value chain does the company sit?
   What is the next-best alternative for its customers?
6. **Unit economics.** Detect the business model type from `company-profile`
   and collect the appropriate metrics:
   - **Physical retail** (Consumer Discretionary / Staples — brick-and-mortar):
     revenue per square foot (annual, 5y), EBITDA per store at maturity,
     new-store capex (unit opening cost), implied payback period
     (unit capex / EBITDA per store), same-store sales CAGR 3y, and
     cannibalization rate (comp deceleration vs new-store density growth).
     Source: AIF / 10-K store-count tables, investor-day presentations.
   - **SaaS / subscription**: CAC, LTV, payback, gross-revenue retention,
     net-revenue retention. Source: filings or investor presentations only.
   - **Manufacturer / industrials**: cost per unit, capacity utilization %,
     yield / scrap rate, throughput per shift. Source: 10-K MD&A or
     investor-day.
   If the business model does not fit any category above, mark
   `unit_economics` as `{"type": "n/a", "reason": "..."}` — never leave it
   null without a reason.

## Dependencies

- Consumes: `company-profile`, `financial-statements`.
- MCP: `financial-datasets` (ratios endpoint for ROIC if available).

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/fundamental-research.json`:

```json
{
  "moat": {"type": "...", "evidence": [{"point": "...", "source": "..."}]},
  "roic_5y": [{"fy": "FY24", "value_pct": 28.5, "source": "..."}],
  "margins": {"gross_5y_pct": [...], "operating_5y_pct": [...], "net_5y_pct": [...]},
  "tam": {"company_stated_usd_b": 1500, "third_party_usd_b": 1100, "assumption": "...", "source": "..."},
  "competitive_position": "...",
  "unit_economics": {
    "type": "physical_retail | saas | manufacturer | n/a",
    "physical_retail": {
      "revenue_per_sqft": [{"fy": "FY25", "value": 0, "currency": "CAD", "source": "..."}],
      "ebitda_per_store_mature": {"value": 0, "currency": "CAD_M", "source": "..."},
      "new_store_capex": {"value": 0, "currency": "CAD_M", "source": "..."},
      "payback_period_years": {"value": 0, "assumption": "unit_capex / ebitda_per_store", "source": "..."},
      "sssg_cagr_3y_pct": {"value": 0, "source": "..."},
      "cannibalization_note": "..."
    },
    "saas": {"cac": 0, "ltv": 0, "payback_months": 0, "grr_pct": 0, "nrr_pct": 0, "source": "..."},
    "manufacturer": {"cost_per_unit": 0, "capacity_utilization_pct": 0, "source": "..."}
  }
}
```

## Source citation policy

Every numeric value carries a `source:` (filing URL + page, or MCP endpoint
+ as-of date). Every forward-looking statement carries an `assumption:` tag.
