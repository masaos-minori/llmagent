## Goal

Add to `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` how a pending stdin read is released at shutdown and the statement that process exit is bounded by the shutdown path rather than by keyboard input (`plans/20261022-040200_plan.md`, REQ-010; AC-9).

## Scope

Modify only `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`: add a bullet to the "REPL Input/Output Model" section describing the owned daemon reader thread and that a pending/abandoned read does not hold the process open, and add a statement to the "Shutdown Behavior" section that exit time is bounded by the shutdown path. No other file is modified by this row.

## Assumptions

- The doc currently documents prompts and EOF/Ctrl-C behavior but never states how a pending read is released; the addition fills that gap.
- Every added sentence must describe behavior a named test asserts (`AC-9`).

## Design decisions

- The new "REPL Input/Output Model" bullet states the prompt read runs on one owned daemon reader thread and that cancelling or abandoning the read does not delay process exit (asserted by `TestAbandonedReadDoesNotDelayProcessExit` and `TestPromptReadDoesNotUseAnExecutor`).
- The "Shutdown Behavior" section gains a statement that process exit is bounded by the shutdown path (`_GRACEFUL_TIMEOUT_S` / forced termination), not by a keystroke arriving at an idle prompt.

## Alternatives considered

N/A: documentation-only; the Plan fixes the claims.

## Implementation

### Target file

`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`

### Procedure

1. In the "REPL Input/Output Model" section, add a bullet stating the interactive prompt is read on one owned daemon reader thread, so a read that is cancelled or left pending at loop exit does not hold the process open.
2. In the "Shutdown Behavior" section, add a statement that process exit time is bounded by the shutdown path (bounded grace period then forced termination), not by keyboard input at an idle prompt.

### Method

- Anchor each new sentence to a named test: the exit-bound claim maps to `TestAbandonedReadDoesNotDelayProcessExit`; the "does not use an executor" claim maps to `TestPromptReadDoesNotUseAnExecutor`; the prompt/EOF/Ctrl-C bullets already present stay as-is.
- Do not introduce a SIGINT/SIGTERM distinction the code does not make (`AC-9`).
- Withhold UNK-01's terminal-state wording (the unreadable question about `readline` state after an abandoned read) until the interactive TTY check is run — the doc states only what the tests measure.

### Details

- Keep the existing bullets (`:36`, `:38`, `:39`, `:44`, `:52`) unchanged; only add.
- After editing, run the docs checkers named in `routing.md`: `check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_refs.py`, `check_docs_index_completeness.py`, `check_docs_japanese.py`, `check_skills_references.py` — all must exit 0 (`AC-9`).

## Compatibility considerations

This doc is a shared Frozen target with `plans/20261022-024105_plan.md` (doc001), whose `REQ-005` substitution wording cites the prompt literals this Plan moves. Implement doc001 before this row, or re-derive the two prompt-literal sentences against `scripts/agent/stdin_reader.py`. See the Notes in `plans/20261022-040200_plan.md` (WI-01).

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` | Docs structure, quality, content policy, cross-domain consistency, references, index. | `uv run python tools/check_docs_structure.py` ; `check_docs_quality.py` ; `check_docs_content_policy.py` ; `check_docs_consistency.py --domain agent` ; `check_docs_refs.py` ; `check_docs_index_completeness.py` ; `check_docs_japanese.py` ; `check_skills_references.py` | All pass; no claim survives that no test asserts (`AC-9`). |

## Completion criteria

- The "REPL Input/Output Model" and "Shutdown Behavior" sections each contain the new statements, each anchored to a named test.
- No untested claim and no SIGINT/SIGTERM distinction remains.
- All docs checkers exit 0.

## Out of Scope

Correcting the `:65` claim in `agent_10_06` (that is row 10). Rewriting the existing prompt/EOF/Ctrl-C bullets.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `agent_07_05` input-model and shutdown text | In Progress | 20261023-074240 | — | REQ-010; AC-9 |
| 2 | Run the docs validation sequence (`routing.md` Tools) | Pending | — | — | |

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
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`
