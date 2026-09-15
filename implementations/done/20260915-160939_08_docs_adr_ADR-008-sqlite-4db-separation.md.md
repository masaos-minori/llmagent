## Goal
Remove ADR-008's redundant file/class/config/test list from `## Implementation
Notes` once reconciled into `### Implementation References`, per `REQ-008` —
including correcting a filename typo and adding a missing file found during
adversarial verification — while leaving the WAL/checkpoint mode lines untouched.

## Scope
- In scope: correct References' `scripts/db/helpers.py` (confirmed nonexistent,
  plural) to `scripts/db/helper.py` (singular); add `scripts/db/create_schema.py`
  — `create_schema()` as a new References entry (currently absent from both
  copies); delete the now-reconciled Notes bullets.
- Out of scope: WALモード (line 456) and チェックポイントモード (line 457) — not
  derivable from a file/symbol name, not present anywhere in References, must
  survive as non-list prose in Notes.

## Assumptions
- No pointer line is needed — lines 456-457 survive, keeping the section
  non-empty.
- `SQLiteHelper.__init__()` and `load_vec()` (already correctly cited in
  References, just under the wrong filename) remain attributed to
  `scripts/db/helper.py` once the filename is corrected.

## Design decisions
- `scripts/db/helpers.py` (plural) does not exist in current source; the actual
  file is `scripts/db/helper.py` (singular) — this is a typo present in both
  Notes and References simultaneously, so cross-copy comparison alone would not
  catch it (same category as REQ-005/009/010's findings).
- `create_schema()` lives in its own file, `scripts/db/create_schema.py`, absent
  from both copies' file lists entirely — added as a new entry, not a correction
  of an existing one.

## Alternatives considered
- Leave `helpers.py` as-is since it might be a deliberate alias/symlink —
  confirmed via `ls` that no such file exists at all under either name except the
  singular — no alias exists, this is a straightforward typo.

## Implementation
### Target file
`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   453-458 (with 456-457 as the protected WAL/checkpoint lines) and References at
   551-559.
2. Re-confirm via `ls scripts/db/helpers.py` (expect failure) and
   `ls scripts/db/helper.py` (expect success), and
   `grep -n "^def create_schema" scripts/db/create_schema.py` (expect a match)
   that both corrections are still needed.
3. Correct References' `scripts/db/helpers.py` entry to `scripts/db/helper.py`
   (keep `SQLiteHelper.__init__()`, `load_vec()` unchanged).
4. Add a new References bullet: `scripts/db/create_schema.py` — `create_schema()`.
5. Delete Notes lines 453, 454, 455, 458 (実装ファイル, 主要Class・Function,
   データベーススキーマ, 対応するテスト) — leave lines 456-457 (WALモード,
   チェックポイントモード) untouched, in place.

### Method
Use `Edit` (exact-string replacement) — one call per step 3-5.

### Details
- Preserve lines 456-457 byte-for-byte; verify with a diff after editing.
- Do not delete the データベーススキーマ line (455) until step 3's filename
  correction and step 4's new entry are both confirmed landed in References
  (データベーススキーマ itself was already correctly duplicated, per the Plan's
  evidence — only the file/symbol lines needed correction).

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-008-sqlite-4db-separation.md` if validation fails.

## Validation plan
- `ls scripts/db/helpers.py` (expect failure), `ls scripts/db/helper.py` (expect success), `grep -n "^def create_schema" scripts/db/create_schema.py` (expect match) — re-confirm before editing.
- Manual diff: confirm References cites `helper.py` (not `helpers.py`) and includes `create_schema.py`; confirm Notes retains only lines 456-457.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-008-sqlite-4db-separation.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-008-sqlite-4db-separation.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- References cites `scripts/db/helper.py` (singular) and includes
  `scripts/db/create_schema.py` — `create_schema()`.
- `## Implementation Notes` retains only lines 456-457 plus boilerplate.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Lines 456-457 (WAL mode, checkpoint mode).
- Any other section of ADR-008.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-163018 | Corrected helper.py typo AND corrected create_schema()'s attribution (was wrongly under maintenance.py in References, not merely absent as the procedure assumed - moved to its own create_schema.py entry); deleted reconciled Notes lines; preserved WAL/checkpoint lines |
| 2 | Add or update tests per Validation plan | Completed | 20260915-163018 | 20260915-163018 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-163018 | 20260915-163018 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 14 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-163018 | 20260915-163018 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-008 — correct helper.py typo, add create_schema.py, partial delete preserving WAL/checkpoint lines
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md