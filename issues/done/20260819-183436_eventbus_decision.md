# [Decision record] Keep eventbus `_REMOVED_CONFIG_KEYS` startup-failure guard permanently

**IMPLEMENTATION PROHIBITED — decision documentation only, per AGENTS.md
Global Rule 8 ("eventbus に関連する実装は絶対にしないこと"). Do not implement
any change to `scripts/eventbus/` based on this issue without a Global Rule 8
change or explicit, separate maintainer authorization. Debugging and
investigation of eventbus code remain permitted; implementation does not.**

## Context

`requires/done/20260818-224506_require.md` asked whether the
`_REMOVED_CONFIG_KEYS = ("poll_interval_ms", "offset_checkpoint_interval")`
hard-fail guard in `scripts/eventbus/config.py::load_config` (lines 69-83)
should remain permanently or be retired now that the deprecation window has
likely passed.

## Decision

**Keep the guard permanently, unchanged.**

## Rationale

- `load_config` runs once at process startup
  (`scripts/eventbus/config.py:72`), so the cost of a hard failure is a
  refused startup with a precise, actionable error message ("delete them from
  {path}") — not an ongoing runtime cost.
- A "warn and continue" relaxation would risk an operator running with a
  silently-ignored stale config, which is strictly worse than a loud,
  self-explaining startup failure.
- There is no evidence available to this workflow that the deprecation window
  has definitively closed for every deployed config (this requires checking
  the live production `/opt/llm/config/eventbus.toml`, which is outside the
  scope and tooling of a requirement-to-plan document pass). Retiring the
  guard without that confirmation would be premature.

## What would change this decision

If a maintainer with access to the production eventbus config confirms no
deployed config has referenced `poll_interval_ms`/`offset_checkpoint_interval`
for a defined, closed deprecation window, and that closure is worth
formalizing in code, this decision may be revisited. Any resulting code change
still requires a Global Rule 8 exception before implementation.

## Traceability

- Workflow phase: requirement-to-plan
- Source requirement: requires/done/20260818-224506_require.md
- Source plan: plans/20260819-183436_plan.md
- Generated at: 20260819-183436
