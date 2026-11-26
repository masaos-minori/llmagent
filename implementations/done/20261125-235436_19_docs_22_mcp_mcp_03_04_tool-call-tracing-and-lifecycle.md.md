## Goal

Describe the new lifecycle state machine and process-ownership rules in the MCP lifecycle doc (REQ-012).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 6)

## Assumptions
- Named by `docs/00_index.md:164` for `HttpServerLifecycleManager / http_lifecycle.py`.
- Corrected during execution (2026-11-26 adversarial verification): this file has no `LifecycleState` section; the state-machine and ownership prose was added as a new `Implementation Note (Process Ownership)` subsection after `Implementation Note (Shutdown Termination)`. The existing shutdown note carried a stale pre-change sentence ("process entry is removed before any signal is sent") and the guard paragraph claimed `ensure_ready()`/`restart()` return immediately; both were corrected against the landed row 03/04/06 behavior.

## Design decisions
- Update only the state-machine and ownership sections the new states and record contract change.

## Alternatives considered
- N/A: the docs mapping fixes the target file.

## Implementation
### Target file
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure
Add the three new states and the record-retention rule to the lifecycle description; note the typed suppression errors.

### Method
Prose update in the Lifecycle Flow section: corrected the shutdown-guard paragraph (typed suppression errors now named per method) and the shutdown-termination paragraph (removed the pre-removal sentence), and added an `Implementation Note (Process Ownership)` subsection covering the record contract, the new states, and restart refusal; kept the Keywords section.

### Details
- State the manual-cleanup semantics: retained record named by `/mcp status`, `kill -TERM -<pgid>` in the log (maintainer decision 2026-11-25).

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `rules/tool-gates.md`.

## Completion criteria
- The doc describes the new states, the ownership contract, and the suppression semantics; both doc checkers pass.

## Out of Scope
- The generated reference artifacts (rows 21-23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change | Completed | 20261126-132400 | 20261126-132345 | Guard paragraph corrected (EnsureSuppressedError/RestartSuppressedError/StartSuppressedError named); stale pre-removal sentence removed; new Implementation Note (Process Ownership) subsection added with record contract, STOPPING/EXIT_UNCONFIRMED/SIGNAL_NOT_DELIVERED, RestartBlockedError refusal |
| 3 | Run the docs checkers (`rules/tool-gates.md`) | Completed | 20261126-132700 | 20261126-132345 | `check_docs_quality.py`, `check_docs_structure.py` check_docs_quality: no issues; check_docs_structure: all checks passed |

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
- **Requirement ID**: REQ-012 (documentation of the new state machine and ownership rules)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`