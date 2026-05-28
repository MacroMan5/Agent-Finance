---
description: Argues both the bull case and the bear case for the company in equal depth. Explicit confirmation-bias antidote — both scenarios are framed with specific milestones, key risks, and what would invalidate each thesis. Use last in the per-company pipeline, before report-composer.
allowed-tools: Read, Write, Grep, Glob, Bash
---

# bull-bear-thesis

## Purpose

Force a symmetric treatment of upside and downside. The skill output is two
arguments of comparable length, each one trying its hardest to make its
case. Confirmation-bias antidote: a one-sided thesis is a sign the analysis
is incomplete.

## Inputs

- `ticker` (required).
- All prior skill outputs for this ticker.

## Methodology

1. **Build the bull case** — 3 to 5 numbered pillars. Each pillar:
   - Claim (one sentence).
   - Evidence (cites specific outputs from `fundamental-research`,
     `historical-baseline`, `earnings-analysis`, `news-intelligence`).
   - Milestones — what the next 12 months should produce if the thesis is
     right.
   - Invalidation — the specific datapoint or event that would break this
     pillar.
2. **Build the bear case** — same structure, equal length. The pillars draw
   on `risk-assessment`, `news-intelligence`, the `qa_pressure_points` from
   `earnings-analysis`, and the anomalies from `historical-baseline`.
3. **Stress-test both.** For each side, list one piece of evidence the other
   side would weaponize. Acknowledge it honestly.
4. **State your view.** One paragraph, with explicit weights on bull vs bear
   pillars. This is the only place a directional view is allowed in the
   harness. It is still framed as a labeled assumption.

## Dependencies

- Consumes: every other skill's output for this ticker.

## Output schema

Markdown at `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/bull-bear-thesis.md`:

```markdown
# Bull case
1. **Pillar.** Claim. Evidence: ... (source). Milestones: .... Invalidation: ....
2. ...

# Bear case
1. **Pillar.** Claim. Evidence: ... (source). Milestones: .... Invalidation: ....
2. ...

# Stress test
- The bull's strongest point against the bear: ...
- The bear's strongest point against the bull: ...

# Working view
Assumption-weighted stance: bull X% / bear Y%. Rationale: ....
```

## Source citation policy

Every pillar cites the specific prior-skill output it draws on, with a path
under `${CLAUDE_PLUGIN_DATA}/companies/<TICKER>/`. The working view explicitly labels itself
`assumption:`.
