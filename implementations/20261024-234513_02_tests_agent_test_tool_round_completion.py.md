# Implementation Procedure: tests/agent/test_tool_round_completion.py

## Goal

Create the missing unit regression file for `scripts/agent/tool_round_completion.py`: direct tests of
the positional merge helper that fail before the production change and lock the fixed behavior after
it (`REQ-007` regression and characterization coverage with a mutation check; `AC-1`..`AC-4`, `AC-7`).

## Scope

- New file `tests/agent/test_tool_round_completion.py` (new) with the helper-level cases
  `T-2`..`T-5` and the `T-6` mutation-check note.
- The full-round integration case (`T-1`) is not here — it lives in `tests/agent/test_tool_runner.py`
  (procedure doc `20261024-234513_03`) because it needs that file's `execute_all_tool_calls()` harness.

## Assumptions

- The helper under test is `_merge_in_declared_order()` (new), a pure function over
  `(tool_calls, results)`; its signature is fixed by procedure doc `20261024-234513_01`.
- Result tuples use the existing shapes: `_PrepFailure` 6-tuples
  `(call_id, name, args, full_text, is_error, llm_text)` and `RoundState.collected` value tuples —
  only position `0` (the `tool_call_id`) matters to the merge.

## Design decisions

- Test the helper directly (no `ctx`, no `asyncio`, no mocks): the Plan `Tests` split records the
  helper as pure, so these cases carry no fixture machinery and cannot drift with the runner harness.
- Expected orders are hard-coded from the Plan `Revalidation record` probes (CASE A-E), not derived
  from the implementation.

## Alternatives considered

N/A: the new file's content is fixed by the Plan `Tests` section (`T-2`..`T-6`).

## Implementation

### Target file

`tests/agent/test_tool_round_completion.py` (new)

### Procedure

One test class with the five cases below plus a module docstring carrying the `T-6` mutation note.
Import: `from agent.tool_round_completion import _merge_in_declared_order` (mirrors how
`tests/agent/test_tool_runner.py` imports `agent.*` modules).

### Method

Cases (helper-level, mirroring the probed shapes):

- `T-1` helper variant (AC-1): one `tool_calls` entry with the `id` key removed and a prep-failure
  tuple with `tool_call_id == ""` → merge returns the failure tuple at that entry's position; no
  exception. (Full-round assertions live in `_03`.)
- `T-2` (AC-2, fails at HEAD as CASE C): entries with ids `["", "call_b", ""]` (the two id-less ones
  missing the key) and results ordered `("call_b", ...), ("", ...), ("", ...)` → merged order is
  `("", ...), ("call_b", ...), ("", ...)`.
- `T-3` (AC-3, scoped per revalidation): ids `["x", "y", "x"]` with collected results `[("x", ...),
  ("y", ...)]` (the collapsed second `x` does not exist upstream, `D-3`) → merged order is
  `("x", ...), ("y", ...)`; the docstring names `D-3` as the reason only one `x` row can exist.
- `T-4` (AC-4): ids `["a"]` with results `[("zz", ...), ("a", ...)]` (a tuple matching no entry) →
  merged order is `("a", ...), ("zz", ...)`: unmatched last, never position `0`, never dropped.
- `T-5` characterization pair (AC-6): two valid unique-id batches — (i) ids already in result order,
  (ii) ids out of result order (simulating concurrent completion) — merged order equals declared
  order in both, with no other transformation (same tuples, same count).

### Details

- `T-6` note in the module docstring: restoring `tc["id"]` (or wrapping the merge in
  `try/except KeyError`) makes `T-1`/`T-2` fail — recorded so a later refactor cannot re-introduce
  strict indexing silently.
- No `/opt/llm` access (no `ctx`, tmp-path-free), honoring the `tests/conftest.py` isolation guard.
- Tuples may be plain `tuple[str, str, dict, str, bool, str]` literals; no helper fixture file is
  needed (each case builds its own 2-3 tuples inline).

## Compatibility considerations

N/A: new test-only file; it must agree with `tests/agent/test_tool_preparation.py`
(`TestPrepareToolCallsBatchOrdering`) rather than contradict it — the expectations above come from
the same probe record.

## Security considerations

N/A: test-only, no I/O beyond pytest assertions.

## Rollback considerations

N/A: delete the new file (single-commit revert).

## Validation plan

- Before the production change: `uv run pytest tests/agent/test_tool_round_completion.py -q` →
  collection fails (helper does not exist); record the 87-pass baseline of `test_tool_runner.py` +
  `test_tool_preparation.py` + `test_tool_result_pairing.py` as the `T-5` anchor snapshot.
- After procedure doc `20261024-234513_01` lands: the same command passes.
- Mutation check `T-6`: scratch-copy restore of `tc["id"]` → `T-1`/`T-2` fail; restore afterwards.
- `uv run pytest tests/agent -q` then `uv run pytest -v` → no new failure.
- New file is not registered in `tools/check_module_size_baseline.txt` and is test-only, so the
  size gate does not track it (baseline lists `scripts/` modules).

## Completion criteria

- `T-2` fails against today's `complete_round()` merge and passes with the helper; `T-1`..`T-5` pass
  in the final state; the `T-6` note is present in the module docstring; the file adds no failure to
  `uv run pytest tests/agent -q`.

## Out of Scope

- Production code (procedure doc `20261024-234513_01`).
- The `execute_all_tool_calls()` integration case and the four characterization anchors in
  `tests/agent/test_tool_runner.py` (procedure doc `20261024-234513_03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the new test file with `T-1`..`T-5` and the `T-6` docstring note (before the production change) | Pending | — | — | must fail pre-change |
| 2 | Re-run the file after `20261024-234513_01` lands and after the `T-6` scratch mutation | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent -q` whole-package regression | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (regression + characterization coverage with mutation check)
- **Source issue**: `issues/20261021-093421_tool004-missing-tool-call-id-raises-keyerror.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-023815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234513
- **Related target files**: `tests/agent/test_tool_round_completion.py`
