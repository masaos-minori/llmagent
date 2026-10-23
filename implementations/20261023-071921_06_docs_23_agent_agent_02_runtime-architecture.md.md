## Goal

Correct the Shutdown constraint paragraph (`:163-165`) in this chapter to the contract this Plan implements (`REQ-008`; `AC-7`). Replace the pre-fix wording ("terminates after the next turn completion", "deferring termination to the post-turn check") with the post-fix shape: a signal sets the flag and the shared event, ends the loop at the prompt, and during a turn cancels the in-flight dispatch with a bounded unwind. Each sentence states measured behavior and names the test that asserts it.

## Scope

Only `docs/23_agent/agent_02_runtime-architecture.md`: the Shutdown constraint paragraph (`:163-165`). No other section of the chapter is touched.

## Assumptions

- The production change lands in the sibling rows first (`repl.py`, `repl_input_loop.py`), so these sentences describe the post-fix contract, not the HEAD state.
- `UNK-01`'s SIGINT/SIGTERM policy is unconfirmed; wording stays neutral and describes measured behavior only. No sentence ascribes different behavior to SIGINT vs SIGTERM.
- Every corrected sentence must map to a named test assertion (`AC-7`): prompt-wait interruption → `TestSignalDuringPromptEndsLoop`; mid-turn bound → `TestMidTurnSignalIsBounded`.

## Design decisions

- Correct, do not expand. Only the Shutdown paragraph (`:163-165`); leave the rest of the chapter byte-identical.
- Neutral signal wording. `signal_handler.py:54-63` registers one handler for both signals; no sentence treats SIGINT and SIGTERM differently (`UNK-01`; `AC-7`).
- Name the asserting test on each corrected sentence. `AC-7` requires that every grace-period sentence describe behavior a named test asserts, so the prompt-wait clause cites `TestSignalDuringPromptEndsLoop` and the mid-turn clause cites `TestMidTurnSignalIsBounded`.
- Keep the resource-closing sentence (`:167`) untouched — it is unrelated to the signal contract and outside this row's change.

## Alternatives considered

- Rewriting the whole Key Constraints section: rejected — out of scope, would touch Startup Validation Pipeline and Lifecycle Implementation.
- Keeping "deferring termination to the post-turn check": rejected — that is the pre-fix mechanism this Plan replaces; after the fix a signal during a turn cancels the dispatch rather than deferring to the post-turn check.
- Keeping the SIGTERM-specific wording: rejected — `AC-7` forbids an unimplemented distinction, and the code treats both signals identically.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Replace the two sentences of the Shutdown paragraph (`:163`) that describe the pre-fix shape ("the loop terminates after the next turn completion", "There is a bounded grace period before timeout") with the cancel-on-shutdown + bounded-unwind contract.
2. Replace the rationale paragraph (`:165`) that states "deferring termination to the post-turn check" with the post-fix rationale (bound prevents an indefinite hang, not a direct system exit).

### Method
- Locate the paragraph by content, not fixed line numbers (line numbers shift by ±1 vs the plan — content-based grep, `UNK-03`): `grep -n "Graceful shutdown is controlled via flags\|post-turn check\|bounded grace period" docs/23_agent/agent_02_runtime-architecture.md`.
- Confirm the current (pre-fix) text before editing: `:163` says "the loop terminates after the next turn completion. There is a bounded grace period before timeout.", `:165` says "Handlers do not block, instead deferring termination to the post-turn check."
- After editing, re-run the `AC-7` docs checkers and confirm no surviving sentence claims an unimplemented SIGINT/SIGTERM distinction.

### Details
- `:163` before: "Graceful shutdown is controlled via flags. Upon receiving `SIGTERM`, the `shutdown_requested` flag is set, and the loop terminates after the next turn completion. There is a bounded grace period before timeout." after: "Graceful shutdown is controlled via flags. On a signal, the `shutdown_requested` flag and the shared shutdown event are set. At the prompt this ends the loop immediately; during a turn the in-flight dispatch is cancelled and the wait for that cancellation is bounded by `_GRACEFUL_TIMEOUT_S` before the loop exits." The cancel-on-shutdown + bounded-wind clause is asserted by `TestMidTurnSignalIsBounded` (`AC-4`); the prompt-wait clause by `TestSignalDuringPromptEndsLoop` (`AC-3`).
- `:165` before: "This approach was chosen to ensure the integrity of ongoing workflows rather than performing a direct system exit. Handlers do not block, instead deferring termination to the post-turn check." after: "The bound keeps a slow or non-cooperative turn from hanging the loop indefinitely, rather than performing a direct system exit. Handlers do not block; the loop stops waiting for the cancelled dispatch once the bound elapses."

## Compatibility considerations
`docs/00_index.md:147` names this chapter ("AgentREPL class structure"), so the correction keeps the task-to-document mapping valid. The resource-closing sentence (`:167`) and the Startup Validation Pipeline (`:169-171`) are left byte-identical.

## Security considerations
N/A: documentation-only correction. No change to signal handling, delivery, or the shutdown path itself.

## Rollback considerations
Revert the single commit; the Shutdown paragraph returns to its pre-correction wording exactly.

## Validation plan
- Re-run the `AC-7` docs checkers: `uv run python tools/check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_refs.py`, `check_docs_index_completeness.py`, `check_docs_japanese.py`, `check_skills_references.py` — all exit 0.
- Confirm no surviving grace-period sentence claims an unimplemented SIGINT/SIGTERM distinction (`AC-7`): grep the chapter for "SIGINT"/"SIGTERM" and confirm none ascribes different behavior.
- Confirm each corrected sentence maps to a named test: `TestSignalDuringPromptEndsLoop` (`AC-3`) for the prompt-wait clause, `TestMidTurnSignalIsBounded` (`AC-4`) for the mid-turn bound clause.
- `git diff --stat docs/23_agent/agent_02_runtime-architecture.md` lists only this file among the doc rows.

## Completion criteria
The Shutdown constraint paragraph (`:163-165`) states the post-fix contract, names the test that asserts it, and claims no unimplemented SIGINT/SIGTERM distinction; the docs checkers pass; and no other section of the chapter changed.

## Out of Scope
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` (its Ctrl-C bullets are corrected in the sibling row), `deploy/start_agent.sh` (operator hint, re-checked not edited), and all other files — byte-identical except the rows that correct them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the Shutdown constraint paragraph in `agent_02_runtime-architecture.md` | Pending | — | — | REQ-008; AC-7 |
| 2 | Add or update tests per Validation plan | N/A | — | — | Tests live in the `tests/agent/test_repl.py` row (AC-3, AC-4) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs checkers in AC-7 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In scope | — | — | This row is the documentation edit |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-030840_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-071921
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
