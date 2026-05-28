---
name: model-input-builder
plugin: agent-finance
description: >
  Transforms MCP JSON caches into values.json + sources.json ready for
  fill_model.py. Applies Bull/Bear deltas. Never invents data — every
  missing datapoint is marked MISSING:<reason>.
---

# model-input-builder

**Responsibility**: Single-purpose bridge between MCP data caches and the
Excel financial model. Input: raw JSON files under
`${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`. Output: two JSON files consumed
by `excel-financial-model/fill_model.py`.

## Invocation

```bash
python build_inputs.py --ticker AAPL
```

Optional overrides:
```bash
python build_inputs.py --ticker AAPL \
  --cache-dir /path/to/caches \
  --output-dir /path/to/model_inputs
```

## Output files

Both files land in `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/model_inputs/`:

- `values.json` — `{logical_name: value}` (or `{"missing": "<reason>"}`)
- `sources.json` — `{logical_name: source_string}`

## MISSING guardrail

If a required datapoint is absent from the MCP cache, `build_inputs.py`:
1. Sets `values[name] = {"missing": "<reason>"}`.
2. Sets `sources[name] = "MISSING: <reason>"`.
3. Reports `missing_critical_count` in its JSON summary.

`fill_model.py` propagates MISSING cells (blank value, annotated source
column). `validate_model.py` checks #7 blocks delivery if any critical
input remains MISSING.

## Scenario logic

| Scenario | Source |
|----------|--------|
| Base     | Direct from MCP cache |
| Bull     | `base + delta["bull"]` from `reference/scenario_deltas.json` |
| Bear     | `base + delta["bear"]` from `reference/scenario_deltas.json` |

Deltas are explicit, version-controlled, and documented in
`reference/scenario_deltas.json`. No silent extrapolation.

## Reference files

- `reference/mcp_to_logical.json` — maps each `in_*_base` logical name to a
  JSON path inside the appropriate cache file. One entry per base input.
- `reference/scenario_deltas.json` — Bull/Bear deltas per metric.

## Adding a new input

1. Add a named range to the Excel template (prefix `in_`).
2. Run `extract_cell_map.py` to regenerate `cell_map.json`.
3. Add a mapping entry to `mcp_to_logical.json`.
4. Add a delta entry to `scenario_deltas.json` (if applicable).
5. Re-run `build_inputs.py` and `test_pipeline.py`.
