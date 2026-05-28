---
description: Enumerates the company's structural risks — customer concentration, FX exposure, regulatory pressure, share dilution, debt covenants, and maturity schedule. Use after financial-statements and news-intelligence; output feeds bull-bear-thesis and report-composer.
allowed-tools: Read, Write, Grep, Glob, WebFetch, Bash
---

# risk-assessment

## Purpose

Surface the risks that filings disclose but skim-readers miss. Output is a
labeled catalogue, not a probability ranking. The bull-bear-thesis skill
turns this catalogue into scenario weights.

## Inputs

- `ticker` (required).
- Outputs of `company-profile`, `financial-statements`,
  `news-intelligence`.

## Methodology

1. **Customer concentration.** From the 10-K / 20-F: how much revenue comes
   from the top-1, top-3, top-5 customers? Disclosed thresholds are typically
   ≥ 10% of revenue.
2. **FX exposure.** What % of revenue is non-functional-currency? What % of
   costs? Net exposure. Hedging program disclosure.
3. **Regulatory.** Active investigations (DoJ, FTC, SEC, EU, CMA, MOFCOM,
   etc.), pending rule-makings, license renewals, FDA / EMA approval risk.
4. **Dilution.** Share-based compensation as % of revenue and as % of FCF
   over the last 3y. Outstanding options + RSUs as % of basic shares.
5. **Debt covenants.** Identify financial covenants in the debt indentures.
   Headroom on each covenant given the current ratios from
   `financial-statements`.
6. **Maturity schedule.** Debt maturities by year for the next 5y. Refinancing
   needs against the current interest-rate environment.

## Dependencies

- Consumes: `company-profile`, `financial-statements`, `news-intelligence`.
- MCP: `financial-datasets` (debt detail endpoint if available).
- Web: SEC EDGAR for the indenture exhibits.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/risk-assessment.json`:

```json
{
  "customer_concentration": {"top1_pct": 14.0, "top5_pct": 28.0, "source": "..."},
  "fx_exposure": {"non_functional_revenue_pct": 58.0, "non_functional_cost_pct": 35.0, "hedging": "...", "source": "..."},
  "regulatory": [{"jurisdiction": "EU", "matter": "...", "stage": "investigation", "source": "..."}],
  "dilution": {"sbc_pct_revenue": 9.5, "sbc_pct_fcf": 22.0, "options_rsus_pct_shares": 4.1, "source": "..."},
  "covenants": [{"indenture": "2030 notes", "covenant": "net leverage <= 4.0x", "headroom": "current 1.2x", "source": "..."}],
  "maturities_usd_m": [{"year": 2026, "amount": 1500, "source": "..."}]
}
```

## Source citation policy

Every risk row cites the filing exhibit, page, or section. Estimates derived
from filings (e.g. dilution rates) state the formula used.
