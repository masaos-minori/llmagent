## Goal

Give `RuntimeToolRegistry` a policy snapshot and restore pair covering the tool mapping that
`apply_policy` replaces, so a failed commit can put the registry back to its pre-commit state
(REQ-006, service snapshot and restore; REQ-008, restart-only MCP).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `apply_policy` (`runtime_tool_registry.py:207`) replaces
  `self._tools` with a `dataclasses.replace` result, so the previous mapping must be captured before
  commit.
- UNK-02 is resolved by this verification pass: `apply_policy` mutates exactly one attribute,
  `self._tools` (`runtime_tool_registry.py:247`), and the policy inputs (`allowed_tools`,
  `tool_policy_mode`, `disabled_tools`) are call arguments, not stored state. There is no primary-tool
  state in the module. `snapshot_policy` (new) therefore captures `self._tools` only; the transaction
  test still compares the registry attribute by attribute after restore.
- The registry semantics are not redefined here: `ADR-02-02-003` keeps authority over
  `RuntimeToolRegistry`, static availability, and reload behavior.

## Design decisions
- The snapshot stores the `self._tools` mapping object reference, not a copy of each tool, so restore
  reattaches the original mapping — including the original `RuntimeTool` objects that `apply_policy`
  replaced with `dataclasses.replace` copies — rather than rebuilding it.
- MCP tool discovery is not made reversible: the registry change caused by an MCP definition change is
  gated before commit (OD-06), and this module only restores what `apply_policy` changed.

## Alternatives considered
- Snapshotting every tool entry — rejected: the entries are declared objects shared with the tool
  layer, and copying them would break identity.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
Add `snapshot_policy()` and `restore_policy(snapshot)` for the tool mapping `apply_policy` replaces.

### Method
- `snapshot_policy()` (new) returns the snapshot type defined by row 7.
- `restore_policy(snapshot)` (new) reattaches the captured mapping.
- `apply_policy` keeps its signature and behavior; only the snapshot capture is added.

### Details
- `self._tools` is the only attribute `apply_policy` mutates; the transaction test still compares the
  registry before and after a rollback attribute by attribute (UNK-02, resolved above).

## Compatibility considerations
- Blast radius: the registry is the tool routing authority for the agent and the HTTP layers; restore
  must not change tool availability beyond what `apply_policy` had changed.

## Security considerations
- No configuration value appears in the snapshot's reporting text.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py -q`
- `uv run pytest tests/agent/services/test_config_reload_transaction.py -q` (row 26)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A restore after a failed commit leaves the registry with the pre-commit `self._tools` mapping, and no
  attribute differs from the pre-commit snapshot.

## Out of Scope
- The transaction and the reverse-order rollback (row 7).
- MCP discovery and lifecycle behavior (rows 8, 21, 22).

### Companion test files
- `tests/shared/test_runtime_tool_registry.py`
  - Procedure: assert snapshot and restore of the tool mapping, including that the original
    `RuntimeTool` objects are reattached, and assert no mutated attribute differs after restore.
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194130 | 20261125-194130 | UNK-02 resolved by reading the class R4-transaction-and-restore 20261125: implemented as recorded in this procedure's Blocker Log |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194130 | 20261125-194130 | companion test file R4 20261125: targeted run tests/agent/services tests/agent/commands tests/shared tests/agent/test_history_manager.py = 2821 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194130 | 20261125-194130 | R4 gate 20261125: full suite 14722 passed 5 skipped, diff-cover 100 percent over 482 lines, integration 146 passed 1 skipped, mypy 466 files clean, lint-imports 6 kept, ruff format and check clean, check_module_size OK, generate_reference_table --check no drift, check_docs_structure OK |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R4 execution (2026-11-25): `snapshot_policy` captures the tool mapping `apply_policy` replaces and `restore_policy` reattaches the original `RuntimeTool` objects, so a restore changes nothing beyond the mapping — the policy inputs are call arguments, not stored registry state. Registry availability and `diagnostics()` are untouched, which is what REQ-008 (INV-05, INV-09) requires. `UndoToken` comes from `scripts/shared/config_undo.py` | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (service snapshot and restore), REQ-008 (restart-only MCP); AC-3, AC-4
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `tests/shared/test_runtime_tool_registry.py`