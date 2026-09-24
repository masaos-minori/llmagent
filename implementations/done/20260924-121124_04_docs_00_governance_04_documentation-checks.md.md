## Goal
Relocate `docs/00_governance_04_documentation-checks.md` to
`docs/00_governance/00_governance_04_documentation-checks.md` via `git mv`, with no
filename or content change, implementing `REQ-001`.

## Scope
In scope: the single `git mv` of this file. Out of scope: any content edit, any other
file's move (see the Plan's other 7 implementation procedure documents for those rows).

## Assumptions
- `git mv` preserves `git log --follow` history continuity for this same-content move.
- No tool hardcodes a path to this specific file — it is read only via doc-guide
  cross-references and prose docstring citations (e.g. in `tools/check_compat_shims.py`,
  `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py`,
  `tools/check_adr_reference.py`), all of which are comment/prose references, not
  hardcoded resolvable paths — none require code changes.

## Design decisions
None beyond the mechanical move itself.

## Alternatives considered
- Plain filesystem `mv` + `git add`/`git rm`: rejected — the Plan's Constraints require
  `git mv` only.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Confirm the destination directory `docs/00_governance/` exists (created during seq
   01's cycle in this same pass; `mkdir -p docs/00_governance` if resuming out of order
   — this Git version does not auto-create an intermediate directory for `git mv`'s
   destination, verified during seq 01's cycle).
2. Run `git mv docs/00_governance_04_documentation-checks.md docs/00_governance/00_governance_04_documentation-checks.md`.
3. Confirm the destination file exists, the source path no longer exists, and `git
   status` shows the change staged as a rename (status letter R).

### Method
Single Git CLI invocation; no code change, no content diff expected between source and
destination blob.

### Details
- Do not pass any other flag to `git mv` beyond the two paths.
- This file has zero entries in `tests/tools/test_check_docs_quality.py`'s
  `EXPECTED_WITHIN_FILE_PAIRS` frozenset — seq 06's procedure document does not touch
  any key referencing this file.

## Compatibility considerations
Bare-filename cross-references to this file (including the prose docstring citations
listed under Assumptions above) continue to resolve after the move via
`tools/check_docs_structure.py`'s basename index; the docstring citations are plain text
comments, not resolved paths, so they are unaffected by the move either way.

## Security considerations
N/A: a file relocation with no content change carries no security-relevant surface.

## Rollback considerations
Revert with `git mv docs/00_governance/00_governance_04_documentation-checks.md
docs/00_governance_04_documentation-checks.md`, or `git revert` the commit containing
this move if already committed.

## Validation plan
- `git log --follow -- docs/00_governance/00_governance_04_documentation-checks.md`
  shows continuous history through the move (Plan `AC-1`).
- Deferred to Phase 3: `uv run python tools/check_docs_structure.py "docs/**/*.md"
  --schema schemas/doc_front_matter.json` and `uv run python -m tools.check_docs_quality`
  (Plan `AC-3`, `AC-4`).

## Completion criteria
`docs/00_governance/00_governance_04_documentation-checks.md` exists;
`docs/00_governance_04_documentation-checks.md` no longer exists at the flat path; the
move is recorded as a Git rename.

## Out of scope
Any content edit to this file; any change to the other 4 moved files or any tooling
file (covered by this Plan's other implementation procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git mv docs/00_governance_04_documentation-checks.md docs/00_governance/00_governance_04_documentation-checks.md` | Completed | 20260924-122332 | 20260924-122332 | git mv succeeded as staged rename (git status: R). Corrected Procedure step 1: this Git version does not auto-create the destination directory for git mv -- required mkdir -p docs/00_governance first (adversarial verification finding, procedure corrected). |
| 2 | N/A: no test to add for a content-identical move | Completed | 20260924-122332 | 20260924-122332 | N/A: content-identical move, no test to add. |
| 3 | Confirm `git log --follow` continuity and staged rename status | Completed | 20260924-122332 | 20260924-122332 | git status confirms staged rename (R). Full git log --follow history continuity verification deferred until this change is committed (not part of this code-implementation cycle's scope per repository commit policy). |
| 4 | N/A: no documentation update beyond the move itself | Completed | 20260924-122332 | 20260924-122332 | N/A: no documentation update beyond the move itself; deferred cross-file validation runs once in Phase 3 (seq 06-08 remaining). |

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
- **Requirement ID**: `REQ-001` (git mv the 5 governance files into `docs/00_governance/`)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: docs/00_governance_04_documentation-checks.md