## Goal

Correct the three Ctrl-C / grace-period bullets in this chapter (`:39`, `:43`, `:52`) to the contract this Plan implements (`REQ-008`; `AC-7`). Each corrected sentence states measured behavior and names the test that asserts it, and no sentence claims an unimplemented distinction between SIGINT and SIGTERM (`UNK-01`). No other section of the chapter is touched.

## Scope

Only `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`: the Ctrl-C bullet (`:39`), the Shutdown Behavior bullet (`:43`) and the Key Constraints bullet (`:52`). No other file, and no other section of this file.

## Assumptions

- The production change lands in the sibling rows first (`repl.py`, `repl_input_loop.py`), so these sentences describe the post-fix contract, not the HEAD state.
- `UNK-01`'s SIGINT/SIGTERM policy is unconfirmed; wording stays neutral and describes measured behavior only. No sentence ascribes different behavior to SIGINT vs SIGTERM.
- Every corrected sentence must map to a named test assertion (`AC-7`): prompt-wait interruption → `TestSignalDuringPromptEndsLoop`; mid-turn bound → `TestMidTurnSignalIsBounded`.

## Design decisions

- Correct, do not expand. Only the three bullets the plan targets (`:39`, `:43`, `:52`); leave the rest of the chapter byte-identical.
- Neutral signal wording. `signal_handler.py:54-63` registers one handler for both signals; no sentence treats SIGINT and SIGTERM differently (`UNK-01`; `AC-7`).
- Name the asserting test on each corrected sentence. `AC-7` requires that every Ctrl-C / grace-period sentence describe behavior a named test asserts, so the prompt-wait clause cites `TestSignalDuringPromptEndsLoop` and the mid-turn clause cites `TestMidTurnSignalIsBounded`.

## Alternatives considered

- Rewriting the whole chapter: rejected — out of scope, would touch unrelated sections (Responsibility Boundary, Keywords) and risk breaking the docs checkers.
- Keeping the SIGTERM-specific / "forced termination" wording: rejected — `AC-7` forbids an unimplemented distinction, and the code treats both signals identically.
- Leaving `:52` untouched: it is already correct for the post-fix contract, so it is retained with its test anchor noted rather than rewritten.

## Implementation
### Target file
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`

### Procedure
1. Correct the Ctrl-C bullet (`:39`): keep "during input wait, it leads to REPL termination similar to EOF"; delete the parenthetical "(handled differently from interruption during tool loop execution in current implementation)".
2. Correct the Shutdown Behavior bullet (`:43`): replace the SIGTERM / forced-termination wording with the cancel-on-shutdown + bounded-unwind contract.
3. Verify the Key Constraints bullet (`:52`): "Ctrl-C while waiting for input terminates the entire REPL rather than interrupting the current line" is now accurate after the fix; retain it and note its test anchor.

### Method
- Locate the three bullets by content, not fixed line numbers (line numbers shift by ±1 vs the plan — content-based grep, `UNK-03`): `grep -n "Ctrl-C\|Shutdown Behavior\|grace period\|_GRACEFUL_TIMEOUT_S" docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`.
- Confirm the current (pre-fix) text before editing: `:39` carries the tool-loop-distinction parenthetical, `:43` says "On SIGTERM ... awaited for a bounded grace period ... before forced termination", `:52` says "Ctrl-C while waiting for input terminates the entire REPL".
- After editing, re-run the `AC-7` docs checkers and confirm no surviving sentence claims an unimplemented SIGINT/SIGTERM distinction.

### Details
- `:39` before: "...it leads to REPL termination similar to EOF (handled differently from interruption during tool loop execution in current implementation)". after: "...it leads to REPL termination similar to EOF". The remaining clause is asserted by `TestSignalDuringPromptEndsLoop` (`AC-3`): a signal while the prompt waits ends the loop without any keyboard input.
- `:43` before: "On SIGTERM the shutdown flag and event are set, and the running turn is awaited for a bounded grace period (`_GRACEFUL_TIMEOUT_S`) before forced termination. `/exit` and the shutdown flag both end the loop (Explicit in code — `scripts/agent/repl.py`)." after: "On a signal the `shutdown_requested` flag and the shared shutdown event are set. At the prompt this ends the loop immediately; during a turn the in-flight dispatch is cancelled and the wait for that cancellation is bounded by `_GRACEFUL_TIMEOUT_S` before the loop exits. `/exit` and the shutdown flag both end the loop (Explicit in code — `scripts/agent/repl.py`)." The cancel-on-shutdown + bounded-wind clause is asserted by `TestMidTurnSignalIsBounded` (`AC-4`); the prompt-wait clause by `TestSignalDuringPromptEndsLoop` (`AC-3`).
- `:52` before/after: unchanged text "Ctrl-C while waiting for input terminates the entire REPL rather than interrupting the current line" — now accurate after `REQ-001` (it described unreachable behavior at HEAD); asserted by `TestSignalDuringPromptEndsLoop` (`AC-3`). Retain as-is.

## Compatibility considerations
`docs/00_index.md:44` and `:153` name this chapter ("CLI view / readline"), so the correction keeps the task-to-document mapping valid. `agent_13_reference-api-generated.md` is unaffected (no docstring here). `deploy/start_agent.sh:195` is re-checked, not edited; after the fix its "Ctrl+C で停止" hint is accurate against the implemented behavior.

## Security considerations
N/A: documentation-only correction. No change to signal handling, delivery, or the shutdown path itself.

## Rollback considerations
Revert the single commit; the three bullets return to their pre-correction wording exactly.

## Validation plan
- Re-run the `AC-7` docs checkers: `uv run python tools/check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_refs.py`, `check_docs_index_completeness.py`, `check_docs_japanese.py`, `check_skills_references.py` — all exit 0.
- Confirm no surviving Ctrl-C / grace-period sentence claims an unimplemented SIGINT/SIGTERM distinction (`AC-7`): grep the chapter for "SIGINT"/"SIGTERM" and confirm none ascribes different behavior.
- Confirm each corrected sentence maps to a named test: `TestSignalDuringPromptEndsLoop` (`AC-3`) for the prompt-wait clauses, `TestMidTurnSignalIsBounded` (`AC-4`) for the mid-turn bound clause.
- `git diff --stat docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` lists only this file among the doc rows.

## Completion criteria
The Ctrl-C bullet (`:39`), Shutdown Behavior bullet (`:43`) and Key Constraints bullet (`:52`) each state the post-fix contract, name the test that asserts it, and claim no unimplemented SIGINT/SIGTERM distinction; the docs checkers pass; and no other section of the chapter changed.

## Out of Scope
`docs/23_agent/agent_02_runtime-architecture.md` (its Shutdown paragraph is corrected in the sibling row), `deploy/start_agent.sh` (operator hint, re-checked not edited), and all other files — byte-identical except the rows that correct them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the Ctrl-C, Shutdown Behavior and Key Constraints bullets in `agent_07_05` | Pending | — | — | REQ-008; AC-7 |
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
- **Related target files**: `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`
