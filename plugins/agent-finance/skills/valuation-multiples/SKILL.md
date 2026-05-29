---
description: Computes relative valuation multiples — P/E, EV/EBITDA, EV/Sales, P/FCF — versus a peer set and versus the company's own 5y history. Triangulates the DCF output. Use after financial-statements, historical-baseline, and fundamental-research. This is the skill that feeds sector-analyst.
allowed-tools: Read, Write, Grep, Glob, WebFetch, Bash
---

# valuation-multiples

## Purpose

Place the company on the relative-valuation map. Output two views: "vs
peers" and "vs own history." This skill is the primary input to
`sector-analyst`.

## Inputs

- `ticker` (required).
- `peer_set` — list of 3–7 tickers. If absent, derive from
  `company-profile.competitors`.
- Outputs of `financial-statements`, `historical-baseline`,
  `fundamental-research`.

## Methodology

1. **Pull current prices and counts** via `financial-datasets` MCP:
   - Share price (latest close).
   - Diluted shares outstanding.
   - Net debt (from the latest balance sheet).
2. **Compute market cap and EV** for the company and each peer.
3. **Compute multiples** (NTM where consensus is available; otherwise TTM):
   - `P/E = price / EPS`
   - `EV/EBITDA = EV / EBITDA`
   - `EV/Sales = EV / revenue`
   - `P/FCF = market cap / FCF`
4. **Build the peer comp table.** One row per ticker (including the target),
   one column per multiple. Add a column for the median of the peer set
   excluding the target.
5. **Build the own-history view.** For each multiple, plot the 5y range
   (min, p25, median, p75, max) and the current value. Position the current
   value as a percentile.
6. **Flag dispersion.** If the peer multiples have a coefficient of variation
   > 50%, the comp is unreliable — say so.

## Dependencies

- Consumes: `company-profile`, `financial-statements`, `historical-baseline`,
  `fundamental-research`.
- MCP: `financial-datasets` (prices, shares, ratios).

## Comps tab — peer_comps.json (required for Excel model)

After computing peer multiples, **always** write a second output:
`${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/model_inputs/peer_comps.json`

This file is consumed by `fill_model.py --comps` to populate the Comps tab
automatically. Without it, the Comps tab ships with placeholder data.

Format:
```json
{
  "ticker": "DOL",
  "as_of": "2026-05-28",
  "source": "<url> as-of=<date>",
  "peers": [
    {"name": "Dollar General (DG)", "ev_sales": 0.62, "ev_ebitda": 15.16, "pe": 25.45, "p_fcf": 20.39, "source": "..."},
    {"name": "Dollar Tree (DLTR)",  "ev_sales": 0.84, "ev_ebitda": 12.50, "pe": 20.23, "p_fcf": 14.31, "source": "..."},
    {"name": "Five Below (FIVE)",   "ev_sales": 2.82, "ev_ebitda": 19.99, "pe": 32.64, "p_fcf": 28.40, "source": "..."},
    {"name": "B&M Value Retail (BME)", "ev_sales": 0.55, "ev_ebitda": 6.93, "pe": 6.87, "p_fcf": 9.20, "source": "..."}
  ]
}
```

Rules:
- 3–6 peers. Always include the target company's own multiples as the last
  row (labeled "Subject — <TICKER>") for visual premium/discount comparison.
- Every multiple must cite its source URL and as-of date.
- Use TTM multiples unless NTM consensus is available (prefer NTM; label it).
- Multiples must be ratio-based (currency-neutral) — safe to mix USD/GBP peers.

## fill_model.py integration

Pass the file to `fill_model.py` via `--comps`:
```bash
python fill_model.py --template ... --output ... --values ... --sources ... \
  --comps "${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/model_inputs/peer_comps.json"
```

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/valuation-multiples.json`:

```json
{
  "as_of": "2026-05-28",
  "peer_set": ["MSFT", "GOOGL", "META"],
  "current": {"price": 195.5, "market_cap_usd_b": 3000, "ev_usd_b": 2950, "source": "..."},
  "multiples_vs_peers": {
    "pe_ntm": {"target": 28.5, "peer_median": 24.0, "source": "..."},
    "ev_ebitda_ntm": {...},
    "ev_sales_ntm": {...},
    "p_fcf_ntm": {...}
  },
  "multiples_vs_own_history": {
    "pe_ntm": {"min_5y": 18.0, "p25": 22.0, "median": 25.0, "p75": 28.0, "max": 32.0, "current": 28.5, "percentile": 78}
  },
  "dispersion_flag": false
}
```

## Source citation policy

Every multiple cites: the MCP endpoint, the as-of date, and the input fields
(price, shares, EBITDA, etc.) used in the computation. Consensus inputs
also cite the consensus provider and date.
