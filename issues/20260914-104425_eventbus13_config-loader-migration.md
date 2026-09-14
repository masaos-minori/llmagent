# Migrate EventBus configuration loading to ConfigLoader

## Priority
High

## Summary
`scripts/eventbus/config.py` reads its TOML configuration directly via `tomllib.load()` rather than through the shared `ConfigLoader`, bypassing the process-level configuration isolation established by `ADR-002`; this issue migrates EventBus to `ConfigLoader` without weakening its existing fail-closed validation.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `CI-001` ("EventBus process reads configuration directly instead of using ConfigLoader") already tracks this exact gap (Status: open, Severity: High). This issue is the implementation-tracking counterpart to that Known Issue entry.

## Problem
Confirmed by direct inspection: `scripts/eventbus/config.py` imports `tomllib` and calls `tomllib.load()` directly; it does not import or use `scripts/shared/config_loader.py`'s `ConfigLoader`. This means EventBus's configuration loading path differs from every other process in the system, and does not benefit from `ConfigLoader`'s process-level file-access restriction (`restrict_to()`) or its shared validation/exception contract.

## Reason for Change
ADR-002 requires that all processes load configuration via ConfigLoader to ensure process-level config isolation. EventBus reads its own TOML configuration directly without going through ConfigLoader, violating this invariant.

## Implementation Intent
Refactor EventBus's configuration loading to use `ConfigLoader`, preserving all of EventBus's current fail-closed validation behavior (cross-field checks, required-token checks, etc. — see `eventbus09`) rather than replacing it with `ConfigLoader`'s defaults.

## Target Files or Areas
- `scripts/eventbus/config.py`
- `scripts/shared/config_loader.py`
- `tests/eventbus/test_eventbus_config.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Replace `scripts/eventbus/config.py`'s direct `tomllib.load()` call with `ConfigLoader`-based loading.
- Preserve EventBus's existing validation behavior (required keys, type checks, cross-field rules) after the migration — do not silently relax any existing check.
- Confirm `ConfigLoader.restrict_to()` is initialized appropriately for the EventBus process before production config loading (coordinate with `mcpagent07` if both are implemented in the same session, since that issue also touches `restrict_to()` initialization requirements).
- Add or update tests confirming EventBus configuration loads correctly through `ConfigLoader` and that all existing validation error cases still produce the same errors.
- Update `CI-001` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect the migration once implemented and verified — remove it from the active inventory per that document's own removal policy.

## Constraints
Must not weaken any existing EventBus configuration validation while migrating the loading mechanism — this is a mechanism change, not a validation-policy change.

## Acceptance Criteria
- `scripts/eventbus/config.py` loads its configuration via `ConfigLoader`, not `tomllib.load()` directly.
- Every existing EventBus configuration validation error case still produces an equivalent error after migration.
- EventBus configuration loading is now covered by the same process-isolation guarantee (`restrict_to()`) as other processes, or the exception is explicitly documented in `ADR-002` if EventBus cannot use it for a confirmed technical reason.
- `CI-001` is removed from the active Known Issues inventory once the migration is verified by tests.

## Testing Expectations
Add or update unit and integration tests confirming the migrated loading path behaves equivalently to the current direct-`tomllib` path for all currently-tested configuration scenarios (missing keys, wrong types, invalid combinations). Run the relevant test suite, static analysis, and type checks.

## Documentation Impact
Update `CI-001`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` — either remove it (if fully migrated) or rewrite it to describe a documented, ADR-002-recorded exception — only after the migration is implemented and verified by tests.

## Out of Scope
- Changing EventBus's actual validation policy or supported configuration keys — this issue only changes the loading mechanism.
- Unrelated refactoring outside the config-loading boundary.

## Dependencies
Coordinates with `mcpagent07` (config isolation/schema validation loader contracts) on `ConfigLoader.restrict_to()`'s initialization requirement, and with `eventbus09` (config validation/role-token policy), which this issue must not regress. Also referenced by `eventbus10` (ADR/known-issue reconciliation), which depends on this issue's outcome to update `ADR-002`/`CI-001`.

## Unresolved Questions
Whether EventBus has a genuine technical reason to diverge from `ConfigLoader` (e.g. a startup-ordering constraint) that would justify a documented ADR-002 exception instead of full migration — resolve during implementation by attempting the migration first, per this issue's own Required Changes.

## AI Implementation Instruction
Keep changes scoped to the configuration-loading mechanism; do not change EventBus's validation policy or add/remove configuration keys as part of this issue. Coordinate with `mcpagent07` if implemented in the same session. Only update or remove `CI-001` after the migration is verified by a passing test suite — do not mark it resolved based on code inspection alone.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-104425
- **Related target files**: scripts/eventbus/config.py, scripts/shared/config_loader.py, tests/eventbus/test_eventbus_config.py, docs/00_governance_03_issue-and-uncertainty-management.md
