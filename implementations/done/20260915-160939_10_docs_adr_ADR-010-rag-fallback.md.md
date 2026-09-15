## Goal
Remove ADR-010's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-010` —
including adding a missing file/symbol found during adversarial verification.

## Scope
- In scope: add `scripts/rag/stages/augment.py` — `AugmentStage.run()` as a new
  References entry (currently absent from both copies); delete the Notes list;
  insert the one-line pointer.
- Out of scope: any other ADR-010 content.

## Assumptions
- The one-line pointer is used verbatim.
- References is otherwise already a superset of Notes (it independently adds
  `RagPipeline._format_chunks()`) — no other correction needed.

## Design decisions
- Notes' 主要Class・Function (line 330) cites `AugmentStage.run()` but never
  lists its containing file (`scripts/rag/stages/augment.py`) in 実装ファイル
  (line 329); References omits it entirely too — confirmed via `grep` that the
  class and method exist at that path. This is a straightforward addition, not a
  correction of an existing wrong entry.

## Alternatives considered
- N/A — this is a simple addition with no competing approach.

## Implementation
### Target file
`docs/adr/ADR-010-rag-fallback.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   329-333 and References at 414-419.
2. Re-confirm via `grep -n "class AugmentStage" -A 15 scripts/rag/stages/augment.py`
   that `run()` still exists there.
3. Add a new References bullet: `scripts/rag/stages/augment.py` —
   `AugmentStage.run()`.
4. Delete the Notes list (実装ファイル / 主要ClassまたはFunction /
   データベーススキーマ / トリガー / 対応するテスト, lines 329-333) — all other
   items already confirmed duplicated or superseded in References.
5. Insert: "See Related Documents > Implementation References for the current
   file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 3-5.

### Details
- Do not alter References' other, unaffected bullets (`pipeline.py`,
  `pipeline_service.py`, `config_loader.py`, `rag.sqlite`, triggers, tests).

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-010-rag-fallback.md` if validation fails.

## Validation plan
- `grep -n "class AugmentStage" -A 15 scripts/rag/stages/augment.py` — confirm `run()` before adding.
- Manual diff: confirm References includes `AugmentStage.run()`/`augment.py`; confirm Notes list removed.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-010-rag-fallback.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-010-rag-fallback.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References includes `scripts/rag/stages/augment.py` — `AugmentStage.run()`.
- `## Implementation Notes` contains only the one-line pointer plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Any other section of ADR-010.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163148 | Added missing AugmentStage.run()/augment.py entry to References; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163148 | 20260915-163148 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163148 | 20260915-163148 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 9 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163148 | 20260915-163148 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-010 — add missing AugmentStage.run()/augment.py entry, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-010-rag-fallback.md