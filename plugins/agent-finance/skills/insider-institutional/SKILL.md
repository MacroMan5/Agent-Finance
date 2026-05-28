---
description: Pulls insider transactions (SEC Form 4) and institutional positions (SEC Form 13F), plus short-interest data. Use after earnings-analysis to spot capital-flow signals that confirm or contradict the narrative.
allowed-tools: Read, Write, Grep, Glob, WebFetch, Bash
---

# insider-institutional

## Purpose

Single-responsibility skill: surface what the people closest to the company
and the largest holders are doing with their position. Capital flows are a
noisy signal but a useful tiebreaker.

## Inputs

- `ticker` (required).
- Optional: `lookback_days` (default: 180 for Form 4, latest filing for
  13F).

## Methodology

1. **Form 4 insider trades.** Pull via `financial-datasets` MCP if
   available; otherwise SEC EDGAR full-text search. Aggregate over the
   lookback window:
   - Net shares bought / sold by insiders.
   - By role: CEO, CFO, other named officers, directors, 10%+ holders.
   - Cluster buys (multiple insiders buying within a 30-day window) — flag
     separately.
2. **13F institutional positions.** Pull the most recent quarterly 13F
   aggregate:
   - Total institutional ownership %.
   - Top 10 holders and their position size.
   - Quarter-over-quarter changes — meaningful additions, exits.
3. **Short interest.** Latest disclosed short interest as % of float, days
   to cover.
4. **Interpret cautiously.** Insiders can sell for non-information reasons
   (10b5-1 plans, diversification, tax). Insider buying is the rarer and
   more signal-rich event.

## Dependencies

- MCP: `financial-datasets` (insider trades, institutional ownership, short
  interest where available).
- Web: SEC EDGAR for Form 4 and 13F as fallback.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/insider-institutional.json`:

```json
{
  "form4": {
    "lookback_days": 180,
    "net_shares_traded": -125000,
    "by_role": [{"role": "CEO", "net_shares": -50000, "source": "..."}],
    "cluster_buys": [],
    "source": "..."
  },
  "form13f": {
    "as_of": "2026-03-31",
    "institutional_ownership_pct": 67.0,
    "top_holders": [{"name": "Vanguard", "shares": 1234567, "qoq_delta_shares": 10000, "source": "..."}]
  },
  "short_interest": {"pct_float": 1.2, "days_to_cover": 1.5, "as_of": "2026-05-15", "source": "..."}
}
```

## Source citation policy

Form 4 trades cite the specific SEC filing accession number. 13F figures
cite the institution and filing date. Short interest cites the data provider
and the as-of date.
