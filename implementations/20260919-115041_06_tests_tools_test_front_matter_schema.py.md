## Goal
Add unit tests for `class_enum` parsing in
`tests/tools/test_front_matter_schema.py` (`REQ-007`).

## Scope
In scope: new test functions in this one file covering `class_enum` parsing
(present and absent cases). Out of scope: modifying existing `area_enum`/
`status_enum` tests.

## Assumptions
- File exists and follows an existing `area_enum`/`status_enum` test pattern —
  re-confirmed via `ls tests/tools/test_front_matter_schema.py`. Read the file's
  actual existing test function names/style immediately before writing new ones
  (not assumed here, to avoid guessing this file's exact current structure).
- Depends on seq 02 (`tools/_front_matter_schema.py`)'s `class_enum` field and
  seq 01 (`schemas/doc_front_matter.json`)'s `class` property both existing for
  a real-schema-file test case to actually exercise parsing.

## Design decisions
Mirror whatever pattern this file already uses for `area_enum`/`status_enum`
tests exactly (read the file first) — add a `class_enum`-present case (schema
has the `class` property with its enum) and a `class_enum`-absent case (schema
lacks it, or no schema file at all — the existing `_default_schema()` fallback
path), matching the granularity of the existing `area_enum`/`status_enum` test
pairs.

## Alternatives considered
N/A: this file's existing test structure for `area_enum`/`status_enum` is the
direct, required precedent (per `REQ-007`'s own language, "mirroring the
area_enum/status_enum handling") — no alternative test structure was
considered.

## Implementation
### Target file
tests/tools/test_front_matter_schema.py

### Procedure
1. Read the existing file in full to identify its exact `area_enum`/
   `status_enum` test function names and fixture style (e.g. whether it uses a
   temp file via `tmp_path` and `load_front_matter_schema(schema_path=...)`, or
   constructs schema dicts directly).
2. Add 2 new test functions mirroring that exact style: one asserting
   `class_enum` is populated correctly when the schema defines it, one
   asserting it is `None` when absent (both via the schema-file path, and via
   `_default_schema()`'s built-in fallback, matching however the existing
   `area_enum`/`status_enum` absent-case test is structured).

### Method
Direct code edit (`Edit` tool), following the file's own existing pattern
exactly (determined by reading it first, per Procedure step 1).

### Details
- Test schema fixture for the present case should use the real 7-value enum
  (Governance/Guide/Specification/Reference/Operations/Note/Known Issues),
  matching seq 01's actual schema content.
- Confirm the existing `area_enum`/`status_enum` tests are unaffected (run the
  full file's test suite, not just the 2 new tests, per Validation plan).

## Compatibility considerations
Additive test-only change.

## Security considerations
N/A: test code only.

## Rollback considerations
`git checkout -- tests/tools/test_front_matter_schema.py` reverts this row
independently.

## Validation plan
- `uv run pytest tests/tools/test_front_matter_schema.py -v` — all tests
  (existing + new) pass.
- `uv run ruff check tests/tools/test_front_matter_schema.py`, `uv run mypy
  tests/tools/test_front_matter_schema.py`.

## Completion criteria
- 2 new tests (present/absent `class_enum`) exist and pass.
- Existing `area_enum`/`status_enum` tests are unmodified and still pass.

## Out of scope
Modifying existing `area_enum`/`status_enum` test coverage.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on seq 01/seq 02 landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's own Target file IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run pytest tests/tools/test_front_matter_schema.py -v` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test file only |

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
- **Requirement ID**: REQ-007 (unit tests for class_enum parsing)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: tests/tools/test_front_matter_schema.py
