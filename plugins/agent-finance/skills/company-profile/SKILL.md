---
description: Builds the qualitative profile of a public company — business model, products and services, reporting segments, geographic mix, management team, competitors, supply chain, and reporting currency. Use first on any new ticker, before any financial analysis.
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# company-profile

## Purpose

Single-responsibility skill: produce the qualitative scaffolding of a
company. Every later skill relies on the segment list, the geographic mix,
the competitor set, and the reporting currency captured here.

## Inputs

- `ticker` (required) — e.g. `AAPL`.
- Optional: a path to a cached 10-K / 20-F if already fetched.

## Methodology

1. Pull the latest annual filing (10-K for US issuers, 20-F for foreign
   private issuers) from SEC EDGAR via `WebFetch`. Cache it under
   `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/raw/`.
2. Pull the company's investor-relations homepage for the latest investor
   presentation. Cache it.
3. Extract:
   - Business model — how revenue is actually earned (subscription,
     transaction, license, etc.).
   - Product / service taxonomy — top-level lines and their share of revenue.
   - Reporting segments — exactly as disclosed, no aggregation.
   - Geographic mix — by % of revenue for the latest FY.
   - Management — CEO, CFO, board chair, tenure, prior roles.
   - Stated competitors — only those named in the filing.
   - Supply-chain dependencies — concentrated suppliers, single-source inputs,
     manufacturing partners.
   - Reporting currency — the currency the financial statements are
     denominated in.

## Dependencies

- MCP: none (this skill is filing-driven).
- Other skills consumed: none. This is the entry point.

## Output schema

JSON written to `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/company-profile.json`:

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "sector": "Information Technology",
  "reporting_currency": "USD",
  "business_model": "...",
  "segments": [{"name": "iPhone", "revenue_share_pct": 52.0, "source": "..."}],
  "geography": [{"region": "Americas", "revenue_share_pct": 43.0, "source": "..."}],
  "management": [{"role": "CEO", "name": "...", "since": "...", "source": "..."}],
  "competitors": [{"name": "...", "source": "..."}],
  "supply_chain_risks": [{"risk": "...", "source": "..."}]
}
```

## Source citation policy

Every entry has a `source:` field pointing to the exact filing URL and page
or section. Statements without sources are invalid and must be re-derived.
