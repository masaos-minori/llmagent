## Goal
Add `"fail-safe"`, `"fail-closed"`, and `"fail-open"` to
`tools/check_docs_content_policy.py`'s `_RATIONALE_MARKERS` frozenset (line 58-60),
per `REQ-001` (Plan `plans/20260920-161400_plan.md`), so
`check_default_value_restatement()` stops flagging the three confirmed false-positive
fail-safe-default sentences while continuing to flag genuine default-value
restatements.

## Scope
In scope: the `_RATIONALE_MARKERS` frozenset literal (lines 58-60) only. Out of scope:
`_DEFAULT_VALUE_RE` (line 55-57), `_FIELD_TYPE_TABLE_HEADER_RE`,
`_MIN_MECHANICAL_TABLE_ROWS`, `check_default_value_restatement()`'s control flow
(lines ~302-336), and every other detection function in this file
(`check_literal_port_number`, field/type table detection, config-file inventory
detection, etc.) — none of these are touched by `REQ-001`.

## Assumptions
`_RATIONALE_MARKERS`'s exact current content (re-verified via Read during this
document's creation: `{"because", "since", "in order to", "so that", "rationale", "to
avoid", "to ensure"}` at lines 58-60) has not changed since the Plan was frozen — no
commit has touched this file since.

## Design decisions
Add the three new marker strings as additional elements of the same `frozenset[str]`
literal, in lowercase (matching the existing markers' case convention, since the
checking code lowercases the candidate line before the `in` substring check — see
`check_default_value_restatement()`'s `lowered = line.lower()` step). No change to the
function's control flow, `_DEFAULT_VALUE_RE`, or any other detection function — per
the Plan's Implementation intent, this is a pure allowlist extension.

## Alternatives considered
- Add the markers as a separate frozenset checked by a new branch in
  `check_default_value_restatement()`: rejected — `_RATIONALE_MARKERS` is already
  checked via a single `any(marker in lowered for marker in _RATIONALE_MARKERS)`
  expression; a second, parallel frozenset would duplicate that check for no benefit,
  contradicting the Plan's own "no new regex or control flow is needed" guidance.
- Use a regex alternation (e.g. `fail-(safe|closed|open)`) instead of three literal
  strings: rejected — `_RATIONALE_MARKERS` is a plain substring-match frozenset, not a
  regex set; introducing regex here would be an unrequested change to the checking
  mechanism itself.

## Implementation
### Target file
`tools/check_docs_content_policy.py`

### Procedure
1. Read lines 55-60 to confirm `_RATIONALE_MARKERS`'s current content matches the
   Plan's recorded evidence.
2. Edit the `_RATIONALE_MARKERS` frozenset literal to add `"fail-safe"`,
   `"fail-closed"`, and `"fail-open"` as three additional string elements (order within
   the literal does not affect behavior — a `frozenset` is unordered; add them in a
   readable position, e.g. immediately after `"to ensure"`).
3. Leave `_DEFAULT_VALUE_RE`, `_FIELD_TYPE_TABLE_HEADER_RE`,
   `_MIN_MECHANICAL_TABLE_ROWS`, and every function in this file unchanged.

### Method
Single localized `Edit` on the `_RATIONALE_MARKERS` literal (lines 58-60). Do not touch
any other line.

### Details
The three new markers must be lowercase strings, matching the existing markers'
convention — the checking code's `lowered = line.lower()` step means an uppercase or
mixed-case marker in the frozenset would never match, silently failing to suppress the
intended false positives. Do not add a marker broad enough to accidentally suppress an
unrelated genuine finding (e.g. bare `"safe"` or `"open"` would be too broad and could
match unrelated prose) — use the full compound terms `"fail-safe"`/`"fail-closed"`/
`"fail-open"` exactly as specified by `REQ-001`.

## Compatibility considerations
Additive-only change to a `frozenset[str]` literal used by one function
(`check_default_value_restatement()`) — no public interface, CLI argument, or output
format changes. `N/A` beyond that.

## Security considerations
`N/A: no security-relevant content is touched` — this is a documentation-linting tool
with no runtime/production code path.

## Rollback considerations
Revert via `git checkout` on this one file. Independently revertable from the sibling
test-file row (`REQ-002`).

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings at the
  three false-positive locations (`docs/agent_06_02_tool-execution-and-approval-approval.md:46,117`,
  `docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md:86`) (Plan
  `AC-1`).
- Confirm the genuine finding at
  `docs/00_governance_03_issue-and-uncertainty-management.md:451` (and `:454`) is still
  reported — a full-corpus run's finding count must decrease by exactly 3, not more
  (Plan `AC-3`).
- `uv run ruff format tools/check_docs_content_policy.py`, `uv run ruff check
  tools/check_docs_content_policy.py`, `uv run mypy tools/check_docs_content_policy.py`
  — per `routing.md` "Adding a new tool"'s lighter validation sequence (pass the path
  explicitly, since `tools/` is outside `pyproject.toml`'s default `mypy` `files`
  scope).
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` — confirm this
  file's edit is covered by the sibling test-file row's new test case (`REQ-002`).

## Completion criteria
`_RATIONALE_MARKERS` contains `"fail-safe"`, `"fail-closed"`, and `"fail-open"` in
addition to its existing seven markers; `check_default_value_restatement()`'s control
flow is unchanged; a full-corpus `check_docs_content_policy.py` run's finding count
decreases by exactly 3 (the three confirmed false positives), with the genuine finding
at `00_governance_03...md:451`/`:454` still reported.

## Out of scope
- `_DEFAULT_VALUE_RE`, `_FIELD_TYPE_TABLE_HEADER_RE`, `_MIN_MECHANICAL_TABLE_ROWS`, and
  every other module-level constant in this file.
- Every detection function other than `check_default_value_restatement()`
  (`check_literal_port_number`, field/type table detection, config-file inventory
  detection, CLI-command-enumeration detection, etc.).
- Auditing the full corpus for other possible marker gaps beyond fail-safe/
  fail-closed/fail-open — per the Plan's own Out of Scope, file a separate issue if
  another gap is found.
- `docs/agent_06_02_tool-execution-and-approval-approval.md`,
  `docs/agent_06_03_tool-execution-and-approval-concurrency-safety.md` — these
  files require no edit; this row only stops the tool from flagging them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-172550 | 20260920-172550 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-172550 | 20260920-172550 | Covered by the sibling row's new test case in `tests/tools/test_check_docs_content_policy.py` All 35 existing tests pass; 3 confirmed false positives suppressed, genuine finding at 00_governance_03:451,454 still detected |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-172550 | 20260920-172550 | Use the `tools/*.py` lighter sequence per `routing.md` "Adding a new tool," not the full `scripts/` toolchain ruff format/check clean, mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-172550 | 20260920-172550 | N/A: no `docs/*.md` impact N/A: no docs/00_index.md task-scope mapping for tools/check_docs_content_policy.py |

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
- **Requirement ID**: `REQ-001` — add fail-safe/fail-closed/fail-open markers to `_RATIONALE_MARKERS`
- **Source issue**: issues/20260920-154905_docschk02_recognize-fail-safe-fail-closed-rationale-in-content-policy-checker.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-161400_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-164536
- **Related target files**: tools/check_docs_content_policy.py