## Goal

Move startup-only classification before any mutation and return structured pending records instead of
display strings, so the CLI reports a startup-only change as pending rather than applied (REQ-003,
pre-mutation classification; REQ-008, structured MCP pending records).

## Scope
**Release unit**: R3-shared-candidate

## Assumptions
- Verified against current source: `classify_startup_only_fields` (`config_outcome_classification.py:48`)
  runs after the mutation and compares against the already-updated config, so it returns an empty
  list; `classify_mcp_server_changes` (`config_outcome_classification.py:25`) returns display strings.
- The pending records it produces are stored by `PendingConfigState` (row 8); this module does not own
  the pending state.
- `detect_diagnostics_live_fields` (`config_outcome_classification.py:68`) is unchanged: those fields
  are read from disk on every save and are genuinely live.

## Design decisions
- The classifier takes the candidate and the live section and compares them before any mutation, which
  is what makes the report truthful.
- The pending reason is part of the returned record, so the display layer does not re-derive it.

## Alternatives considered
- Keeping the post-mutation comparison and renaming the report field — rejected: it enforces nothing
  (OD-02).

## Implementation
### Target file
`scripts/agent/services/config_outcome_classification.py`

### Procedure
Make `classify_startup_only_fields` compare the candidate payload against live values before any
mutation and return the fields with their pending reason; make `classify_mcp_server_changes` return
structured pending records.

### Method
- Both functions return the record shape `PendingConfigState` (row 8) stores.
- `_diff_mcp_server_config` (`config_outcome_classification.py:16`) keeps its field-diff behavior and
  returns field paths instead of formatted strings.

### Details
- The returned pending reason distinguishes "startup-only" from "restart-required MCP definition",
  because the CLI prints them under different headings.

## Compatibility considerations
- `tests/agent/services/test_config_reload_classification.py` asserts the current display strings and
  the post-mutation comparison; it is retargeted by this document's companion.

## Security considerations
- Records name fields and keys, never values.

## Rollback considerations
- Revert the Phase 3 commit; the classifier is stateless.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_classification.py tests/agent/services/test_config_reload_transaction.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A startup-only payload produces pending records against an unmutated live config, and the MCP
  classifier returns records that the pending state and the display layer read without re-parsing.

## Out of Scope
- The pending-state storage (row 8) and the CLI display (rows 20, 21).

### Companion test files
- `tests/agent/services/test_config_reload_classification.py`
  - Procedure: assert startup-only classification against an unmutated live config and assert the MCP
    classifier returns structured pending records instead of display strings.
  - Validation: `uv run pytest tests/agent/services/test_config_reload_classification.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-008 (restart-only MCP); AC-2, AC-4
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_outcome_classification.py`, `tests/agent/services/test_config_reload_classification.py`
