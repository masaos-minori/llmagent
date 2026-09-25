## Goal
Move `docs/90_shared_00_document-guide.md` to `docs/40_shared/90_shared_00_document-guide.md` via `git mv`, with no filename or content change, per Plan `plans/20260924-150508_plan.md` REQ-001.

## Scope
- In scope: the single `git mv` of this file into the new `docs/40_shared/` subfolder.
- Out of scope: any content edit to this file (its own outbound `adr/ADR-008-sqlite-4db-separation.md` link fix is a separate row, seq 10, since this document may modify only one file); any other file's move or reference fix.

## Assumptions
- `docs/40_shared/` does not yet exist at the time this row executes; it must be created with `mkdir -p docs/40_shared` before the first `git mv` in this Plan's execution — this Git environment does not auto-create an intermediate destination directory for `git mv` (confirmed empirically during `docsreorg05`'s execution; see Plan Implementation intent).
- `git mv` preserves `git log --follow` history continuity for a same-content rename (standard Git rename-detection behavior).

## Design decisions
A plain `git mv` is used rather than a copy+delete or a content rewrite, since Front Matter and body content require no change for this row — only the file's directory location changes (per `skills/python-design` guidance: prefer the simplest operation that satisfies the Requirement; no design trade-off applies to a pure rename).

## Alternatives considered
N/A: a directory move has exactly one correct implementation (`git mv`) for this row; no alternative approach was considered.

## Implementation
### Target file
`docs/90_shared_00_document-guide.md`

### Procedure
1. Confirm `docs/40_shared/` exists (created once for the whole batch, not per row — see seq 01's own execution as the first row in table order).
2. Run `git mv docs/90_shared_00_document-guide.md docs/40_shared/90_shared_00_document-guide.md`.
3. Confirm the move via `git status --short` (expect an `R` rename line) and `ls docs/40_shared/90_shared_00_document-guide.md`.

### Method
`git mv <source> <destination>` — a single Git-tracked rename; no scripting required.

### Details
- Source: `docs/90_shared_00_document-guide.md` (confirmed present, 3943 bytes, per Plan Implementation Target Files evidence).
- Destination: `docs/40_shared/90_shared_00_document-guide.md`.
- No Front Matter or body edit in this row — `git mv` never alters file content.

## Compatibility considerations
Any bare-filename reference to `90_shared_00_document-guide.md` elsewhere in the repository continues to resolve via `tools/check_docs_structure.py`'s basename-index resolution (`docsreorg01`). Relative-path (`/`-containing) references are handled by separate rows (seq 12: `docs/00_governance/00_index.md`'s 2 links) — not this row.

## Security considerations
N/A: a documentation file rename has no security surface.

## Rollback considerations
Revert via `git mv docs/40_shared/90_shared_00_document-guide.md docs/90_shared_00_document-guide.md` if needed before commit; after commit, `git revert` the commit that performed this move.

## Validation plan
- `git log --follow docs/40_shared/90_shared_00_document-guide.md` shows continuous history through the move (AC-1).
- `ls docs/90_shared_00_document-guide.md` reports not found; `ls docs/40_shared/90_shared_00_document-guide.md` reports found.

## Completion criteria
`docs/40_shared/90_shared_00_document-guide.md` exists with identical content to the pre-move `docs/90_shared_00_document-guide.md`, the old path no longer exists, and the move is recorded as a Git rename.

## Out of scope
Link fixes referencing this file (handled by seq 10, seq 12), and the domain-consistency/`check_schema_drift()` investigation (Plan Design section, out of scope for this Plan entirely).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260924-221341 | 20260924-221341 | |
| 2 | Add or update tests per Validation plan | Completed | 20260924-221341 | 20260924-221341 | N/A: no test code applies to a pure rename; validation is the `git log --follow` + `ls` check above |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260924-221341 | 20260924-221341 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260924-221341 | 20260924-221341 | N/A: this row's own file move IS the documentation change; no further doc update applies |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260923-141137_docsreorg09_move-general-shared-docs-into-new-shared-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-150508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-151506
- **Related target files**: docs/90_shared_00_document-guide.md
