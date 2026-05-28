# Assumptions reference — v2 template

Every writeable input in `fundamental_model_template_v2.xlsx`. Each entry
corresponds to a named range with the `in_*` prefix in `cell_map.json`.

The Assumptions tab layout:
- **Column B** — label
- **Column C** — Bull value (or single value for non-scenario inputs)
- **Column D** — Base value (or active formula for DCF inputs)
- **Column E** — Bear value
- **Column F+** — additional forecast years (C=Year 1 through J=Year 8)
- **Column L** — source annotation (written by `fill_model.py`, read by validator)

Source annotation is **mandatory** for every written cell. A missing source
causes `validate_model.py` check #6 to fail.

---

## Scenario-aware operating drivers

These inputs come in Bull / Base / Bear rows. The `→ Active` row below each
triplet is a formula (`=IF($C$9=1, bull, IF($C$9=2, base, bear))`) and is
**never written directly**.

### Revenue growth %

| named range | scenario | cell | units | plausibility |
|---|---|---|---|---|
| `in_rev_growth_bull` | bull | C15 | decimal (e.g. 0.09) | −0.5 to 2.0 |
| `in_rev_growth_base` | base | C16 | decimal | −0.5 to 2.0 |
| `in_rev_growth_bear` | bear | C17 | decimal | −0.5 to 2.0 |

Source: `earnings-analysis.json → consensus.revenue_growth_next_year` (base);
bull/bear derived via `scenario_deltas.json`.

### Gross margin %

| named range | scenario | cell | units |
|---|---|---|---|
| `in_gross_margin_bull` | bull | C21 | decimal |
| `in_gross_margin_base` | base | C22 | decimal |
| `in_gross_margin_bear` | bear | C23 | decimal |

Source: `financial-statements.json → annual[-1].gross_margin`.

### SG&A % of revenue

| named range | scenario | cell | units |
|---|---|---|---|
| `in_sga_pct_bull` | bull | C27 | decimal |
| `in_sga_pct_base` | base | C28 | decimal |
| `in_sga_pct_bear` | bear | C29 | decimal |

Source: `financial-statements.json → annual[-1].sga_pct_revenue`.

### R&D % of revenue

| named range | scenario | cell | units |
|---|---|---|---|
| `in_rnd_pct_bull` | bull | C33 | decimal |
| `in_rnd_pct_base` | base | C34 | decimal |
| `in_rnd_pct_bear` | bear | C35 | decimal |

Source: `financial-statements.json → annual[-1].rd_pct_revenue`.

### Tax rate %

| named range | scenario | cell | units |
|---|---|---|---|
| `in_tax_rate_bull` | bull | C39 | decimal |
| `in_tax_rate_base` | base | C40 | decimal |
| `in_tax_rate_bear` | bear | C41 | decimal |

Source: `financial-statements.json → annual[-1].effective_tax_rate`.

### Dividend payout %

| named range | scenario | cell | units |
|---|---|---|---|
| `in_payout_bull` | bull | C45 | decimal |
| `in_payout_base` | base | C46 | decimal |
| `in_payout_bear` | bear | C47 | decimal |

Source: `financial-statements.json → annual[-1].dividend_payout_ratio`.
Optional (not critical).

---

## DCF inputs — scenario-aware (rows 62–66)

For DCF inputs the column layout is: C=Bull, D=Base, E=Bear, F=Active formula.

### Terminal growth rate g %

| named range | scenario | cell | units | plausibility |
|---|---|---|---|---|
| `in_tgr_bull` | bull | C63 | decimal | 0 to 0.05 |
| `in_tgr_base` | base | D63 | decimal | 0 to 0.05 |
| `in_tgr_bear` | bear | E63 | decimal | 0 to 0.05 |

Source: `macro-context.json → long_term_growth_rate` (base). Default fallback: 0.025.

### Equity risk premium %

| named range | scenario | cell | units |
|---|---|---|---|
| `in_erp_bull` | bull | C64 | decimal |
| `in_erp_base` | base | D64 | decimal |
| `in_erp_bear` | bear | E64 | decimal |

Source: `macro-context.json → equity_risk_premium`. Default fallback: 0.055.

