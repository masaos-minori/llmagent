# `ProductionConfigValidator._check_unknown_top_level_keys()` is dead code duplicating the active unknown-key check with a different, inconsistent field set

## Priority
Medium

## Summary
`ProductionConfigValidator` (`scripts/shared/production_config_validator.py`) contains
two separate implementations of "check for unknown top-level config keys":
`_check_unknown_top_level_keys()` (an instance method) and `_check_unknown_production_keys()`
+ `_get_valid_production_keys()` (a static method plus a module-level function). Only the
second pair is actually called (from `validate()`); `_check_unknown_top_level_keys()` has
zero callers anywhere in `scripts/` or `tests/` (confirmed via `rg`). The two
implementations also derive a different "known fields" set:
`_check_unknown_top_level_keys()` additionally includes `AgentConfig`'s own dataclass
fields (via `dataclasses.fields(AgentConfig)`), while the active
`_get_valid_production_keys()` instead hardcodes exactly two extra strings
(`"system_prompt_tool"`, `"security_profile"`) rather than introspecting `AgentConfig`.

## Background
Discovered while investigating `build_agent_config()`'s exact input-shape contract
during `plans/done/20260908-221312_plan.md` (cfgval001)'s freeze-validation re-entry.
`_check_unknown_top_level_keys()` (defined immediately after
`_get_valid_production_keys()` in the same file) imports the same 9 sub-config
dataclasses plus `AgentConfig` itself, and returns unknown keys the same way
`_check_unknown_production_keys()` does — but is never invoked; `validate()` (the only
call site of either check) calls `_check_unknown_production_keys()`/
`_get_valid_production_keys()` exclusively.

## Problem
This is a maintainability and correctness-drift risk: a maintainer reading
`ProductionConfigValidator` may reasonably assume `_check_unknown_top_level_keys()` is
the active check (it is defined first, and its name and docstring both plausibly
describe the class's actual behavior), edit it expecting it to take effect, and be
surprised when `validate()`'s behavior does not change. The two implementations'
differing field derivation (one omits `AgentConfig`'s own fields via introspection and
hardcodes 2 literal strings instead; the other includes them) is itself evidence they
were not kept in sync, and any future edit to one without the other risks silently
diverging further.

## Reason for Change
Dead code that closely resembles the live code path it duplicates is a common source of
confused future edits (fixing the wrong copy) and wasted investigation time (as occurred
in this session while establishing `build_agent_config()`'s exact contract for
cfgval001). Removing or consolidating it eliminates that risk.

## Implementation Intent
Confirm via `git log` whether `_check_unknown_top_level_keys()` predates
`_check_unknown_production_keys()`/`_get_valid_production_keys()` (an abandoned first
draft, most likely) or postdates it (a newer, currently-unwired replacement attempt).
If it is an abandoned draft, remove it. If it appears to be an intended replacement that
was never wired in, evaluate whether its `AgentConfig`-inclusive field derivation is
actually more correct than the active implementation's hardcoded 2-string approach
(REQ-relevant: `AgentConfig` may have fields beyond `system_prompt_tool`/
`security_profile` that the active check currently misses) before deciding whether to
wire it in as a replacement instead of deleting it.

## Target Files or Areas
- `scripts/shared/production_config_validator.py`
  (`_check_unknown_top_level_keys()`, `_check_unknown_production_keys()`,
  `_get_valid_production_keys()`)

## Required Changes
Deferred until the Implementation Intent's git-history check determines whether to
delete `_check_unknown_top_level_keys()` outright or reconcile the two implementations'
field derivation.

## Constraints
Do not change `_check_unknown_production_keys()`/`_get_valid_production_keys()`'s
currently-active behavior as a side effect of removing the dead method, unless the
investigation above concludes the active implementation itself has a field-derivation
gap worth fixing (e.g. missing `AgentConfig`'s own fields beyond the 2 hardcoded
strings) — if so, file that as a distinct, separate concern rather than folding it
silently into this cleanup.

## Acceptance Criteria
- [ ] `_check_unknown_top_level_keys()` is either removed, or reconciled with
  `_get_valid_production_keys()` so both implementations derive an identical field set
- [ ] `rg -n "_check_unknown_top_level_keys" scripts/ tests/` returns no result if removed,
  or only call sites consistent with the reconciled design if kept
- [ ] `uv run pytest tests/shared/test_production_config_validator.py -q` still passes

## Testing Expectations
- `uv run pytest tests/shared/test_production_config_validator.py -q` — no regression
- `uv run vulture scripts/shared/production_config_validator.py --min-confidence 80` —
  confirms the dead method is flagged (or no longer present)

## Documentation Impact
N/A: internal implementation detail; no documented behavior change.

## Out of Scope
- `plans/done/20260908-221312_plan.md` (cfgval001)'s own fix.
- `issues/20260909-183426_toolcache01_removed-tool-result-caching-leaves-orphaned-config-keys-and-stale-references.md` —
  unrelated root cause, tracked separately.

## Dependencies
N/A: none. Discovered independently while investigating cfgval001's revalidation.

## Unresolved Questions
Whether `_check_unknown_top_level_keys()` predates or postdates the active
`_check_unknown_production_keys()`/`_get_valid_production_keys()` pair, and therefore
whether it represents an abandoned draft (delete) or an unwired improvement (reconcile)
— resolve via `git log -p -S"_check_unknown_top_level_keys" --
scripts/shared/production_config_validator.py` before implementing.

## AI Implementation Instruction
Check the git history question above before choosing delete-vs-reconcile. If deleting,
remove only `_check_unknown_top_level_keys()` and its now-unused imports specific to
that method — do not touch `_check_unknown_production_keys()`/`_get_valid_production_keys()`
unless the investigation concludes a field-derivation gap needs fixing, and if so, file
that separately rather than expanding this issue's scope.
