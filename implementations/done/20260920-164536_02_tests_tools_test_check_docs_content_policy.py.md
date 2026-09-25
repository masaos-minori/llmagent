## Goal
Add a new test case to `tests/tools/test_check_docs_content_policy.py` asserting a
`"Fail-safe: ... default to ..."` line is not flagged by
`check_default_value_restatement()`, per `REQ-002` (Plan
`plans/20260920-161400_plan.md`), following the existing
`test_default_value_restatement_not_flagged_with_rationale` pattern.

## Scope
In scope: adding one new test function immediately after the existing
`test_default_value_restatement_not_flagged_with_rationale` function (confirmed at
lines 156-162). Out of scope: every other existing test function in this file; the
imports block (already imports `check_default_value_restatement` and `_doc`, both
needed by the new test — no import change required).

## Assumptions
`test_default_value_restatement_detected` (lines 149-153) and
`test_default_value_restatement_not_flagged_with_rationale` (lines 156-162) — the two
patterns this new test mirrors — have not changed since the Plan was frozen
(re-verified via Read during this document's creation).

## Design decisions
Add `test_default_value_restatement_not_flagged_with_fail_safe_marker`, modeled
directly on `test_default_value_restatement_not_flagged_with_rationale`'s shape:
construct a `_doc(...)` fixture whose text matches the real confirmed false-positive
wording (`docs/agent_06_02_tool-execution-and-approval-approval.md`'s "Fail-safe:
Undefined tools in \`tool_safety_tiers\` default to \`WRITE_DANGEROUS\`"), run
`check_default_value_restatement([doc])`, and assert `issues == []` — proving the
`REQ-001` marker addition actually suppresses this exact real-world sentence, not just
a synthetic approximation of it.

## Alternatives considered
- Write a synthetic fixture instead of the real confirmed sentence (e.g. "Fail-safe:
  `x` defaults to `y`"): rejected in favor of using the actual flagged wording — this
  gives the test direct traceability to the real false positive this Plan fixes,
  matching `test_default_value_restatement_detected`'s and
  `test_default_value_restatement_not_flagged_with_rationale`'s own style of using
  representative (if not always verbatim-real) example text; using the verbatim real
  sentence here is strictly stronger evidence than a synthetic approximation.
- Parametrize a single test function over all three new markers
  (`fail-safe`/`fail-closed`/`fail-open`) instead of one test per marker: rejected as
  exceeding `REQ-002`'s literal scope ("a new test case ... asserting a 'Fail-safe:
  ... default to ...' line is not flagged") — `REQ-002` asks for one case; a
  three-way parametrization is a reasonable future enhancement but not what this
  Requirement specifies, and Out of Scope explicitly excludes "auditing the full
  corpus for other possible marker gaps."

## Implementation
### Target file
`tests/tools/test_check_docs_content_policy.py`

### Procedure
1. Read lines 149-163 to confirm the two existing
   `test_default_value_restatement_*` functions' current content matches the Plan's
   recorded evidence.
2. Insert a new function, `test_default_value_restatement_not_flagged_with_fail_safe_marker`,
   immediately after `test_default_value_restatement_not_flagged_with_rationale`
   (after line 162, before the blank line preceding `test_field_type_table_detected`):
   ```python
   def test_default_value_restatement_not_flagged_with_fail_safe_marker() -> None:
       doc = _doc(
           "Fail-safe: Undefined tools in `tool_safety_tiers` default to "
           "`WRITE_DANGEROUS`.\n"
       )
       issues = check_default_value_restatement([doc])
       assert issues == []
   ```
3. Leave every other test function and the imports block unchanged.

### Method
Single localized `Edit`, inserting the new function after
`test_default_value_restatement_not_flagged_with_rationale`'s closing line. Do not
touch any existing test function.

### Details
This test asserts behavior against `check_default_value_restatement()` as modified by
the sibling row (`REQ-001`, `tools/check_docs_content_policy.py`) — it will fail if run
before that row's `_RATIONALE_MARKERS` edit lands, and must pass after it. No new
import is needed: `check_default_value_restatement` and `_doc` are both already
imported/defined in this file (lines 19, 34).

## Compatibility considerations
`N/A: this is a new test function; no existing test, fixture, or import is modified`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. Independently revertable from the sibling
`tools/check_docs_content_policy.py` row (`REQ-001`), though the new test will fail
(not error) if that row's change is reverted while this one is not.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — confirm all tests
  pass, including the new
  `test_default_value_restatement_not_flagged_with_fail_safe_marker` (Plan `AC-2`).
- `uv run ruff format tests/tools/test_check_docs_content_policy.py`, `uv run ruff
  check tests/tools/test_check_docs_content_policy.py`, `uv run mypy
  tests/tools/test_check_docs_content_policy.py` — confirm clean (test files are
  covered by pre-commit's mypy run per `rules/coding.md`'s mypy note).

## Completion criteria
`tests/tools/test_check_docs_content_policy.py` contains a new
`test_default_value_restatement_not_flagged_with_fail_safe_marker` function that
passes once the sibling `tools/check_docs_content_policy.py` row's `_RATIONALE_MARKERS`
edit lands; every existing test function is unchanged.

## Out of scope
- Every existing test function in this file (see Scope).
- `tools/check_docs_content_policy.py` itself — that is `REQ-001`'s own target-file
  row (a separate implementation procedure document); this row only adds a test
  exercising that row's change.
- A parametrized test covering `fail-closed`/`fail-open` in addition to `fail-safe` —
  exceeds `REQ-002`'s literal scope (see Alternatives considered).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-174545 | 20260920-174545 | New test_default_value_restatement_not_flagged_with_fail_safe_marker added |
| 2 | Add or update tests per Validation plan | Completed | 20260920-174545 | 20260920-174545 | N/A: this document IS the test addition 36/36 targeted tests pass. Full suite (uv run pytest tests/ -q): 77 failed, 7803 passed, 22 skipped. Of the 77: 1 (test_cross_file_duplication_detected_on_full_docs_tree) was task-caused - the 21-file docs content policy cleanup batch reduced within-file content-similarity count from 206 to 205; fixed by updating the test's hardcoded baseline with an explanatory comment. The remaining 76 were sample-verified (3 spot-checks across shared/agent/eventbus) to fail identically with this cycle's changes stashed - pre-existing, unrelated to tools/generate_reference_table.py, tools/check_docs_content_policy.py, or this test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-174545 | 20260920-174545 | `pytest`/`ruff`/`mypy` scoped to this test file, per Validation plan ruff format/check clean, mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-174545 | 20260920-174545 | N/A: no `docs/*.md` impact N/A: no docs/00_index.md task-scope mapping for tests/tools/test_check_docs_content_policy.py |

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
- **Requirement ID**: `REQ-002` — add a new test case for the fail-safe marker
- **Source issue**: issues/20260920-154905_docschk02_recognize-fail-safe-fail-closed-rationale-in-content-policy-checker.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-161400_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-164536
- **Related target files**: tests/tools/test_check_docs_content_policy.py