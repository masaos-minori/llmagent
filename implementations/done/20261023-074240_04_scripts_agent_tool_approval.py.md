## Goal

Route `scripts/agent/tool_approval.py`'s approval prompts through a module-level owned `StdinReader` (new), and remove the now-unused `import asyncio` (used in the module only for `asyncio.to_thread`, which is `loop.run_in_executor(None, …)`) so the approval prompt is no longer a default-executor stdin read (`plans/20261022-040200_plan.md`, REQ-005, REQ-009; AC-2, AC-6, AC-8).

## Scope

Modify only `scripts/agent/tool_approval.py`: add a module-level lazily-created `StdinReader` (new), route both prompts through a private seam, and delete `import asyncio`. Keep the prompts, `"yes"`/`"y"` matching, `check_approval`'s exactly-one-prompt-per-tool-call shape (`:186`), the audit calls, and the `EOFError` propagation path unchanged.

## Assumptions

- `_prompt_user_approval` runs only during a dispatch (`tool_runner.py:409`), when no other prompt read is in flight, so a single module-level instance serves one request at a time.
- `asyncio` is used in this module solely for `asyncio.to_thread` (`:127`, `:130`); removing the import changes no other behavior. (Verified against current HEAD: the only `asyncio.` occurrences are the two `to_thread` calls.)

## Design decisions

- A single module-level `StdinReader` (new) is created lazily on first use (no eager import-time construction), since this module has no component to own an instance (`REQ-005`). A small private helper `_approval_read(prompt)` wraps `reader.read(prompt=prompt)` so the two call sites stay one-liners and the patch-target re-point in `test_tool_approval_preflight.py` has a single seam to aim at.
- `import asyncio` is removed in the same step once both `to_thread` calls are replaced.

## Alternatives considered

N/A: the Plan fixes the mechanism; this row performs the mechanical substitution and import removal.

## Implementation

### Target file

`scripts/agent/tool_approval.py`

### Procedure

1. Import `StdinReader` (new) from `scripts/agent/stdin_reader.py`.
2. Add a module-level lazily-created reader, e.g. a function-local singleton via a module global set on first call, or a small accessor that constructs one on first use.
3. In `_prompt_user_approval` (`:123-131`), replace `(await asyncio.to_thread(input, "  Execute? [yes/no]: "))` with `(await _approval_read("  Execute? [yes/no]: "))` and `(await asyncio.to_thread(input, "  Execute? [y/N]: "))` with `(await _approval_read("  Execute? [y/N]: "))`.
4. Delete `import asyncio` (`:11`).

### Method

- The prompts, `.strip().lower()` normalization, and the `answer == "yes"` / `answer == "y"` comparisons are preserved exactly.
- Confirm the import is truly unused after the change: `grep -n "to_thread\|import asyncio\|asyncio\." scripts/agent/tool_approval.py` returns nothing except any intentional comment (`AC-6`).

### Details

- Do not touch `check_approval` (`:134`), its audit calls, or the `EOFError` propagation path through `tool_runner.py:409` (`REQ-009`).
- The `from __future__ import annotations` (`:9`) stays; only the `asyncio` import line is removed.

## Compatibility considerations

No public symbol changes; `check_approval`'s signature and single-prompt-per-call shape are unchanged. See `plans/20261022-040200_plan.md` REQ-011 for the unchanged-files list.

## Security considerations

N/A: no new trust boundary or data path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_approval.py` | Regression over the whole approval suite with re-pointed patch targets, plus an `EOFError` propagation case. | `uv run pytest tests/agent/test_tool_approval_preflight.py -q` ; `grep -n "to_thread\|import asyncio" scripts/agent/tool_approval.py` ; `grep -c "asyncio.to_thread" tests/agent/test_tool_approval_preflight.py` | Approval semantics cases pass with unchanged expectations; grep returns nothing in the module; count in the test file is 0 (AC-6). |

## Completion criteria

- Neither approval prompt calls `asyncio.to_thread`; both await the module reader.
- `import asyncio` is absent from the module.
- The whole approval suite passes with the re-pointed patch targets (`AC-6`).

## Out of Scope

The primary prompt reads (`repl_input_loop.py`, row 2) and the multiline continuation read (`cli_view.py`, row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewire `scripts/agent/tool_approval.py` and remove its `asyncio` import | Completed | 20261023-135520 | 20261023-135520 | REQ-005, REQ-009; AC-2, AC-6 implemented; full suite 9831 passed; procedures corrected (reader state machine, call-time input lookup, new-markers, nonexistent doc checkers); rows 11-13 added for three further approval test files; generated reference table regenerated |
| 2 | Add or update tests per Validation plan | Completed | 20261023-135520 | 20261023-135520 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-135520 | 20261023-135520 |  |

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
- **Requirement ID**: REQ-005, REQ-009
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `scripts/agent/tool_approval.py`