## Goal
Fix `docs/40_shared/90_shared_01_overview.md`'s outbound Markdown link to `docs/adr/ADR-008-sqlite-4db-separation.md` — currently `adr/ADR-008-sqlite-4db-separation.md` — which breaks once this file moves one directory level deeper (seq 02), per Plan `plans/20260924-150508_plan.md` REQ-002.

## Scope
- In scope: rewriting the single Markdown link `[ADR-008](adr/ADR-008-sqlite-4db-separation.md)` to `[ADR-008](../adr/ADR-008-sqlite-4db-separation.md)` at line 125 (pre-move line number, confirmed via `grep -n` during Plan creation).
- Out of scope: the seq 02 move itself (a prerequisite for this row, executed first per table order).

## Assumptions
- Seq 02 (the `git mv` of this file into `docs/40_shared/`) has already executed by the time this row runs.
- The link target `docs/adr/ADR-008-sqlite-4db-separation.md` itself does not move as part of this Plan.

## Design decisions
A one-line relative-path prefix fix (`adr/...` → `../adr/...`) is the minimal correct change.

## Alternatives considered
Same as seq 10: relative-path fix preferred over an absolute-from-docs-root link, per this repository's existing convention.

## Implementation
### Target file
`docs/40_shared/90_shared_01_overview.md`

### Procedure
1. Confirm seq 02's move has completed (`ls docs/40_shared/90_shared_01_overview.md`).
2. Locate the link with `rg -n '\]\([^)]*adr/ADR-008-sqlite-4db-separation\.md(#[^)]*)?\)' docs/40_shared/90_shared_01_overview.md`.
3. Edit the link target from `adr/ADR-008-sqlite-4db-separation.md` to `../adr/ADR-008-sqlite-4db-separation.md`, preserving the link text (`ADR-008`) exactly.
4. Re-run the same `rg` command to confirm exactly one match remains, now with the `../` prefix.

### Method
Single-line text substitution via Edit.

### Details
- Confirmed (pre-move) via `grep -n "adr/ADR-008-sqlite-4db-separation.md" docs/90_shared_01_overview.md`: exactly 1 match (line 125), the Markdown link `[ADR-008](adr/ADR-008-sqlite-4db-separation.md)`.
- Only the link's target path changes; the link text `ADR-008` is untouched.

## Compatibility considerations
After this fix, `tools/check_docs_structure.py`'s link checker resolves this link correctly from the new `docs/40_shared/` location.

## Security considerations
N/A: a documentation link-path edit has no security surface.

## Rollback considerations
Revert via Edit back to `adr/ADR-008-sqlite-4db-separation.md` if needed before commit; after commit, `git revert` the commit that performed this fix.

## Validation plan
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json` reports no broken-link finding for this file (AC-3).
- `rg -n '\]\([^)]*adr/ADR-008-sqlite-4db-separation\.md(#[^)]*)?\)' docs/40_shared/90_shared_01_overview.md` shows the link now reads `../adr/ADR-008-sqlite-4db-separation.md`.

## Completion criteria
The Markdown link at the former line 125 resolves to `docs/adr/ADR-008-sqlite-4db-separation.md` from `docs/40_shared/90_shared_01_overview.md`'s new location, verified via `tools/check_docs_structure.py`.

## Out of scope
Seq 02 (the file's own move, a prerequisite).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260925-072954 | 20260925-072954 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260925-072957 | 20260925-072957 | N/A: no test code applies to a docs link fix; validation is `tools/check_docs_structure.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260925-073001 | 20260925-073001 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260925-073004 | 20260925-073004 | N/A: this row's own edit IS the documentation change |

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
- **Related target files**: docs/40_shared/90_shared_01_overview.md