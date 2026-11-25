## Goal

Give `RuntimeToolRegistry` a policy snapshot and restore pair covering the tool mapping, the
primary-tool state, and the policy fields, so a failed commit can put the registry back to its
pre-commit state (REQ-006, service snapshot and restore; REQ-008, restart-only MCP).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `apply_policy` (`runtime_tool_registry.py:207`) replaces
  `self._tools` with a `dataclasses.replace` result, so the previous mapping must be captured before
  commit.
- UNK-02: the internal derived caches of `apply_policy` were read but not exhaustively enumerated; the
  implementation must read the class and extend `snapshot_policy` (new) to every mutated attribute, and the
  transaction test asserts no attribute differs after restore.
- The registry semantics are not redefined here: `ADR-02-02-003` keeps authority over
  `RuntimeToolRegistry`, static availability, and reload behavior.

## Design decisions
- The snapshot stores the mapping object reference and the policy fields, not a copy of each tool, so
  restore reattaches the original mapping rather than rebuilding it.
- MCP tool discovery is not made reversible: the registry change caused by an MCP definition change is
  gated before commit (OD-06), and this module only restores what `apply_policy` changed.

## Alternatives considered
- Snapshotting every tool entry — rejected: the entries are declared objects shared with the tool
  layer, and copying them would break identity.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
Add `snapshot_policy()` and `restore_policy(snapshot)` for the tool mapping, primary-tool state, and the
policy fields used by `apply_policy`.

### Method
- `snapshot_policy()` (new) returns the snapshot type defined by row 7.
- `restore_policy(snapshot)` (new) reattaches the captured mapping and restores the policy fields.
- `apply_policy` keeps its signature and behavior; only the snapshot capture is added.

### Details
- Every attribute `apply_policy` mutates must be covered; the transaction test compares the registry
  before and after a rollback attribute by attribute (UNK-02).

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
- A restore after a failed commit leaves the registry with the pre-commit tool mapping, primary-tool
  state, and policy fields, and no attribute differs from the pre-commit snapshot.

## Out of Scope
- The transaction and the reverse-order rollback (row 7).
- MCP discovery and lifecycle behavior (rows 8, 21, 22).

### Companion test files
- `tests/shared/test_runtime_tool_registry.py`
  - Procedure: assert snapshot and restore of the policy fields and the tool mapping, and assert no
    mutated attribute differs after restore.
  - Validation: `uv run pytest tests/shared/test_runtime_tool_registry.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | UNK-02 resolved by reading the class |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

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
