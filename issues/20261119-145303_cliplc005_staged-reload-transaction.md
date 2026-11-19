# Rebuild configuration parsing and /reload as a typed, staged, rollback-capable transaction

## Priority
High

## Summary
Use one strict parser at startup and reload, keep startup-only values out of live state, stage all service changes with rollback on commit failure, and treat every MCP server-definition change as restart-required.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 5). Related archived work that must be re-verified first: `issues/done/20261026-224903_config001_make-config-reload-atomic.md`, `plans/done/20261027-073638_config001_make-config-reload-atomic.md`, and `plans/done/20261119-094759_adrchk004_hot-reload-validation.md` (validated approval and allowed-tool fields on `/reload`).

Evidence (`Explicit in code`, by reading): `scripts/agent/services/config_section_reload.py` documents a prepare half (candidate build and validators, no live mutation) and an apply half (`setattr`, lines 84 and 158), so part of the staging in the backlog may already exist; `scripts/agent/services/config_reload.py` converts requests with `list(...)` and applies service updates through `setattr` (lines 116-141). The claims about startup-only fields written to live state, Memory and MCP direct sections bypassing validators, missing rollback across LLM, HistoryManager, RuntimeToolRegistry, and MCP resources, removed-server live cleanup, and outcome states are from the backlog and `Needs confirmation`.

## Problem
Fields marked startup-only may already be written to live configuration; Memory and MCP sections may skip typed candidate construction; coercive parsing can accept malformed values; commit mutates several live objects sequentially without rollback; removed MCP servers may be cleaned up live without terminating their processes; outcomes cannot express prepared, committed, rolled-back, or degraded states.

## Reason for Change
Correctness of the configuration transaction; the MCP launch, health, and cleanup issues depend on a strict configuration model.

## Implementation Intent
Startup and reload use identical typed validation. Startup-only changes stay pending until restart. Every reloadable service prepares before any commit and rolls back in reverse order on failure. Added, changed, and removed MCP server definitions stay pending restart and do not touch live lifecycle or registry state.

## Target Files or Areas
- `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`
- `scripts/agent/services/config_reload.py`, `config_section_reload.py`, `config_field_registry.py`, `config_validators.py`, `config_service_sync.py`, `config_outcome_classification.py`
- `scripts/shared/runtime_tool_registry.py`; LLM, HistoryManager, and registry apply paths (`scripts/agent/production_config_validator.py` exists; the LLM and HistoryManager `apply_config()` code is `不明` until located)
- Reload tests under `tests/agent/`; `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`

## Required Changes
- One typed parser for startup and reload: `cmd` a non-empty list or tuple of non-empty strings, `env` a `mapping[str, str]`, strict booleans, no booleans for numbers, URL and role types, unknown-field rejection, existing Memory validators connected, typed candidate objects instead of direct `setattr()`, stable field-level errors without raw values.
- Filter non-hot-reloadable fields during candidate preparation, keep them out of `ctx.cfg` and service sync, report them as pending restart only.
- Snapshot old config, conversation state, and service settings; add prepare APIs to live services; commit only after every prepare succeeds; roll back applied services in reverse order; move irreversible cleanup to the final stage; add outcomes `prepared`, `committed`, `rolled_back`, `degraded`; redact commit and rollback errors.
- Classify added, changed, and removed MCP servers as `needs_restart`; do not call live cleanup from reload; do not mutate live MCP config or RuntimeToolRegistry; show pending changes in `/mcp status`; rebuild lifecycle, discovery, posture, and registry after restart.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate that approval.
- Stricter parsing changes accepted inputs; list the newly rejected inputs.

## Acceptance Criteria
- [ ] Startup and reload accept and reject identical values.
- [ ] Startup-only changes leave every live object unchanged.
- [ ] Any commit failure restores all reversible services.
- [ ] A removed-server reload cannot orphan a process; RuntimeToolRegistry changes only after restart and rediscovery.
- [ ] The CLI outcome matches the actual live state.

## Testing Expectations
- Startup-only fields across LLM, context, approval, Memory, and GitOps; invalid Memory and MCP types and ranges.
- Service prepare, commit, rollback, and cleanup failures; added, changed, and removed MCP definitions; pending-restart status display.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Startup-only versus hot-reload behavior; transactional reload outcomes; MCP server-definition changes require restart.

## Out of Scope
- Launch security and credentials (`issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`); MCP health and capability state (`issues/20261119-145306_cliplc008_mcp-health-capability.md`).

## Dependencies
- No dependency; can start immediately in parallel with `issues/20261119-145259_cliplc001_repl-input-controller.md` through `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`. Blocks `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`, `issues/20261119-145306_cliplc008_mcp-health-capability.md`, and `issues/20261119-145311_cliplc013_api-field-cleanup.md`.

## Unresolved Questions
- `不明`: which of the listed defects the archived config001 and adrchk004 work already fixed.
- `不明`: whether LLM, HistoryManager, and RuntimeToolRegistry expose reversible apply operations.

## AI Implementation Instruction
First re-verify each reported defect with a test against current source, since related fixes exist. Keep the change within configuration and reload code. Do not write ADR approval statements. Stop and report if a live service cannot be made reversible.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145303
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`, `scripts/agent/services/config_reload.py`, `scripts/agent/services/config_section_reload.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_service_sync.py`, `scripts/agent/services/config_outcome_classification.py`, `scripts/shared/runtime_tool_registry.py`
