---
description: Frames the company against the macro and sector backdrop — interest-rate environment, sector cycle position, commodity sensitivity, and end-market exposure. Use to add the top-down view that bottom-up financial analysis misses.
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# macro-context

## Purpose

Single-responsibility skill: position the company on the macro/sector
backdrop. Bottom-up analysis answers "is this a good business"; this skill
answers "is this a good time."

## Inputs

- `ticker` (required).
- Output of `company-profile` (sector, geographic mix, supply chain).

## Methodology

1. **Rate environment.** Current policy rate in the company's primary
   funding jurisdiction. 2y and 10y sovereign yields. Direction over the last
   12 months. Cite a central-bank or treasury source.
2. **Sector cycle position.** Where is the sector in its cycle (early / mid /
   late / contraction)? Use the sector-relevant indicator:
   - Cyclicals — capacity utilization, new orders, inventories.
   - Consumer — retail sales, consumer confidence.
   - Financials — credit-spread trajectory, NPL rates.
   - Tech — capex cycle of large customers, software-spending intentions.
3. **Commodity sensitivity.** If the company has material commodity
   exposure (energy, metals, agriculture), state the input and the price
   trajectory over the last 12 months.
4. **End-market exposure.** Map the company's revenue mix to GDP exposure —
   developed-market consumer, emerging-market industrial, etc. Pull the
   GDP-growth outlook for the relevant blocs.
5. **Top-down stance.** One paragraph framing the company's tailwinds and
   headwinds. Explicit `assumption:` label.

## Dependencies

- Consumes: `company-profile`.
- Web: central-bank sites, statistical agencies (BLS, Eurostat, etc.).
- MCP: `financial-datasets` for commodity prices where available.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/macro-context.json`:

```json
{
  "rates": {"jurisdiction": "US", "policy_rate_pct": 5.25, "2y_yield_pct": 4.6, "10y_yield_pct": 4.4, "as_of": "2026-05-28", "source": "..."},
  "sector_cycle": {"phase": "mid", "indicator": "capacity utilization", "value": 81.2, "source": "..."},
  "commodities": [{"input": "copper", "price_usd_per_t": 9500, "delta_12m_pct": 14.0, "source": "..."}],
  "end_markets": [{"bloc": "US", "revenue_share_pct": 43.0, "gdp_outlook_pct": 1.8, "source": "..."}],
  "top_down_view": "assumption: ..."
}
```

## Source citation policy

Macro data cites the issuing institution (Fed, ECB, BLS, IMF, World Bank,
etc.) and the as-of date. Sector indicators cite the data provider.
