# Agent-Finance — Market Finance Research Plugin Marketplace

## Mission

This repository is a **Claude Code plugin marketplace** that ships the
`agent-finance` plugin: a decision-support research harness for publicly
traded companies. It is **never investment advice**. Every forecast is an
explicitly labeled assumption, not a prediction.

The marketplace pattern lets future plugins (e.g. `sector-screener`,
`options-research`) ship from the same repo without restructuring.

## Ground rules (non-negotiable)

1. **Decision-support only**, never investment advice. Every forecast carries an
   `assumption:` label and a `source:` reference.
2. **Primary data source**: Financial Datasets MCP (`financial-datasets` server,
   remote HTTP). Standardized endpoints for income / balance sheet / cash flow /
   prices / ratios.
3. **Secondary sources**: native `WebSearch` and `WebFetch` for news, earnings
   transcripts, company profiles, regulatory filings.
4. **Fallback for primary filings**: SEC EDGAR (10-K, 10-Q, 8-K, DEF 14A, Form 4,
   13F).
5. **Always cite sources** in every output. Each datapoint, ratio, or claim must
   carry a URL or filing reference. Outputs without citations are invalid.
6. **Language**: every harness file — CLAUDE.md, agent files, SKILL.md files,
   code, comments, generated reports — is written in **English**.
7. **Currency handling**: detect the company's reporting currency on first
   contact. Never mix currencies inside a model without an explicit FX note
   stating the rate, the rate's source, and the as-of date.
8. **Excel formulas never contain hardcoded numbers.** All inputs live on the
   `Assumptions` tab. A formula that references a literal value instead of an
   Assumptions cell is a bug.
9. **Never write Excel cells by literal coordinate.** Always resolve through
   `cell_map.json` (logical name -> named range -> cell). This rule is
   non-negotiable; bypassing it breaks the cohesion guarantees of the model.

## MCP tool inventory (Financial Datasets)

Each skill calls the following MCP tools. Names are the expected endpoints
from the `financial-datasets` MCP server; verify against the server's
actual tool list on first run.

- `company-profile` — none (filing-driven via WebFetch / EDGAR).
- `financial-statements` — income-statements, balance-sheets,
  cash-flow-statements (annual + quarterly).
- `historical-baseline` — same as financial-statements, extended history.
- `earnings-analysis` — analyst estimates, transcripts (where available).
- `fundamental-research` — ratios (ROIC).
- `news-intelligence` — news / sentiment (if exposed).
- `valuation-multiples` — prices, shares outstanding, ratios.
- `risk-assessment` — debt detail (if exposed).
- `insider-institutional` — insider trades, institutional ownership,
  short interest.
- `macro-context` — commodity prices (if exposed).

## Repository layout

```
Agent-Finance/                                      (the marketplace repo)
├── .claude-plugin/
│   └── marketplace.json                            ← marketplace manifest
├── plugins/
│   └── agent-finance/                              ← the plugin
│       ├── .claude-plugin/
│       │   └── plugin.json                         ← plugin manifest
│       ├── .mcp.json                               ← Financial Datasets MCP
│       ├── agents/                                 ← orchestrator, _template-company, sector-analyst
│       └── skills/                                 ← 12 research skills + excel-financial-model + model-input-builder
├── CLAUDE.md
├── README.md
├── .env.example
└── requirements.txt                                (dev-only)
```

Plugin-relative paths use the env vars Claude Code exports to every plugin
subprocess:

- `${CLAUDE_PLUGIN_ROOT}` — absolute path to the plugin install dir
  (`~/.claude/plugins/cache/agent-finance/...` once installed; the local
  `plugins/agent-finance/` dir when loaded via `--plugin-dir`).
- `${CLAUDE_PLUGIN_DATA}` — persistent per-plugin data dir (survives
  updates). Used for per-company cache:
  `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`.
- `${CLAUDE_PROJECT_DIR}` — the user's project root. Used for deliverables:
  `${CLAUDE_PROJECT_DIR}/output/agent-finance/reports/` and
  `${CLAUDE_PROJECT_DIR}/output/agent-finance/models/`.

Inside Claude Code, the plugin's skills are namespaced:
`/agent-finance:company-profile`, `/agent-finance:report-composer`, etc.

## Required environment

Set the Financial Datasets API key in your shell before launching Claude
Code. The plugin's `.mcp.json` reads it via `${FINANCIAL_DATASETS_API_KEY}`
expansion.

```
FINANCIAL_DATASETS_API_KEY=<your key from financialdatasets.ai>
```

For local dev, `.env.example` at the repo root documents the variable;
copy it to `.env` (git-ignored) and source it before launching.

## How a request flows

1. User asks for research on a ticker.
2. The `orchestrator` agent picks the skills relevant to the question and
   spawns the per-company sub-agent from `_template-company.md` (with
   placeholders filled in).
3. The sub-agent pulls data through the relevant skills, caches raw responses
   under `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`, and accumulates
   per-company learnings in project memory.
4. The sub-agent runs `model-input-builder` to transform the JSON caches into
   `values.json` + `sources.json` (3 scenarios: Bull / Base / Bear).
5. The sub-agent runs `excel-financial-model/fill_model.py` to produce the
   filled xlsx, then `validate_model.py` (9 blocking checks). The model is
   **not delivered** if validation fails or any critical input is MISSING.
6. The sub-agent returns a **summary** (not raw dumps) to the orchestrator.
7. For multi-company comparisons, the `sector-analyst` agent consumes the
   `valuation-multiples` output of each company.
8. `report-composer` assembles a single, consistent deliverable in
   `${CLAUDE_PROJECT_DIR}/output/agent-finance/reports/`.

## Safety checks before delivery

A research output may not be returned to the user until:

- Every figure carries a `source:` field.
- The Excel model (if produced) passes `validate_model.py` with zero failures
  across all 9 checks. No MISSING critical inputs remain.
- All three scenarios (Bull / Base / Bear) are fully populated — no partial
  fills. Check #9 enforces this.
- The bull and bear theses are both argued in `bull-bear-thesis` (explicit
  confirmation-bias antidote).
- All currencies in the model are consistent or accompanied by an FX note.
