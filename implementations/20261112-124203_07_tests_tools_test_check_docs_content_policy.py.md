## Goal
Add fixture tests in `tests/tools/test_check_docs_content_policy.py` that flag the `eventbus_08` table shape outside a guarded block, exempt it inside one, and leave a similar non-inventory table alone (`REQ-001`, `REQ-006` / `AC-1`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file tests `check_index_table` and the other `check_*` functions with `DocFile` fixtures (checked); it also names `check_docs_content_policy.py` in row 01 and 02, so it keeps its own procedure rather than being a companion.
- Write these tests before the regex change (row 01) and show them failing.

## Design decisions
- Three cases: (a) `| File | Class/Function | Signature | Summary |` outside a guard is reported; (b) inside `<!-- AUTO-GENERATED ... -->` is exempt; (c) a `| File | Purpose | Description |` table is not reported.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tests/tools/test_check_docs_content_policy.py`

### Procedure
1. Add the three tests using the file's existing `DocFile` fixture pattern.
2. Run them against the unmodified checker; expect (a) to fail.

### Method
- Follow the existing `check_index_table` tests for the fixture shape and the guard comment forms.

### Details
- Do not use `docs/24_eventbus/eventbus_08_reference_api.md` as the fixture (generated, exempt).

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_content_policy.py -q`; `uv run ruff format`/`ruff check`/`mypy` on the file — clean.

## Completion criteria
- (a) fails before and passes after the widening; (b) and (c) pass both times.

## Out of Scope
- Tests for the other checkers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the three fixture tests and show (a) failing | Pending | — | — | |
| 2 | Run after the regex change in row 01: all pass | Pending | — | — | |
| 3 | Run ruff format/check and mypy on the test file | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` / `REQ-006` — fixture for the `eventbus_08` table shape
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tests/tools/test_check_docs_content_policy.py`
