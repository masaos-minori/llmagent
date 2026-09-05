## Goal

Add unit tests for `tools/check_docs_content_policy.py`'s detection logic —
one test per remove-category plus one retain-category-only false-positive
check (REQ-007).

## Scope

- In-scope: this new test file only.
- Out-of-scope: implementing the script under test
  (`implementations/20260905-112812_01`); registration
  (`implementations/20260905-112812_02`); `tools/TOOL_DESCRIPTIONS.md`
  (`implementations/20260905-112812_04`).

## Assumptions

- **Blocking precondition**: same as `implementations/20260905-112812_01` —
  this row cannot be executed until `tools/check_docs_content_policy.py`
  exists (that row must land first, matching this Plan's own `seq` order:
  01 precedes 03).
- Follows the existing sibling-file-per-check-script test convention
  (re-confirmed present this cycle: `tests/tools/test_check_docs_structure.py`
  exists for `tools/check_docs_structure.py`).

## Design decisions

Six fixture-based tests: one small in-memory or temp-file document per
remove-category (5), each containing exactly that category's pattern and
confirming it is detected; one additional fixture containing only
retain-category-style content (prose describing component responsibility,
dependency direction, etc. — no file tree, no index table, no port number,
no location mapping) confirming zero false positives.

## Alternatives considered

Testing against the real corpus files cited in the source Plan's evidence
(e.g. `docs/01_overview-files-02-rag.md`) directly, instead of small
fixtures — rejected: real corpus files can change independently of this test
suite (per `rules/ai-execution.md` Context Reading's staleness caveat),
making the test suite brittle to unrelated doc edits; small, purpose-built
fixtures isolate exactly one category's pattern per test.

## Implementation

### Target file

`tests/tools/test_check_docs_content_policy.py`

### Procedure

1. Confirm `tools/check_docs_content_policy.py` exists and exposes one
   detection function per remove-category (from
   `implementations/20260905-112812_01`) before writing tests against it.
2. Create fixture documents (as string constants or temp files, matching
   this repository's existing `tests/tools/test_check_docs_structure.py`
   fixture style) for each of the five remove-categories.
3. Write one test per remove-category asserting the corresponding detection
   function returns at least one `Issue` for its fixture.
4. Write one test asserting zero `Issue`s are returned for a
   retain-category-only fixture (no remove-category pattern present).

### Method

Standard `pytest` test functions, one per category plus the false-positive
check (6 total), following this repository's existing `tests/tools/`
fixture/assertion conventions (confirmed present in
`tests/tools/test_check_docs_structure.py`).

### Details

Fixture content should mirror the confirmed real-corpus examples in shape
(not verbatim copy) to keep detection patterns realistic: a short ASCII tree
snippet for the file-tree test; a two-column-plus table with
`Function`/`Signature`/`Description` headers for the index-table test; an
inline `# ... (moved by X.py)`-style comment for the location-mapping test; a
heading containing "(Port NNNN)" for the port-number test. The
retain-category-only fixture should contain prose describing component
responsibility and dependency direction, with no tree-drawing characters, no
index table, no location-mapping phrasing, and no port number.

## Compatibility considerations

No interface change — new test file only, no existing test is modified.

## Security considerations

N/A — test-only, no production code, no credentials.

## Rollback considerations

New, standalone test file under version control; revert via `git revert` if
a fixture proves unrepresentative. No other file depends on this test
file's existence yet.

## Validation plan

`uv run pytest tests/tools/test_check_docs_content_policy.py` — all 6 tests
pass.

## Completion criteria

Six tests exist and pass: one per remove-category confirming detection, one
confirming no false positive on retain-category-only content.

## Out of scope

Implementing the script under test. Testing against real corpus files
directly (see Alternatives considered).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | `implementations/done/20260905-112812_01` landed first, confirmed 5 detection function names via `grep -n "^def "` before writing tests. Created 7 tests (one per remove-category, one for the illustrative-port exemption, one retain-category-only false-positive check) using small in-line fixtures via a `DocFile` helper. |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | This row IS the test addition |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `ruff format`/`ruff check`/`mypy` clean; `uv run pytest tests/tools/test_check_docs_content_policy.py` — 7 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260905 | 20260905 | N/A: test file only |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `tools/check_docs_content_policy.py` (`implementations/20260905-112812_01`) not yet implemented | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260903-200135_docscope2_build-content-policy-detection-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-102139_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-112812
- **Related target files**: tests/tools/test_check_docs_content_policy.py
