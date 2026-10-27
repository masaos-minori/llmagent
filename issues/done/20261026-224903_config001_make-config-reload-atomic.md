# Make config reload apply all-or-nothing to the live context

## Priority
Medium

## Summary
`/config reload` can leave the live `ctx.cfg` partially updated (new direct fields
and some sections applied) while live services keep their stale configuration,
because validation failure happens after earlier parts have already been applied.
Make the reload all-or-nothing.

## Background
From a python-code-review pass over the REPL command path (finding F-005).
Evidence (Explicit in code):
- `scripts/agent/services/config_reload.py` applies direct fields onto the live
  `ctx.cfg` before `_reload_sections` runs cross-section validation.
- `scripts/agent/services/config_section_reload.py` validates and `setattr`s each
  section onto `ctx.cfg` sequentially; a later invalid section raises mid-loop.
- `scripts/agent/commands/cmd_config.py` calls service re-sync only when the whole
  reload succeeds.

## Problem
When one section fails validation, the process ends up with a mix of new and old
config: updated direct fields and early sections in `ctx.cfg`, later sections old,
and services (circuit breaker, context manager, memory config) not re-synced at
all. Runtime behavior becomes ambiguous until restart.

## Reason for Change
Ambiguous live configuration is a maintenance and debugging hazard: after a failed
reload, neither the operator nor a coding agent can reason about which settings are
active.

## Implementation Intent
Two-phase reload: validate the fully assembled new config (all sections plus direct
fields, including cross-section validators) against the candidate object first;
only after all validation passes, apply it to the live context and re-sync
services. Keep the existing per-field/per-section validation registry as the
validation source; the change is the ordering, not the rules.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (apply order)
- `scripts/agent/services/config_section_reload.py` (per-section apply loop)
- `scripts/agent/commands/cmd_config.py` (service re-sync gating)

## Required Changes
- Reorder reload: build and validate a complete candidate config before mutating
  `ctx.cfg`.
- On any validation failure, leave `ctx.cfg` untouched and report the failing
  section/field.
- Keep service re-sync tied to the successful whole-config apply.
- Add a regression test for the partial-apply scenario.

## Constraints
- Keep error reporting at least as specific as today (which section/field failed).
- Do not weaken any existing validator or cross-section check.
- Reload must remain fast enough for interactive use (single config read).

## Acceptance Criteria
- A config file with one invalid section leaves `ctx.cfg` byte-for-byte unchanged
  and services not re-synced (test).
- A fully valid reload still updates all sections, direct fields, and services.
- Existing config reload tests pass or are updated with explicit justification.

## Testing Expectations
- Regression test: mixed valid/invalid sections → live config unchanged, actionable
  error message.
- Test for direct-field + section interaction (previously applied direct fields must
  also roll back on later failure).

## Documentation Impact
Update the config reload docs to state the all-or-nothing guarantee and the failure
behavior (no partial application).

## Out of Scope
- Hot-reload of fields that are intentionally startup-only.
- Config file format changes.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Reorder validation and application only; do not add new validators and do not
change the field registry semantics. If a validator currently depends on the live
`ctx.cfg` being partially updated (cross-section comparison), extract the needed
values from the candidate config instead of mutating the live one. Keep the public
`reload_config` signature stable.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224903
- **Related target files**: `scripts/agent/services/config_reload.py`, `scripts/agent/services/config_section_reload.py`, `scripts/agent/commands/cmd_config.py`
