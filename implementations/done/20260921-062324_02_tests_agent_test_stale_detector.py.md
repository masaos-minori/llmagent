## Goal
Update the existing `_check_line_refs()`/`_check_symbol_refs()` test calls to match
their new signatures (Row 1 of this Plan adds `source_dir`, `target_file`, and
`file_cache` parameters), and add new regression tests covering the non-symbol
allowlist and file-scoped citation resolution.

## Scope
In scope: update 6 existing test-function call sites in
`tests/agent/test_stale_detector.py` to the new signatures; add new tests for
REQ-001, REQ-002, REQ-003 (`plans/20260920-221706_plan.md`).
Out of scope: `scripts/agent/stale_detector.py` itself (covered by this Plan's Row 1,
a separate implementation procedure document); any test for
`_check_import_refs()`/`_check_before_blocks()` (unchanged by this Plan).

## Assumptions
- Row 1 (`scripts/agent/stale_detector.py`) is implemented before or alongside this
  row — the updated call sites and new tests both depend on the new function
  signatures and helpers Row 1 adds; until Row 1 lands, this row's updated tests will
  fail with a `TypeError` on argument count.
- `Path(".")` is a valid `source_dir` for the new tests' existing-Target-file-only
  cases (no scoped path is ever found in their `proc_text`, so `source_dir` is never
  actually dereferenced) — matches the existing tests' style of not depending on real
  filesystem state.
- `scripts/agent/llm_turn_runner.py` (confirmed 295 lines via `wc -l`) and its
  `LLMTurnRunner` class (confirmed at line 41 via `grep`) are used as the real
  Reference File for the new file-scoping regression tests, per the Plan's Reference
  Files section — these tests run against the actual repository file, so `source_dir`
  must resolve to the real repository root (`Path(".")`, matching pytest's default
  working directory when run from the repository root, consistent with every other
  test in this repository).

## Design decisions
- Update all 6 existing calls (3 in `TestCheckLineRefs`, 4 in `TestCheckSymbolRefs`)
  to pass `Path("."), "dummy_target.py", {}` as the three new trailing arguments — a
  fixed, inert target file name that never appears in any of these tests' `proc_text`,
  so `_find_scoped_path()` always returns `None` and behavior is byte-for-byte
  identical to before Row 1's change.
- For the new Reference-File regression tests, use `scripts/agent/llm_turn_runner.py`
  (a real file, confirmed 295 lines) as the cited Reference File, and a short
  fixed-length `source_lines`/`source_content` standing in for a much shorter Target
  file — this reproduces the Plan's own concrete historical case
  (`docs/05_agent_05_llm-and-streaming.md`, 148 lines, citing lines 149-163 of the
  294-line-at-the-time `llm_turn_runner.py`) without depending on that specific doc
  file's current content.

## Alternatives considered
- Mocking `Path.exists()`/`Path.read_text()` instead of reading a real repository
  file: rejected — every other test in this file already exercises real string/regex
  logic without mocking the filesystem; using a real, stable repository file
  (`scripts/agent/llm_turn_runner.py`) is simpler and matches the Plan's own Reference
  Files section, which names this exact file for this exact purpose.

## Implementation
### Target file
`tests/agent/test_stale_detector.py`

### Procedure
1. Add `from pathlib import Path` to the imports if not already present (confirm via
   Read — this file currently imports only from `agent.stale_detector`).
2. Update `TestCheckLineRefs`'s three existing calls (lines 131, 138, 146) to pass the
   three new trailing arguments.
3. Update `TestCheckSymbolRefs`'s four existing calls (lines 158, 165, 173, 180) to
   pass the three new trailing arguments.
4. Add `test_allowlisted_tool_vocabulary_term_not_flagged` to `TestCheckSymbolRefs`
   (REQ-001): a procedure citing `Edit`, `mypy`, and `related` in backticks, with an
   empty/unrelated `source_content` — assert no `symbol_missing` finding.
5. Add `test_symbol_from_reference_file_not_flagged_when_absent_from_target` to
   `TestCheckSymbolRefs` (REQ-002): a procedure citing `LLMTurnRunner` together with
   `` `scripts/agent/llm_turn_runner.py` `` in the same sentence, with a `source_content`
   that does not contain `LLMTurnRunner` — assert no `symbol_missing` finding (the
   symbol is validated against the real Reference File instead).
6. Add `test_line_citation_for_reference_file_not_flagged_against_target_length` to
   `TestCheckLineRefs` (REQ-003): a procedure citing
   `` `scripts/agent/llm_turn_runner.py` `` (lines 149-163) in the same sentence, with
   a 10-line `source_lines` standing in for the Target file — assert no
   `line_out_of_bounds` finding (validated against the real, 295-line Reference File
   instead of the 10-line Target file).
7. Add `test_line_citation_for_target_file_still_flagged_out_of_bounds` to
   `TestCheckLineRefs`: same shape as the existing
   `test_out_of_bounds_line_returns_stale`, but with a scoped-but-nonexistent path
   nearby (e.g. `` `scripts/agent/does_not_exist.py` ``) to confirm the fallback to
   Target-file validation still correctly flags an out-of-bounds citation when the
   named Reference File cannot be resolved.

