# Agent-Finance Marketplace

A Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
that ships the **`agent-finance`** plugin — a decision-support research
harness for publicly traded companies (company profiles, financial
statements, valuation, DCF, sector comps, bull/bear thesis, Excel 3-statement
modeling).

This repo is **not** investment advice. Every forecast carries an explicit
`assumption:` label and every datapoint carries a `source:` reference.

## Plugins in this marketplace

| Plugin | Version | Description |
|---|---|---|
| `agent-finance` | 0.1.0 | Market-finance research harness: 14 skills, 3 agents, Financial Datasets MCP, 3-statement Excel models with DCF and multi-scenario (Bull/Base/Bear). |

## Install

### Prerequisite — Financial Datasets API key

Get an API key at [financialdatasets.ai](https://financialdatasets.ai) and
export it in your shell before launching Claude Code:

```bash
export FINANCIAL_DATASETS_API_KEY="your-key-here"
```

On Windows PowerShell:

```powershell
$env:FINANCIAL_DATASETS_API_KEY = "your-key-here"
```

The plugin's `.mcp.json` reads it via `${FINANCIAL_DATASETS_API_KEY}`
expansion. Without it, `financial-datasets` MCP calls return auth errors.

### Option A — install from this marketplace

```bash
# Add the marketplace once
/plugin marketplace add <git-url-of-this-repo>

# Install the plugin
/plugin install agent-finance@agent-finance-marketplace
```

### Option B — local development / testing

Load the plugin directly from a checkout, without publishing:

```bash
claude --plugin-dir ./plugins/agent-finance
```

Validate the plugin manifest and structure:

```bash
claude plugin validate ./plugins/agent-finance
```

## Usage

Once the plugin is enabled, the orchestrator routes research requests:

```
> Research AAPL — full company package.
> Compare AAPL, MSFT, GOOGL on valuation.
> What's the FY-1 EBIT margin for NVDA?
```

Skills are exposed as `/agent-finance:<skill>` (e.g.
`/agent-finance:company-profile`, `/agent-finance:report-composer`).

Outputs land in your project under:

- `output/agent-finance/reports/` — composed Markdown deliverables.
- `output/agent-finance/models/` — filled Excel 3-statement models.

Per-company cache (raw API responses, fetched filings) lives in the plugin's
persistent data dir (`${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`) and
survives plugin updates.

## Excel model pipeline

The `excel-financial-model` skill uses `fundamental_model_template_v2.xlsx`
(11 sheets, 86 named ranges, full DCF and Scenario & Sensitivity). The pipeline:

```
MCP data skills → model-input-builder → fill_model.py → validate_model.py
                                         (cell_map.json)   (9 blocking checks)
```

All three scenarios (Bull / Base / Bear) are filled in a single run. Base values
come from MCP data; Bull/Bear are derived from explicit, configurable deltas in
`scenario_deltas.json`. No data is invented — missing MCP fields are marked
`MISSING:<reason>` and block delivery if critical.

## Repository layout

See [`CLAUDE.md`](CLAUDE.md) for the full layout, ground rules, and request
flow.

## Python development dependencies

The `excel-financial-model` and `model-input-builder` skills use `openpyxl`.
To run the scripts outside the plugin runtime (e.g. for skill development):

```bash
pip install -r requirements.txt
```

Run the integration tests:

```bash
pytest plugins/agent-finance/skills/excel-financial-model/tests/test_pipeline.py -v
```

## License

MIT.
