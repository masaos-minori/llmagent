## Goal

Update the protocol contract docstrings for suppression errors, per-server outcome states, and record retention semantics (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 4 is in R3-ownership, but this row is docstring-only)

## Assumptions
- The error names are declared by row 08; this document only cites them in docstrings.

## Design decisions
- Docstring-only change: no signature changes; the protocol is the shared contract callers code against.

## Alternatives considered
- N/A: no behavioral alternative for a docstring row.

## Implementation
### Target file
`scripts/agent/lifecycle_protocol.py`

### Procedure
Extend the `ensure_ready` (`:35`), `shutdown_all` (`:39`), `restart` (`:57`), and `get_transport_state` (`:65`) docstrings to state the suppression-error raises, the per-server outcome states, and record retention until confirmed exit.

### Method
One-line docstring additions naming `EnsureSuppressedError` (new), `RestartSuppressedError` (new), `RestartBlockedError` (new), and the `EXIT_UNCONFIRMED`/`SIGNAL_NOT_DELIVERED` states (new, row 01).

### Details
- Keep the existing summary sentences; add the raise and retention semantics as the contract callers must observe (AC-4).

## Compatibility considerations
- N/A: docstrings only; `generate_reference_table.py` picks up the text in the regenerate rows (19-23).

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py` (the suppression tests in row 11 exercise the contract); `uv run python tools/check_docs_quality.py` is not applicable — this is source, not `docs/`.

## Completion criteria
- The protocol docstrings state suppression raises, per-server outcome states, and retention-until-confirmed; the suite stays green.

## Out of Scope
- The error class definitions (row 08), the router behavior (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docstring-only row: ruff/mypy plus the protocol tests |

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
- **Requirement ID**: REQ-008 (typed suppression errors in the shared contract)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/lifecycle_protocol.py`
