---
description: Assembles every per-skill output for a ticker into one consistent, fully cited deliverable in ${CLAUDE_PROJECT_DIR}/output/agent-finance/reports/. Use last in the pipeline after every other skill has produced its JSON or markdown artifact. Invocable directly with /report-composer once a ticker has been fully researched.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# report-composer

## Purpose

Take the JSON / markdown artifacts produced by the other skills under
`${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/` and emit a single, structured research note in
`${CLAUDE_PROJECT_DIR}/output/agent-finance/reports/<TICKER>_<YYYY-MM-DD>.md`. The note is the only thing the
user sees; it must stand alone.

## Inputs

- `ticker` (required).
- All artifacts under `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/` produced by the other skills.

## Methodology

1. **Verify completeness.** Every required artifact must exist. If any is
   missing, list the missing ones and stop — do not produce a partial
   report.
2. **Assemble** the markdown report in this fixed order:
   1. Header — ticker, company name, sector, reporting currency, report date.
   2. Decision-support disclaimer (one line, verbatim from CLAUDE.md).
   3. Headline view — 3 to 5 bullets from `bull-bear-thesis.md` working view.
   4. Business — from `company-profile`.
   5. Financials — from `financial-statements` and `historical-baseline`.
   6. Latest quarter — from `earnings-analysis` (most recent).
   7. Fundamental view — from `fundamental-research`.
   8. News flow — from `news-intelligence`.
   9. Valuation — from `valuation-multiples`.
   10. Risk catalogue — from `risk-assessment`.
   11. Insider & institutional — from `insider-institutional`.
   12. Macro frame — from `macro-context`.
   13. Bull case — verbatim from `bull-bear-thesis.md`.
   14. Bear case — verbatim from `bull-bear-thesis.md`.
   15. Working view — verbatim from `bull-bear-thesis.md`.
   16. Sources index — every URL cited, grouped by skill.
   17. Model — link to `${CLAUDE_PROJECT_DIR}/output/agent-finance/models/<TICKER>_<DATE>.xlsx`
       if produced by `excel-financial-model`; omit the section if no model exists.
3. **Validate citations.** Every numeric figure in the report must carry an
   inline `[source: ...]` and appear in the sources index. Scan and fail if
   any figure is unsourced.
4. **Currency check.** Every monetary figure states a currency. Mixed
   currencies require an FX note adjacent to the figure.

## Dependencies

- Consumes: every other skill's output for the ticker.

## Output schema

Markdown at `${CLAUDE_PROJECT_DIR}/output/agent-finance/reports/<TICKER>_<YYYY-MM-DD>.md`. Section anchors are
fixed (the orchestrator and downstream tooling may link into them).

## Source citation policy

This skill is the **citation enforcer**. It refuses to produce the report
if any consumed artifact contains an unsourced figure. The error message
names the offending artifact and field.

## Hard rules

- Never paraphrase a quote that another skill captured verbatim. Copy it
  through with the original attribution.
- Never aggregate two different currencies without an explicit FX note that
  states the rate, the source, and the as-of date.
- Never label any output as investment advice; the disclaimer line is fixed.
