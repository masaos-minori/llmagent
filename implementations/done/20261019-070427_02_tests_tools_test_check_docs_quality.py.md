## Goal

Add unit tests to `tests/tools/test_check_docs_quality.py` covering the new
`check_stale_patterns` absent-canonical-document behavior: a dangling canonical reference is
flagged at `Warning`, a valid reference is not, and the current `docs/` corpus yields no false
positives. Guard the regression of existing `check_stale_patterns` tests.

## Scope

- **In-Scope**: dangling-canonical and valid-reference fixtures; confirm `Warning` severity and
  no corpus false positives; regression assertion on existing `test_check_docs_quality.py`.
- **Out-of-Scope**: changing the checker's behavior or existing test logic.

## Assumptions

- Tests invoke `check_stale_patterns` (or `check_docs_quality` end-to-end) against a temp `docs/`
  tree or fixture `DocFile` list.
- "Canonical document reference" is scoped to canonical-language mentions pointing at a
  non-existent path; fixtures must reflect that scope.

## Design decisions

- Mirror the existing `check_stale_patterns` test style so the new tests fit the suite and the
  regression guard is natural.

## Alternatives considered

N/A: mirroring the sibling test module is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_docs_quality.py`

### Procedure

1. Locate the existing `check_stale_patterns` tests.
2. Dangling-canonical fixture: a canonical-language reference (`[the canonical source for](docs/01_overview/overview_99_missing.md)`)
   whose target does not exist → assert one finding at `Warning` severity (REQ-001/002).
3. Valid-reference fixture: a canonical-language reference whose target exists → assert no finding.
4. Generic-dangling fixture: a non-canonical dangling internal link → assert the new pattern does
   NOT fire (scoped to canonical references); `check_links` remains responsible (REQ-003).
5. Corpus run: run `check_docs_quality.py` against the full `docs/` corpus and assert zero false
   positives on legitimate cross-domain or templated/placeholder references (REQ-004).
6. Regression: confirm existing `check_stale_patterns` tests still pass.

### Method

- Reuse the sibling test module's conventions (how it builds fixture docs, how it invokes the
  check, how it asserts on `Issue.severity`).
- Assert `issue.severity == "WARNING"` for the dangling-canonical case (not `"ERROR"`).
- For the corpus run, ensure templated/placeholder references (e.g. `{{path}}`, `$REF`) are not
  flagged.

### Details

- `REQ-001`/`REQ-002`: dangling canonical reference flagged at `Warning`; valid reference not.
- `REQ-003`: generic dangling link not flagged by the new pattern.
- `REQ-004`: corpus run yields zero false positives.
- Regression: existing `check_stale_patterns` suites unchanged.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_docs_quality.py` | Unit | `uv run pytest tests/tools/test_check_docs_quality.py` | Dangling canonical at Warning; valid/corpus clean |
| Whole suite | Regression | `uv run pytest` | Existing `check_stale_patterns` suites still pass |

## Completion criteria

- One test each covering the passing and failing path for REQ-001/002 and REQ-003.
- A corpus run proving zero false positives (REQ-004).
- The existing `check_stale_patterns` suites pass unchanged.

## Out of scope

Changing the checker's behavior or existing test logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | N/A | — | — | tool change is E01 |
| 2 | Add or update tests per Validation plan | Done | — | — | 12 new tests (67 total); passing + failing paths |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | ruff/mypy/bandit clean; corpus clean; all pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | docs edit is E03 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit + corpus coverage for the absent-canonical pattern)
- **Source issue**: `issues/done/20261018-173143_gov011_extend-stale_patterns-config-to-cover-canonical-document-references.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180921_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-070427
- **Related target files**: `tests/tools/test_check_docs_quality.py`
