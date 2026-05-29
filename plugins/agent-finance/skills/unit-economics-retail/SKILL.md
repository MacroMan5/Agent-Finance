---
description: Builds store-level unit economics for physical retailers — revenue per square foot, EBITDA per store, new-store payback period, cohort analysis, and cannibalization rate. Auto-triggered when company-profile identifies a physical-retail sector. Feeds bull-bear-thesis and model-input-builder (growth capex calibration).
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
trigger: auto when company-profile.sector contains "Consumer Discretionary" or "Consumer Staples" and store_count > 0
---

# unit-economics-retail

## Purpose

Translate store-count and financial data into the unit-level economics that
institutional retail analysts use to assess the quality and durability of
growth. A DCF that models revenue growth as a single percentage misses the
underlying driver: each new store is a capital allocation decision with a
measurable return. This skill makes that return explicit.

## Inputs

- `ticker` (required).
- `company-profile` output — confirms sector and store count.
- `financial-statements` output — revenue, COGS, capex, D&A.
- `historical-baseline` output — multi-year store count and revenue.
- Annual report (10-K / AIF / 20-F) and investor-day presentations.

## Methodology

### 1. Revenue per square foot

Pull total selling square footage from the annual report (AIF or 10-K).
Compute `revenue / total_sqft` for each of the last 5 fiscal years.
Trend direction (expanding = pricing power or traffic; contracting = saturation
signal) is as important as the level.

### 2. EBITDA per store at maturity

From the annual report or investor-day: disclosed store-level EBITDA or
four-wall EBITDA. If not disclosed directly:
- Derive: `(store-level gross profit − store-level opex) / store count`
- Require: the company must separate corporate overhead from store-level costs.
  If it does not, derive from segment disclosures or investor-day guidance.
- Label as `assumption:` when derived, `filing:` when explicitly disclosed.

### 3. New-store capex (unit opening cost)

From the capital expenditure note in the annual report:
- Identify the disclosed cost to open one new store (fit-out, fixtures,
  initial inventory if capitalized).
- If not disclosed per unit, derive: `growth capex / net new stores opened`.
- Label derivation method explicitly.

### 4. Payback period

`payback_period_years = new_store_capex / ebitda_per_store_mature`

This is the single most important unit-economics metric for a retailer.
A payback period lengthening over cohort years is an early saturation signal,
often visible 2–3 years before same-store sales show stress.

### 5. Store cohort analysis

Group stores by opening year (cohort). For each cohort:
- Average revenue per store in year 1, year 2, year 3 post-opening.
- Compare ramp profile across cohorts — are newer stores reaching maturity
  faster or slower than older cohorts?
- Source: requires multi-year store-count tables + revenue per cohort.
  If granular cohort data is not disclosed, use the aggregate ramp implied
  by `(total revenue / store count)` trajectory as a proxy and label as
  `assumption: aggregate proxy`.

### 6. Market density and cannibalization

- Compute `stores per 100,000 population` by province/state/region where
  disclosed.
- Compare high-density markets (e.g. Ontario, Quebec for Dollarama) vs
  low-density markets — same-store sales differential is the cannibalization
  signal.
- If regional same-store sales are not disclosed, compute the implied
  cannibalization rate:
  `cannibalization_rate = (company_sssg − market_sssg_proxy) / new_store_density_growth`
  Label as `assumption:`.

### 7. Calibration output for model-input-builder

Translate unit economics into scenario-level inputs for the DCF:

- **Bull**: store count reaches management target on schedule; payback period
  stable or compressing; mature EBITDA per store holds.
- **Base**: store count grows at current guidance; payback period flat;
  mature EBITDA per store inflates with CPI.
- **Bear**: new store openings slow by 20%; payback period extends 1 year
  (saturation); mature EBITDA per store compresses 10% (cannibalization).

These feed `in_rev_growth_*` and `in_capex_pct_*` in `values.json` via
`model-input-builder`.

## Dependencies

- Consumes: `company-profile`, `financial-statements`, `historical-baseline`.
- No MCP calls — data sourced from filings and investor-day via WebFetch /
  WebSearch.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/unit-economics-retail.json`:

```json
{
  "ticker": "DOL",
  "currency": "CAD",
  "as_of": "2026-05-29",
  "revenue_per_sqft": [
    {"fy": "FY25", "revenue_m": 6413, "total_sqft_k": 0, "rev_per_sqft": 0, "source": "..."}
  ],
  "ebitda_per_store": {
    "value_m": 1.4,
    "method": "disclosed | derived",
    "assumption": "...",
    "source": "..."
  },
  "new_store_capex": {
    "value_m": 0,
    "method": "disclosed | derived",
    "assumption": "...",
    "source": "..."
  },
  "payback_period_years": {
    "value": 0,
    "trend": "stable | compressing | extending",
    "source": "..."
  },
  "cohort_analysis": [
    {
      "cohort_year": 2022,
      "stores_opened": 65,
      "avg_rev_yr1_m": 0,
      "avg_rev_yr2_m": 0,
      "avg_rev_yr3_m": 0,
      "method": "disclosed | aggregate_proxy",
      "source": "..."
    }
  ],
  "market_density": [
    {
      "region": "Ontario",
      "stores": 0,
      "population_m": 0,
      "stores_per_100k": 0,
      "sssg_proxy": null,
      "source": "..."
    }
  ],
  "cannibalization": {
    "rate_estimate_pct": null,
    "method": "disclosed | derived",
    "assumption": "...",
    "source": "..."
  },
  "dcf_calibration": {
    "_note": "NOT YET WIRED — build_inputs.py reads single-file sources only. Cross-check in_rev_growth_* and in_capex_pct_* in the Assumptions tab manually until model-input-builder adds cross-file fallback support.",
    "bull":  {"rev_growth_pct": 0, "capex_pct_rev": 0, "rationale": "..."},
    "base":  {"rev_growth_pct": 0, "capex_pct_rev": 0, "rationale": "..."},
    "bear":  {"rev_growth_pct": 0, "capex_pct_rev": 0, "rationale": "..."}
  }
}
```

## Source citation policy

Every numeric value carries a `source:` (filing URL + page or section).
Every derived value carries both `assumption:` (formula used) and `source:`
(the raw inputs the formula was applied to). Never invent store-level data
not present in public filings or investor-day materials.
