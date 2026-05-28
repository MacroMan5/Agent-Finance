# Changelog

## [0.1.0] - 2026-05-28

Initial release.

- 13 skills covering company profile, financial statements, historical
  baseline, earnings analysis, fundamental research, news intelligence,
  valuation multiples, risk assessment, insider/institutional, macro
  context, bull/bear thesis, report composer, Excel financial model.
- 3 agents: orchestrator, `_template-company`, sector-analyst.
- Financial Datasets MCP wired via `${FINANCIAL_DATASETS_API_KEY}`.
- Excel 3-statement skeleton (IS + BS + CF wired and closing on each
  other); DCF and Sensitivity tabs stubbed (formulas TODO).
- Validator with 6 blocking checks: balance-sheet identity, cash-flow
  tie-out, no error cells, segment sums (vacuous on skeleton),
  plausibility bounds, source traceability.
