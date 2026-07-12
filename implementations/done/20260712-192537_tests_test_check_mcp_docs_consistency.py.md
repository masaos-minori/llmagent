# Implementation Procedure: tests/test_check_mcp_docs_consistency.py

Source plan: `plans/20260712-191820_plan.md`, Implementation Steps §2 (Tests)
Source requirement: `requires/done/20260712_18_require.md`
Companion implementation doc: `implementations/20260712-192507_tools_check_mcp_docs_consistency.py.md`

## Goal

`TestCheckTransportErrorIsError` proves both that the Japanese-negation false positive is
fixed, and that a genuinely stale Japanese affirmative claim is still caught — so the fix
cannot silently regress into either under- or over-suppression.

## Scope

**In scope:** two new test methods added to `TestCheckTransportErrorIsError`
(`tests/test_check_mcp_docs_consistency.py:515-548`).

**Out of scope:** the four existing tests in the same class (unchanged); every other test
class in the file.

## Assumptions

1. `_mk_file(rel: str, lines: list[str]) -> DocFile` (defined at line 32) and
   `check_transport_error_is_error` are already imported/available in this test file, as used
   by the four existing tests in `TestCheckTransportErrorIsError` — no new imports needed.
2. The companion implementation (`implementations/20260712-192507_tools_check_mcp_docs_consistency.py.md`)
   adds `_JA_NEGATION_MARKERS = ("ことはない", "しない", "返さない")` and extends the skip
   condition to check for these substrings — these tests are written against that exact
   contract, using `"ことはない"` for the negative case.

## Implementation

### Target file

`tests/test_check_mcp_docs_consistency.py`

### Procedure

Add the following two methods to `TestCheckTransportErrorIsError`, after the existing
`test_known_issues_file_skipped` (line 548):

```python
def test_japanese_negation_no_issue(self) -> None:
    """Japanese negation of the stale claim should not produce a warning."""
    doc = _mk_file(
        "04_mcp_02_03_audit-logging-and-errors.md",
        ["HttpTransport は is_error=True を直接返すことはない"],
    )
    issues = check_transport_error_is_error(Path("/fake"), [doc])
    assert not issues

def test_japanese_affirmative_stale_still_triggers(self) -> None:
    """Japanese affirmative stale claim (no negation) should still produce a WARNING."""
    doc = _mk_file(
        "04_mcp_02_03_audit-logging-and-errors.md",
        ["HttpTransport は transport 障害時に is_error=True を返す"],
    )
    issues = check_transport_error_is_error(Path("/fake"), [doc])
    assert len(issues) == 1
    assert issues[0].severity == "WARNING"
```

Do not modify `test_no_stale_language_no_issue`, `test_stale_language_triggers_warning`,
`test_fenced_code_block_exempt`, or `test_known_issues_file_skipped`.

### Method

Same fixture pattern as all four existing tests in this class: build a single-line `DocFile`
via `_mk_file`, call `check_transport_error_is_error` directly (unit-level, no file I/O), and
assert on the returned `Issue` list. No new fixtures or helpers needed.

### Details

- `test_japanese_negation_no_issue` uses the literal phrasing style of the actual flagged
  line in `docs/04_mcp_02_03_audit-logging-and-errors.md:56` (verb + `を直接返すことはない`),
  so it exercises the same substring (`"ことはない"`) the companion implementation adds to
  `_JA_NEGATION_MARKERS`.
- `test_japanese_affirmative_stale_still_triggers` is the regression guard: it proves the new
  Japanese-negation skip condition does not accidentally swallow a line that both matches
  `_TRANSPORT_IS_ERROR_RE` and asserts the stale claim affirmatively (no negation word
  present) — this is the test that would fail if the fix were implemented as a blanket
  `> **注記:**`-block skip instead of the literal-substring approach the requirement specifies.
- Use the real target filename (`04_mcp_02_03_audit-logging-and-errors.md`) in both fixtures
  rather than a placeholder, matching the existing tests' convention in this class (all four
  use `"04_mcp_03_routing.md"` as a generic stand-in; either filename works since the function
  does not branch on filename except for the known-issues-file exemption, but using the real
  flagged file makes the regression test's intent unambiguous to a future reader).

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| New tests only | `uv run pytest tests/test_check_mcp_docs_consistency.py::TestCheckTransportErrorIsError -v` | 6 tests pass (4 existing + 2 new) |
| Full file | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | all pass, no regressions |
| Lint | `uv run ruff check tests/test_check_mcp_docs_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_check_mcp_docs_consistency.py` | no new errors |
