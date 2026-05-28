---
description: Parses the latest earnings release and conference-call transcript. Extracts beat/miss vs consensus, management guidance, tone, and the Q&A signal. Use for the most recent quarter and the prior three quarters to detect trend changes.
allowed-tools: Read, Write, Grep, Glob, WebFetch, WebSearch, Bash
---

# earnings-analysis

## Purpose

Single-responsibility skill: turn a quarterly earnings event into a
structured signal. The output feeds `news-intelligence`, `bull-bear-thesis`,
and `report-composer`.

## Inputs

- `ticker` (required).
- Optional: `quarter` (e.g. `Q1-FY26`). Defaults to the latest reported.

## Methodology

1. **Fetch artefacts.**
   - 8-K filing containing the earnings press release (US issuers) — SEC EDGAR.
   - The earnings press release PDF / HTML from the IR site.
   - The conference-call transcript — first via `financial-datasets` MCP if
     available; otherwise via `WebFetch` of the IR site or a major transcript
     provider.
   - Consensus estimates — via `financial-datasets` MCP (analyst estimates
     endpoint).
2. **Compute beats/misses** for: revenue, gross margin, operating margin, EPS,
   guidance vs prior guidance. Express each as `actual - consensus` and as a
   percentage.
3. **Extract management guidance** verbatim. Map each guidance line to the
   line item on the income statement it constrains.
4. **Score tone.** From the prepared-remarks transcript, classify each
   forward statement on a `confident / measured / cautious / defensive` scale.
   Cite the exact quote.
5. **Q&A signal.** Identify the three questions analysts pressed on hardest
   (multiple analysts asked, or management deflected). These are usually
   where the next disappointment lives.

## Dependencies

- Consumes: `company-profile` (segment list to map guidance correctly).
- MCP: `financial-datasets` (analyst estimates, transcripts where available).
- Web: `WebFetch` for the 8-K and IR-site artefacts as fallback.

## Output schema

JSON at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/earnings/<QUARTER>.json`:

```json
{
  "quarter": "Q1-FY26",
  "reported_on": "2026-04-30",
  "beats_misses": {"revenue": {"actual_usd_m": ..., "consensus_usd_m": ..., "delta_pct": ..., "source": "..."}},
  "guidance": [{"line": "revenue", "value": "...", "vs_prior": "raised|maintained|lowered", "quote": "...", "source": "..."}],
  "tone": [{"topic": "...", "label": "confident|measured|cautious|defensive", "quote": "...", "source": "..."}],
  "qa_pressure_points": [{"topic": "...", "analysts": ["..."], "deflection": true, "source": "..."}]
}
```

## Source citation policy

Every quote carries a `source:` pointing to the transcript URL + speaker +
approximate timestamp or paragraph. Every consensus figure cites the MCP
endpoint and as-of date.