### Method
Direct file edit (`Edit` tool) — update 6 existing call-site lines, append 4 new test
functions to their respective existing classes; no change to any existing assertion
logic beyond the added call arguments.

### Details
Existing calls to update (confirmed via Read, lines 131, 138, 146, 158, 165, 173,
180):
```python
_check_line_refs(result, proc_text, source_lines)
...
_check_symbol_refs(result, proc_text, source_content)
```
Target shape for each (illustrative — apply to all 6 call sites):
```python
_check_line_refs(result, proc_text, source_lines, Path("."), "dummy_target.py", {})
...
_check_symbol_refs(result, proc_text, source_content, Path("."), "dummy_target.py", {})
```

New tests to add (illustrative — write exact final code during implementation):
```python
class TestCheckSymbolRefs:
    ...
    def test_allowlisted_tool_vocabulary_term_not_flagged(self) -> None:
        result = StaleResult.clean()
        proc_text = "Use `Edit`, `mypy`, and front-matter key `related` here"
        source_content = "# unrelated source"
        _check_symbol_refs(
            result, proc_text, source_content, Path("."), "dummy_target.py", {}
        )
        assert result.is_stale is False

    def test_symbol_from_reference_file_not_flagged_when_absent_from_target(
        self,
    ) -> None:
        result = StaleResult.clean()
        proc_text = (
            "`LLMTurnRunner` is defined in `scripts/agent/llm_turn_runner.py`."
        )
        source_content = "# target file does not define this class"
        _check_symbol_refs(
            result, proc_text, source_content, Path("."), "dummy_target.py", {}
        )
        assert result.is_stale is False


class TestCheckLineRefs:
    ...
    def test_line_citation_for_reference_file_not_flagged_against_target_length(
        self,
    ) -> None:
        result = StaleResult.clean()
        proc_text = (
            "See `scripts/agent/llm_turn_runner.py` (lines 149-163) for details."
        )
        source_lines = [""] * 10
        _check_line_refs(
            result, proc_text, source_lines, Path("."), "dummy_target.py", {}
        )
        assert result.is_stale is False

    def test_line_citation_for_target_file_still_flagged_out_of_bounds(self) -> None:
        result = StaleResult.clean()
        proc_text = (
            "See `scripts/agent/does_not_exist.py` in passing. See Line 9999 here."
        )
        source_lines = [""] * 100
        _check_line_refs(
            result, proc_text, source_lines, Path("."), "dummy_target.py", {}
        )
        assert result.is_stale is True
        assert any(m["type"] == "line_out_of_bounds" for m in result.mismatches)
```
Confirm during implementation that `test_line_citation_for_target_file_still_flagged_out_of_bounds`'s
citation and the "See Line 9999" reference fall in the same paragraph as designed by
`_find_scoped_path()`'s scoping rule (Row 1's Design) — adjust the fixture text if
paragraph boundaries (blank lines) split them unexpectedly, since a nonexistent
scoped path must still resolve to `None` and fall back to Target-file validation.

## Compatibility considerations
The 6 updated call sites keep every existing assertion unchanged — only the call
arguments grow, matching Row 1's new signatures exactly. No existing test's expected
outcome changes.

## Security considerations
N/A: test-only change; the new Reference-File tests read a real, already-repository-
tracked source file (`scripts/agent/llm_turn_runner.py`), no external input.

## Rollback considerations
Trivially revertable: reverting the 6 call-site argument additions and removing the 4
new test functions restores the exact prior test file — but only in tandem with
reverting Row 1's signature change, since a full revert of only this row while Row 1's
new signatures remain would break these calls.

## Validation plan
- `uv run pytest tests/agent/test_stale_detector.py -v` — full file, run once Row 1
  has also landed (REQ-001, REQ-002, REQ-003 of `plans/20260920-221706_plan.md`).
- `uv run ruff check tests/agent/test_stale_detector.py` /
  `uv run mypy tests/agent/test_stale_detector.py`.

## Completion criteria
- All 6 updated existing tests pass unchanged in outcome.
- `test_allowlisted_tool_vocabulary_term_not_flagged` passes, proving AC-1.
- `test_symbol_from_reference_file_not_flagged_when_absent_from_target` and
  `test_line_citation_for_reference_file_not_flagged_against_target_length` pass,
  proving AC-2.
- `test_line_citation_for_target_file_still_flagged_out_of_bounds` (plus the existing,
  unmodified `test_out_of_bounds_line_returns_stale`/`test_missing_symbol_returns_stale`)
  pass, proving AC-3.

## Out of scope
- Implementing the allowlist/scoping logic itself — covered by this Plan's Row 1
  (`scripts/agent/stale_detector.py`), a separate implementation procedure document.
- Any test for `_check_import_refs()`/`_check_before_blocks()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update 6 existing call sites to the new signatures | Completed | — | 20260921-192353 |  |
| 2 | Add the 4 new regression tests | Completed | — | 20260921-192353 |  |
| 3 | Run full test file (after Row 1 lands) and lint/type checks | Completed | — | 20260921-192353 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (test coverage for allowlist and file-scoped citation resolution)
- **Source issue**: issues/20260920-175023_staledet01_reduce-stale_detector.py-false-positives-on-docs-target-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-221706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260921-062324
- **Related target files**: tests/agent/test_stale_detector.py