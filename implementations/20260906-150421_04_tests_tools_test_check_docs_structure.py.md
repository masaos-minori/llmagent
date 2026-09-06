## Goal
Add a duplicate-ADR-ID test case to `tests/tools/test_check_docs_structure.py` for
seq 02's new `GV-003` (Unique ADR ID) check (REQ-009).

## Scope
- In scope: one new test class/function in `tests/tools/test_check_docs_structure.py`
  exercising seq 02's duplicate-ADR-ID detection.
- Out of scope: seq 02's own implementation (`tools/check_docs_structure.py`,
  read-only from this row); every other existing test class in this file.

## Assumptions
- **Blocking dependency**: seq 02
  (`implementations/20260906-150421_02_tools_check_docs_structure.py.md`) was still
  an empty skeleton at the time of this cycle's read (2026-09-06) — this row cannot
  finalize its exact fixture/assertion shape until seq 02 documents the check's
  actual function name and return-value shape. This document records the test
  design at the level the Plan's own Requirement (REQ-004: "fail on duplicate ADR
  identifiers across `docs/adr/*.md`") specifies, to be reconciled against seq 02's
  landed interface before implementation.
- Confirmed this cycle: `docs/adr/*.md` files use an `ADR-{NNN}` identifier
  convention (e.g. `ADR-001`, `ADR-003` — confirmed via `rg -oE "ADR-[0-9]+"
  docs/adr/*.md`); this test's fixture should construct two temporary files sharing
  the same `ADR-{NNN}` identifier to trigger the duplicate case.

## Design decisions
- Follow this file's existing per-concern class structure (`TestSchemaComplianceRequiredFields`,
  `TestSchemaComplianceEnums`, `TestCheckSize`, `TestValidateFileSchemaOptIn`) — add
  a new `TestDuplicateAdrId` class rather than adding cases to an existing,
  differently-scoped class.
- Use `tmp_path`-based temporary `.md` files (matching `TestCheckSize`'s existing
  fixture style in this same file) rather than mocking the filesystem, so the test
  exercises real file-reading and ID-extraction logic end-to-end.

## Alternatives considered
- Test only via a unit-level function call with in-memory strings, no real files:
  considered, but this file's existing convention (`TestCheckSize`) already uses real
  `tmp_path` files for structural checks — matching that convention keeps the file
  internally consistent.

## Implementation
### Target file
`tests/tools/test_check_docs_structure.py`

### Procedure
1. Re-read seq 02's landed implementation (once it exists) to confirm the exact
   function name and signature the duplicate-ADR-ID check exposes.
2. Add `class TestDuplicateAdrId`, with at least: a test constructing two temporary
   `docs/adr/`-style files sharing the same `ADR-{NNN}` identifier — assert the
   check reports a failure/error naming both files; a test with two files having
   distinct IDs — assert no failure.
3. Do not add cases for any other Governance Verification Matrix rule in this pass
   — scope is REQ-009's single duplicate-ADR-ID case only.

### Method
Confirmed this cycle (2026-09-06) via direct read: this file's existing structure
(4 classes, 178 lines) and `docs/adr/*.md`'s `ADR-{NNN}` naming convention (`rg`
confirmed `ADR-001` through at least `ADR-005` present).

### Details
No change to any existing test class.

## Compatibility considerations
N/A: additive test only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if seq 02's landed interface differs
enough from this document's assumption to require a different fixture shape.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_structure.py -v` — new
  `TestDuplicateAdrId` cases pass alongside all existing cases.

## Completion criteria
- A duplicate-ADR-ID case and a non-duplicate case both pass against seq 02's
  landed check.

## Out of scope
- `tools/check_docs_structure.py` — tracked in seq 02.
- `tools/check_canonical_source_conflicts.py` — tracked in seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked on seq 02 landing — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | seq 02 (`tools/check_docs_structure.py`'s GV-003 check) not yet implemented as of 2026-09-06 | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260903-103028_m0105_implement-canonical-source-validation-and-ci-enforcement.md
- **Source plan**: plans/20260905-165817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150421
- **Related target files**: tests/tools/test_check_docs_structure.py
