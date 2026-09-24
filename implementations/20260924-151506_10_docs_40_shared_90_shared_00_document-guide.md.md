## Goal
Fix `docs/40_shared/90_shared_00_document-guide.md`'s outbound Markdown link to `docs/adr/ADR-008-sqlite-4db-separation.md` — currently `adr/ADR-008-sqlite-4db-separation.md` — which breaks once this file moves one directory level deeper (seq 01), per Plan `plans/20260924-150508_plan.md` REQ-002.

## Scope
- In scope: rewriting the single Markdown link `[...](adr/ADR-008-sqlite-4db-separation.md)` to `[...](../adr/ADR-008-sqlite-4db-separation.md)` at line 94 (pre-move line number; confirmed via `grep -n` against the pre-move file during Plan creation — re-verify post-move via `rg` before editing, since seq 01's move may shift no line numbers but the file path itself changes).
- Out of scope: the seq 01 move itself (a prerequisite for this row, executed first per table order); the backtick-quoted prose citation of `docs/adr/ADR-008-sqlite-4db-separation.md` (confirmed non-link, out of scope per Plan Design).

## Assumptions
- Seq 01 (the `git mv` of this file into `docs/40_shared/`) has already executed by the time this row runs, since `Implementation Target Files` table order places seq 01 before seq 10.
- The link target `docs/adr/ADR-008-sqlite-4db-separation.md` itself does not move as part of this Plan (only `docsreorg09`'s own 9 general-shared files move) — so `../adr/ADR-008-sqlite-4db-separation.md` is the correct post-move relative path from `docs/40_shared/`.

## Design decisions
A one-line relative-path prefix fix (`adr/...` → `../adr/...`) is the minimal correct change — content and anchor text are unchanged, only the path depth adjusts to account for the new `40_shared/` directory level.

## Alternatives considered
Converting to an absolute-from-docs-root link was considered but rejected: this repository's existing convention (confirmed across `docsreorg05`-`08`'s own link fixes) uses relative paths for intra-`docs/` links, and `tools/check_docs_structure.py`'s link checker resolves relative paths via `(path.parent / target).resolve()` — a relative link is the conventional and directly-verifiable form.

## Implementation
### Target file
`docs/40_shared/90_shared_00_document-guide.md`

### Procedure
1. Confirm seq 01's move has completed (`ls docs/40_shared/90_shared_00_document-guide.md`).
2. Locate the link with `rg -n '\]\([^)]*adr/ADR-008-sqlite-4db-separation\.md(#[^)]*)?\)' docs/40_shared/90_shared_00_document-guide.md`.
3. Edit the link target from `adr/ADR-008-sqlite-4db-separation.md` to `../adr/ADR-008-sqlite-4db-separation.md`, preserving the link text exactly.
4. Re-run the same `rg` command to confirm exactly one match remains, now with the `../` prefix.

### Method
Single-line text substitution via Edit — no scripted rewrite needed for one occurrence.

### Details
- Confirmed (pre-move) via `grep -n "adr/ADR-008-sqlite-4db-separation.md" docs/90_shared_00_document-guide.md`: 2 total substring matches, of which only 1 (line 94) is an actual Markdown link `[...](adr/ADR-008-sqlite-4db-separation.md)`; the other (line 63) is a backtick-quoted prose citation `` `docs/adr/ADR-008-sqlite-4db-separation.md` ``, not a link — confirmed out of scope.
- Only the link's target path changes; the link's display text is untouched.

## Compatibility considerations
After this fix, `tools/check_docs_structure.py`'s link checker resolves this link correctly via `(path.parent / target).resolve()` from the new `docs/40_shared/` location.

## Security considerations
N/A: a documentation link-path edit has no security surface.

## Rollback considerations
Revert via Edit back to `adr/ADR-008-sqlite-4db-separation.md` if needed before commit; after commit, `git revert` the commit that performed this fix.

## Validation plan
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` reports no broken-link finding for this file (AC-3).
- `rg -n '\]\([^)]*adr/ADR-008-sqlite-4db-separation\.md(#[^)]*)?\)' docs/40_shared/90_shared_00_document-guide.md` shows the link now reads `../adr/ADR-008-sqlite-4db-separation.md`.

## Completion criteria
The Markdown link at the former line 94 resolves to `docs/adr/ADR-008-sqlite-4db-separation.md` from `docs/40_shared/90_shared_00_document-guide.md`'s new location, verified via `tools/check_docs_structure.py`.

## Out of scope
Seq 01 (the file's own move, a prerequisite); the non-link prose citation at the former line 63.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test code applies to a docs link fix; validation is `tools/check_docs_structure.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's own edit IS the documentation change |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260923-141137_docsreorg09_move-general-shared-docs-into-new-shared-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-150508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-151506
- **Related target files**: docs/40_shared/90_shared_00_document-guide.md
