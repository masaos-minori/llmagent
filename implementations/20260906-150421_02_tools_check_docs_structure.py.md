## Goal
Add a Unique ADR ID check to `tools/check_docs_structure.py`, implementing the
already-tracked-but-"Missing" `GV-003`: fail on duplicate ADR identifiers across
`docs/adr/*.md` (REQ-004).

## Scope
- In scope: one new function performing a cross-file duplicate-ADR-ID check, plus
  wiring it into `main()`'s validation loop.
- Out of scope: any other existing `check_*` function in this file (all per-file,
  confirmed unaffected); `tools/check_canonical_source_conflicts.py`'s own
  `CANONICAL-007` re-emission of this check's result — tracked in that Plan's row 1
  (`implementations/20260906-150421_01_tools_check_canonical_source_conflicts.py.md`),
  not this row.

## Assumptions
- Confirmed via `ls docs/adr/`: current ADR IDs are `ADR-001` through `ADR-010` and
  `ADR-012` (`ADR-011` absent — a pre-existing numbering gap, not a duplicate; out of
  scope for this check, which only detects duplicates, not gaps) — all currently
  unique, so this new check currently finds nothing to report against the real
  corpus (expected: exits 0 baseline).
- ADR filenames follow `ADR-{NNN}-*.md` (confirmed via `ls`); the ID is the
  `ADR-{NNN}` prefix, extracted from the filename, not re-parsed from the `# ADR-{NNN}:
  ...` H1 heading — filenames are the simpler, already-unique-by-convention source of
  truth to check against itself.

## Design decisions
- Implement as a new module-level function, e.g. `check_unique_adr_ids(adr_dir: Path)
  -> list[str]`, called once in `main()` (not per-file via `validate_file()`) — this
  is a cross-file check (compares all ADR filenames against each other), structurally
  different from every existing `check_*` function in this file, which validates one
  file's own content in isolation. Wiring it as a one-time call after the main
  per-file loop (or before it) avoids forcing this file's existing per-file
  architecture to become stateful.
- Extract the ID via a simple regex on the filename (`^ADR-(\d+)-`) rather than
  parsing the H1 heading — cheaper and avoids depending on the H1 format staying
  exactly `# ADR-{NNN}: ...` (confirmed via `rg` this cycle: all 11 current ADR files'
  H1 lines already start with `# ADR-{NNN}:`, but the filename is enforced by the
  glob pattern itself, so it is the more robust anchor).

## Alternatives considered
- Parse the H1 heading's `ADR-{NNN}` prefix instead of the filename: rejected — the
  filename is already the canonical identifier per this repository's own naming
  convention (`ADR-{NNN}-*.md`), and using it avoids a dependency on H1 text format
  drift.

## Implementation
### Target file
`tools/check_docs_structure.py`

### Procedure
1. Add `check_unique_adr_ids(files: list[Path]) -> list[str]`: group the given ADR
   file paths by their extracted `ADR-{NNN}` ID (regex on filename stem); for any ID
   with more than one file, emit an error string naming the ID and the conflicting
   filenames.
2. In `main()`, when the resolved `files` set includes any path under `docs/adr/`
   (or when the caller explicitly targets `docs/adr/*.md`), call this new function
   once against that subset and report its errors alongside the existing per-file
   issues, incrementing the same `total_issues` counter used by the existing loop.
3. Confirm the new check's error format matches this file's existing convention
   (`str(path)`-prefixed issue lines, consistent with `check_h1_count`/
   `check_front_matter`'s existing string format) so
   `tools/check_canonical_source_conflicts.py`'s planned `CANONICAL-007` re-emission
   (row 1, out of this row's scope) can parse or forward it consistently.

### Method
Confirmed this cycle (2026-09-06) via `ls docs/adr/`: 11 files, IDs `ADR-001`
through `ADR-010` plus `ADR-012` (`ADR-011` absent, a gap not a duplicate), all
unique. Confirmed via direct read of `tools/check_docs_structure.py` (`validate_file()`,
lines 176-193; `main()`, lines 196+): every existing `check_*` function is per-file;
none currently performs a cross-file comparison — this row's function is the first
of that kind in this file.

### Details
No change to any existing `check_*` function or to `validate_file()`'s own signature.

## Compatibility considerations
Additive-only: existing per-file checks and their call sites are unchanged. Any
caller invoking this tool against `docs/adr/*.md` will now also receive this new
check's findings (currently zero, since no duplicate exists).

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `tools/check_canonical_source_conflicts.py`'s
row 1 (`CANONICAL-007` wiring) finds the error-string format needs adjusting —
low risk, since the new function's output only feeds that one consumer plus this
tool's own CLI output.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_structure.py -v` (seq 04 adds the
  duplicate-ADR-ID test case).
- `uv run python tools/check_docs_structure.py docs/adr/*.md` — exits 0 against the
  current, duplicate-free corpus (baseline, confirmed this cycle).
- `uv run mypy tools/check_docs_structure.py`.

## Completion criteria
- A duplicate ADR ID across `docs/adr/*.md` produces a reported error.
- The current, duplicate-free corpus produces no new finding.
- `GV-003`'s status can be updated to "Existing" once this lands (tracked in seq 06,
  gated on CI wiring per that Plan's own REQ-011 ordering).

## Out of scope
- `tools/check_canonical_source_conflicts.py`'s `CANONICAL-007` re-emission —
  tracked in seq 01.
- Any other `check_*` function in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Completed | — | — | |
| 2 | Read the current implementation procedure file | Completed | — | — | |
| 3 | Implement the feature and pass code validation | Completed | — | — | Added check_unique_adr_ids() + main() wiring; mypy/ruff OK |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | 12 existing tests pass |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | N/A | — | — | No docs files matched |
| 6 | Validate documentation updates | N/A | — | — | No documentation changes to validate |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260903-103028_m0105_implement-canonical-source-validation-and-ci-enforcement.md
- **Source plan**: plans/20260905-165817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150421
- **Related target files**: tools/check_docs_structure.py
