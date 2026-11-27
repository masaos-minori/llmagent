## Goal

Qualify the absolute Ctrl-C statement so it matches the configured force-exit opt-in stated earlier in the same
document (REQ-002; AC-2).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: line 57 states "Ctrl-C never ends the REPL by itself", while line 39 of the same file states
  that the process exits through the force-exit path only when `shutdown_force_exit_on_second_sigint` is true
  (`scripts/agent/signal_handler.py:102-138`).
- `tests/agent/test_signal_handler.py` proves both halves: `TestInterruptByState` (state-dependent behavior) and
  `test_configured_force_exit_is_read_once_at_construction` (the configured opt-in).
- `tests/agent/test_signal_handler.py` is a validation reference, not a modification target: it is not a row of the
  Plan's target table.

## Design decisions

- The correction adds the exception to the absolute claim rather than rewriting line 39, so the document keeps one
  authoritative statement of the interrupt contract with a single qualified exception.

## Alternatives considered

- Removing the exception clause from line 39 — rejected: the force-exit path is implemented and test-proven, so the
  absolute claim is the incorrect half.

## Implementation
### Target file
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`
### Procedure

- Rewrite line 57 so the absolute claim carries the `shutdown_force_exit_on_second_sigint` exception already stated at
  line 39.

### Method

- Sentence-level edit; no code path is touched.

### Details

- Keep the state-by-state enumeration (prompt, turn, maintenance job, shutdown step) and the `TestInterruptByState`
  citation unchanged; only the absolute wording is qualified.

## Compatibility considerations

- No runtime behavior changes; the docs gates and the named test are the only checks affected.

## Security considerations

- N/A: documentation-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_signal_handler.py`: passes; the corrected statement matches
  `TestInterruptByState` and `test_configured_force_exit_is_read_once_at_construction`.
- Docs gate — `uv run python tools/check_docs_consistency.py --domain agent`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The file states the interrupt contract without internal contradiction, the corrected statement is provable by the
  named test, and the docs gate reports no finding.

## Out of Scope

- Any change to the interrupt or force-exit implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Qualify the statement per Procedure/Method/Details | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 2 Plan Phase 2 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 7 Plan Phase 7 |

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
- **Requirement ID**: `REQ-002` (interrupt contract stated without internal contradiction)
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-223853_cliplc014_cli-docs-consolidation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-001124
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`