---
description: Surfaces recent catalysts, sentiment shifts, regulatory events, M&A activity, and analyst rating changes affecting the company. Use after earnings-analysis to add the post-earnings news flow and any cross-cutting events between earnings prints.
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# news-intelligence

## Purpose

Pull the news flow that moves the stock between earnings prints. Classify
each event by type and assess directional impact.

## Inputs

- `ticker` (required).
- Optional: `lookback_days` (default: 90).

## Methodology

1. **Search the news.** `WebSearch` for the ticker and the company name over
   the lookback window. Prefer primary sources (company press releases,
   regulator filings, court documents) over secondary commentary.
2. **Classify each event** into one of:
   - `M&A` — announced, rumored, or pending acquisition / divestiture.
   - `regulatory` — antitrust, FDA, FTC, SEC enforcement, EU action.
   - `litigation` — new suit, settlement, judgment.
   - `rating-change` — credit rating or sell-side rating change.
   - `management` — executive departure, board change.
   - `product` — launch, recall, major design win or loss.
   - `macro` — sector-wide event affecting this company.
3. **Score directional impact** on a `materially-positive / mildly-positive /
   neutral / mildly-negative / materially-negative` scale. Cite the specific
   element that drives the score.
4. **Cross-check** against the earnings transcript: did management address
   this event? If yes, capture the framing.

## Dependencies

- Consumes: `company-profile` (to recognize what is in-scope), optionally
  `earnings-analysis` for cross-check.
- MCP: `financial-datasets` if a news/sentiment endpoint is available.
- Web: `WebSearch` + `WebFetch` for primary sources.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/news-intelligence.json`:

```json
{
  "lookback_days": 90,
  "events": [
    {
      "date": "2026-04-15",
      "type": "regulatory",
      "headline": "...",
      "summary": "...",
      "directional_impact": "mildly-negative",
      "rationale": "...",
      "addressed_in_earnings": true,
      "management_framing": "...",
      "source": "..."
    }
  ]
}
```

## Source citation policy

Every event carries the primary-source URL. Secondary commentary is allowed
only as supporting context and must be labeled as such.
