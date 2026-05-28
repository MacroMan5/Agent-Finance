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
6. **Unit economics.** Where applicable (subscription / transaction / SaaS):
   CAC, LTV, payback, gross-revenue retention, net-revenue retention. From
   filings or investor presentations only.

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
  "unit_economics": {...}
}
```

## Source citation policy

Every numeric value carries a `source:` (filing URL + page, or MCP endpoint
+ as-of date). Every forward-looking statement carries an `assumption:` tag.
