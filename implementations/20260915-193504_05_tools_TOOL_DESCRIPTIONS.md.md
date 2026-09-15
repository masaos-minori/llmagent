## Goal
Add `tools/check_adr_structure.py` to both `tools/TOOL_DESCRIPTIONS.md`
tables (`## 一覧` summary table and the detailed table under `## ドメイン別
ドキュメント整合性チェッカー`), per `REQ-007`, matching `check_adr_reference.py`'s
row format/detail level, and update the module count in the `## 一覧` heading.

## Scope
- In scope: one new row in each of the two tables; the `## 一覧 (Nモジュール)`
  heading's module count incremented by 1.
- Out of scope: `check_tool_descriptions_sync.py` itself — this row's own
  addition is what keeps that checker's drift detection passing, not a
  change to the checker.

## Assumptions
- `## 一覧`'s current heading reads `## 一覧 (36モジュール)` (confirmed via this
  pass's grep) — becomes `## 一覧 (37モジュール)` once `check_adr_structure.py`
  is added, since this is a genuinely new file in `tools/` (sibling procedure
  01), not a rename.
- `check_adr_reference.py`'s two rows are the exact format precedent
  (confirmed via this pass's grep):
  - Summary table: `| \`check_adr_reference.py\` | ADR関連 | ADR Invariant
    Verification Matrixのソースファイル参照検証 |`
  - Detailed table: `| \`check_adr_reference.py\` | \`docs/adr-index.md\`,
    \`scripts/**/*.py\` | ADR Invariant Verification Matrixが... |`

## Design decisions
- Summary table row (category `ADR関連`, inserted alphabetically among the
  existing `ADR関連` rows — after `check_adr_reference.py`, before
  `check_known_deviation_sync.py`, per the existing rows' apparent
  alphabetical-within-category ordering confirmed at line 15-25):
  `| \`check_adr_structure.py\` | ADR関連 | ADR構造（Known Deviations見出し・
  Implementation Notes/References整合性）検証 |`
- Detailed table row (inserted immediately after `check_adr_reference.py`'s
  row at line 63, within `## ドメイン別ドキュメント整合性チェッカー`):
  `| \`check_adr_structure.py\` | \`docs/adr/*.md\` | 各ADRについて(a)\`##
  Known Deviations\`見出しの存在(欠落時はError)、(b)\`## Implementation
  Notes\`と\`### Implementation References\`間のscripts/tests配下パス引用の
  ドリフト(Notes側にのみ存在する場合はWarning、Notes側に該当パス引用が0件のADR
  は本チェック対象外)を検証する。読み取り専用。\`--format json\`で機械可読形式
  の出力にも対応 |`

## Alternatives considered
- Place the detailed-table row before `check_adr_reference.py` instead of
  after — rejected: no stated ordering rule beyond apparent insertion-order/
  grouping-by-related-check, and placing the new, narrower-scoped check
  immediately after its closest sibling keeps related checks visually
  adjacent.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Re-verify (Step 3a) the `## 一覧` heading's current count and both
   precedent rows' exact text are unchanged before editing.
2. Update `## 一覧 (36モジュール)` → `## 一覧 (37モジュール)`.
3. Insert the new summary-table row after `check_adr_reference.py`'s row.
4. Insert the new detailed-table row after `check_adr_reference.py`'s row
   under `## ドメイン別ドキュメント整合性チェッカー`.

### Method
`Edit` tool, three separate anchored edits (heading count, summary row,
detailed row) to keep each change independently reviewable.

### Details
See Design decisions for exact row text.

## Compatibility considerations
- `tools/check_tool_descriptions_sync.py` (pre-commit hook
  `tool-descriptions-sync`) compares `tools/TOOL_DESCRIPTIONS.md`'s listed
  filenames against actual `tools/*.py` files — this row's addition is what
  keeps that hook passing once sibling procedure 01's new script exists;
  omitting this row would make that hook fail (unlisted addition).

## Security considerations
N/A: documentation change only.

## Rollback considerations
Revert by removing the added rows and reverting the count; no other file
depends on this row's presence except the sync-check hook's passing state.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — passes (zero
  drift) once both this row and sibling procedure 01's script exist.
- `uv run python tools/check_docs_quality.py tools/TOOL_DESCRIPTIONS.md` — clean.
- Manual count check: `grep -c '^| \`check_' tools/TOOL_DESCRIPTIONS.md`'s
  `## 一覧` section row count matches the stated `(37モジュール)`.

## Completion criteria
- Both rows present, matching precedent format/detail level.
- `check_tool_descriptions_sync.py` passes.

## Out of scope
- `check_tool_descriptions_sync.py` itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-195355 | 20260915-195355 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-195355 | 20260915-195355 | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-195355 | 20260915-195355 | Documentation change — validated via `check_tool_descriptions_sync.py`/`check_docs_quality.py` check_tool_descriptions_sync.py: passes (exit 0). check_docs_quality.py: 5 pre-existing ERROR findings confirmed unchanged via git stash (same 5 malformed-table findings, just shifted +2 lines by this edit's insertions) -- unrelated to this change, out of REQ-007 scope. Manual count check found a genuine PRE-EXISTING drift: baseline (pre-edit) actually had 35 data rows under a '36モジュール' heading (off by 1 already); this edit added 1 row and incremented the heading 36->37, preserving the same magnitude of pre-existing drift rather than fixing or worsening it -- reconciling it is out of REQ-007's scope (not requested), noted here per Adversarial Verification discipline |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-195355 | 20260915-195355 | This row IS the documentation update This row IS the documentation update |

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
- **Requirement ID**: REQ-007 — register check_adr_structure.py in both TOOL_DESCRIPTIONS.md tables
- **Source issue**: issues/done/20260914-124634_docqa05_adr-implementation-notes-lint-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-192743_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-193504
- **Related target files**: tools/TOOL_DESCRIPTIONS.md