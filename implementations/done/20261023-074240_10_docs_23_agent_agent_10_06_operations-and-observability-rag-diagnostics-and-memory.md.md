## Goal

Replace the claim in `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` that the remaining stdin-read executor thread "terminates upon process exit" with the reader-thread behavior this Plan changes (`plans/20261022-040200_plan.md`, REQ-010; AC-9).

## Scope

Modify only `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`: correct the final sentence of the "Graceful Shutdown" bullet that describes the stdin-read thread. No other file is modified by this row.

## Assumptions

- Line `:65`'s opening clause (the `_read_input` shutdown-event race via `asyncio.wait(FIRST_COMPLETED)`, stdin read returning `None` when the shutdown event completes first) is still accurate and stays; only the final sentence about the thread is false after this Plan.
- Every corrected sentence must describe behavior a named test asserts (`AC-9`).

## Design decisions

- Replace "The executor thread for the remaining stdin read is not interrupted and terminates upon process exit" with a statement that the prompt read now runs on one owned daemon reader thread, so an abandoned/cancelled read is not joined at interpreter exit and process exit is bounded by the shutdown path rather than by the abandoned read (asserted by `TestAbandonedReadDoesNotDelayProcessExit`).

## Alternatives considered

N/A: documentation-only; the Plan fixes the claim.

## Implementation

### Target file

`docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

### Procedure

1. In the "Graceful Shutdown" section, replace the final sentence of the "Shutdown flag set" bullet (the claim that the stdin-read executor thread "terminates upon process exit") with the daemon reader-thread behavior described above.

### Method

- Keep the accurate opening clause of the bullet (the shutdown-event race and immediate `None` return) unchanged.
- Anchor the corrected sentence to `TestAbandonedReadDoesNotDelayProcessExit`.
- Do not introduce a SIGINT/SIGTERM distinction the code does not make (`AC-9`).
- Withhold UNK-01's terminal-state wording until the interactive TTY check is done.

### Details

- The correction must not imply the abandoned read is unblocked or flushed; the daemon thread simply loses nothing at exit.

## Compatibility considerations

N/A: single-sentence correction in a runbook.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Docs structure, quality, content policy, cross-domain consistency, references, index. | `uv run python tools/check_docs_structure.py` ; `check_docs_quality.py` ; `check_docs_content_policy.py` ; `check_docs_consistency.py --domain agent` ; `check_docs_refs.py` ; `check_docs_index_completeness.py` ; `check_docs_japanese.py` | All pass; the false operational claim is gone; no untested claim survives (`AC-9`). |

## Completion criteria

- The `:65` claim no longer states that an executor thread terminates upon process exit.
- The replacement names the daemon reader-thread behavior and is anchored to a named test.
- All docs checkers exit 0.

## Out of Scope

Editing any other section of this document. Updating `agent_07_05` (that is row 9).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `:65` stdin-read executor-thread claim in `agent_10_06` | Completed | 20261023-135528 | 20261023-135528 | REQ-010; AC-9 implemented; full suite 9831 passed; procedures corrected (reader state machine, call-time input lookup, new-markers, nonexistent doc checkers); rows 11-13 added for three further approval test files; generated reference table regenerated |
| 2 | Run the docs validation sequence (`routing.md` Tools) | Completed | 20261023-135528 | 20261023-135528 |  |

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
- **Requirement ID**: REQ-010
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`