### Levered beta

| named range | scenario | cell | units | plausibility |
|---|---|---|---|---|
| `in_beta_bull` | bull | C65 | ratio | 0 to 3.0 |
| `in_beta_base` | base | D65 | ratio | 0 to 3.0 |
| `in_beta_bear` | bear | E65 | ratio | 0 to 3.0 |

Source: `valuation-multiples.json → beta`.

### Terminal EV/EBITDA exit multiple

| named range | scenario | cell | units |
|---|---|---|---|
| `in_exit_mult_bull` | bull | C66 | x |
| `in_exit_mult_base` | base | D66 | x |
| `in_exit_mult_bear` | bear | E66 | x |

Source: `valuation-multiples.json → ev_ebitda_forward`. Optional.

---

## Non-scenario inputs

### Scenario selector

| named range | cell | sheet | value |
|---|---|---|---|
| `in_scenario` | C9 | Assumptions | 1=Bull, 2=Base, 3=Bear |

Default: 2 (Base). Controls the `→ Active` row formulas throughout the model.

### Debt Schedule inputs

| named range | cell | units | notes |
|---|---|---|---|
| `in_term_loan_open` | C6 | USD | Opening term-loan balance |
| `in_term_loan_amort` | C7 | USD | Annual amortization |
| `in_term_loan_rate` | C8 | decimal | Interest rate on term loan |
| `in_revolver_rate` | C9 | decimal | Revolving credit facility rate. Default: 0.065 |
| `in_min_cash` | C10 | USD | Minimum cash balance (triggers revolver draw) |

Sources: `financial-statements.json` for debt balances; constant for revolver rate.

### PP&E Schedule inputs

| named range | cell | units | notes |
|---|---|---|---|
| `in_ppe_useful_life` | C11 | years | Useful life for straight-line depreciation |

Source: `financial-statements.json → annual[-1].ppe_useful_life_years`. Default fallback: 10.

---

## Read-only outputs (never written)

| named range | sheet | cell | description |
|---|---|---|---|
| `out_wacc` | DCF | C10 | Computed WACC |
| `out_enterprise_value` | DCF | C31 | Enterprise value |
| `out_equity_value` | DCF | C33 | Equity value |
| `out_value_per_share` | DCF | C35 | Equity value per share |
| `out_upside` | DCF | C37 | (Value per share / current price) − 1 |
| `out_tv_pct_ev` | DCF | C38 | Terminal value as % of EV |
| `out_comps_avg_vps` | Comps | E17 | Average comparable-company value per share |

---

## Built-in check cells (read by validator check #7)

| named range | sheet | cell | passes when |
|---|---|---|---|
| `chk_bs_balance` | Checks | C6 | Assets = Liabilities + Equity |
| `chk_cf_tie` | Checks | C7 | Δcash on CF = Δcash on BS |
| `chk_wacc_gt_g` | Checks | C8 | WACC > terminal growth rate |
| `chk_tv_pct` | Checks | C9 | Terminal value ≤ 75% of enterprise value |
| `chk_int_coverage` | Checks | C10 | EBIT / Interest expense ≥ 1 |
| `chk_revolver_nonneg` | Checks | C11 | Revolver balance ≥ 0 |
| `chk_scenario_valid` | Checks | C12 | `in_scenario` ∈ {1, 2, 3} |

These cells return TRUE/FALSE (or a numeric difference near 0). They are
evaluated by Excel on the last save. When `validate_model.py` reads them
via `data_only=True`, None means the file was never opened in Excel — the
check is skipped with a warning, not failed.

---

## Critical vs optional inputs

**Critical** (validator check #8 blocks delivery if MISSING):

`in_rev_growth_*`, `in_gross_margin_*`, `in_sga_pct_*`, `in_tax_rate_*`,
`in_beta_*`, `in_erp_*`, `in_tgr_*` — all three scenarios each.

**Optional** (MISSING is allowed, model still delivers):

`in_rnd_pct_*`, `in_payout_*`, `in_exit_mult_*`, `in_term_loan_*`,
`in_revolver_rate`, `in_ppe_useful_life`, `in_min_cash`.
