# Clarify `ConfigReloadOutcome.skipped` vs `startup_only` semantics

## Priority
Low

## Summary
`ConfigReloadOutcome` exposes both `skipped` and `startup_only`. Their intended distinction (unrecognized/ignored vs. requires-restart) is easy to conflate, which can confuse operators reading `/reload` output. Verified: `skipped` already has a docstring-style comment explaining its meaning; `startup_only` has none at all.

## Background
N/A: covered by Summary.

## Problem
Verified in `scripts/agent/services/config_reload.py`, the `ConfigReloadOutcome` dataclass:
```
skipped: list[str] = field(default_factory=list)
"""Fields intentionally ignored by /reload for reasons other than restart-
required (e.g. unrecognized keys). MCP server definition changes are never
reported here — see needs_restart instead."""
source_files: list[str] = field(default_factory=list)
startup_only: list[str] = field(default_factory=list)
```
`skipped` already carries an explanatory docstring. `startup_only` has no docstring at all — the asymmetry is the more concrete, verifiable problem here (not merely that both fields "are easy to conflate" in the abstract).

## Reason for Change
An operator reading `/reload` output, or a developer extending `ConfigReloadOutcome`, has no in-code explanation of what `startup_only` means or how it differs from `skipped` and `needs_restart` (a third, related field already documented by cross-reference from `skipped`'s docstring).

## Implementation Intent
Add a docstring to `startup_only` symmetric in quality to the existing `skipped` docstring, stating precisely when it is populated and how it differs from both `skipped` and `needs_restart`. Ensure the `/reload` command's output renderer labels the three fields distinctly for the operator.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`
- `docs/05_agent_07_06_cli-and-commands-hot-reload.md` — cross-reference if it documents `/reload` output fields

## Required Changes
- Add a docstring to `ConfigReloadOutcome.startup_only` explaining: populated when a field was present in the reload payload, differs from the running value, but requires a restart to take effect (as opposed to `skipped`, which is for fields ignored for reasons other than restart-required, and `needs_restart`, which is for MCP server definition changes specifically).
- Check the `/reload` command's rendering code (wherever `ConfigReloadOutcome` is formatted for display) and confirm `skipped`, `startup_only`, and `needs_restart` are each labeled distinctly rather than merged into one generic "ignored" bucket.

## Constraints
- Do not change which fields are classified into `skipped` vs. `startup_only` vs. `needs_restart` — this issue is documentation/clarity only.

## Acceptance Criteria
- [ ] `startup_only` has a docstring of equivalent clarity to `skipped`'s existing docstring.
- [ ] `/reload` output visibly distinguishes "ignored" (`skipped`), "restart required" (`startup_only`), and "server restart required" (`needs_restart`) from one another.

## Testing Expectations
- Manual review of `/reload` output text is sufficient; this is a documentation/clarity change with no behavior change, so no new automated test is required.

## Documentation Impact
If `docs/05_agent_07_06_cli-and-commands-hot-reload.md` describes `/reload` output fields, ensure it matches the clarified in-code docstrings.

## Out of Scope
- Changing which fields fall into each category.
- Any behavior change to `apply_config_dict()` or its helpers.

## Dependencies
- N/A: none.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
This is a documentation-only change to a dataclass field's docstring plus a check of the `/reload` output renderer — do not modify any logic that assigns values into `skipped`, `startup_only`, or `needs_restart`.
