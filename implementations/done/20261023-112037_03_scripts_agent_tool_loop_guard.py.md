## Goal

Correct `ToolLoopGuard`'s class docstring so it states that each instance owns its
empty-result counts per turn, removing the "Stateless per-instance" claim that made the
never-filled counter look harmless (`REQ-006`, `AC-5`).

## Scope

Only the class docstring of `scripts/agent/tool_loop_guard.py`. The text at `:88-89`
currently reads "Stateless per-instance; all mutable state lives in `TurnLoopState`", which
contradicts `self._empty_result_counts` declared at `:107`. Rewrite those lines only. No code,
signature, threshold, or behavior changes.

## Assumptions

- The counts live in `self._empty_result_counts: dict[str, int]` (`:107`), one instance per
  LLM turn (`handle_llm_turn`, `scripts/agent/llm_turn_executor.py:83`).
- The startup self-report (`_STARTUP_REPORTED`, `:36`, `:96-123`) and the option gating
  (`record_tool_result` early return `:159-160`) are unaffected by a docstring rewrite.

## Design decisions

- **State per-instance, per-turn ownership** of `_empty_result_counts`, matching the field
  declaration at `:107` and the constructor. Do not mention `TurnLoopState`, which owns
  nothing about empty-result counts.

## Alternatives considered

- Editing any method body — rejected by `REQ-006`/`REQ-005`: only the docstring is wrong; the
  gating and consumer at `:159-189` must stay byte-for-byte.

## Implementation

### Target file

`scripts/agent/tool_loop_guard.py`

### Procedure

Replace the two docstring lines at `:88-89` with a statement that the instance holds its
`_empty_result_counts` per turn (created in `__init__`), and that mutable empty-result state
lives on the per-instance guard, not on `TurnLoopState`.

### Method

Locate the class body at `:85`, read the current `:88-89` text, and reword those sentences.
Leave everything from `:90` onward untouched.

### Details

- Keep the docstring present-tense and evidence-grounded: name the field (`_empty_result_counts`)
  and its per-turn lifetime. Do not introduce thresholds, reset semantics, or per-tool-name
  rules (`tool003`/`tool004`).

## Compatibility considerations

### Corrections found while implementing

- Class docstring rewritten: one instance per LLM turn owns `_empty_result_counts`, filled by `record_tool_result`; the other per-turn state stays in `TurnLoopState`. No code change.


- N/A: docstring-only; no signature or runtime change. The generated API table (row 8) is
  unaffected by a docstring edit.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit; one-line docstring change.

## Validation plan

- `uv run python tools/check_docstrings.py` passes (docstring still valid, no stale claim).
- `uv run ruff check scripts/agent/tool_loop_guard.py`.
- `uv run pytest tests/agent/test_tool_loop_guard.py -q` — the 34-test suite is unchanged and
  green; none of its assertions are edited.

## Completion criteria

The class docstring no longer claims "Stateless per-instance"; it states per-instance,
per-turn ownership of `_empty_result_counts`; `check_docstrings.py` is green; the 34 tests
pass unedited.

## Out of Scope

- Any behavior, signature, threshold, or state change in `tool_loop_guard.py`.
- The parameter threading and recording in `scripts/agent/tool_runner.py` (row 1).
- Test migrations (rows 4-7) and reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the class docstring at :88-89 to state per-instance/per-turn ownership | Completed | 20261023-163751 | 20261023-163751 | REQ-006; docstring-only, no code change implemented; full suite 9909 passed |
| 2 | Run documentation checkers (`rules/toolchain.md`) | Completed | 20261023-163751 | 20261023-163751 | check_docstrings.py green; 34 tests unedited |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `scripts/agent/tool_loop_guard.py`