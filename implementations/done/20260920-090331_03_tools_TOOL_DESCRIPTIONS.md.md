## Goal

Correct both `tools/TOOL_DESCRIPTIONS.md` entries for `check_docs_content_policy.py`
to list the module's full, current check set — 11 existing categories plus the four
this pass adds — instead of only the original five `skills/DESIGN.md`-named
categories (satisfies `REQ-005`).

## Scope

- In scope: the two existing `check_docs_content_policy.py` rows in
  `tools/TOOL_DESCRIPTIONS.md` (current lines 21 and 72).
- Out of scope: any other row in either table; the file's overall structure or
  module count header (`## 一覧 (37モジュール)`) — this change does not add or
  remove a tool, only corrects one existing tool's description.

## Assumptions

- `implementations/20260920-090331_01_tools_check_docs_content_policy.py.md` (seq
  01, this same pass) has already added the four new check functions — this
  document's corrected description text names all 15 resulting categories
  (11 existing + 4 new) as already-present, current behavior, not as a future
  change.

## Design decisions

- Update both entries in the same pass rather than only one, since both already
  describe the same module and both are already stale relative to its actual
  11-function (now 15-function) check set — leaving one corrected and one stale
  would reintroduce the same kind of drift this change fixes.
- Preserve each entry's existing column position, surrounding row order, and
  non-category content (report-only/Warning operation note, `rules/env.md`
  out-of-scope note, `GV-021` reference) — only the category list itself is
  corrected.

## Alternatives considered

- Shortening the description to a generic "detects multiple implementation-detail
  categories, see module docstring for the full list" instead of enumerating all
  15: rejected — every other entry in this file (e.g. `check_adr_invariant_matrix.py`,
  `check_workitem_traceability.py`) enumerates its actual check categories inline
  rather than deferring to source; matching that existing convention keeps this
  file usable without opening the source module.

## Implementation

### Target file

tools/TOOL_DESCRIPTIONS.md

### Procedure

1. Replace the short "主な目的" cell for `check_docs_content_policy.py` in the
   first table (current line 21).
2. Replace the detailed "主なチェック内容" cell for `check_docs_content_policy.py`
   in the second table (current line 72).

### Method

Line 21 (first table, "## 一覧" — columns ファイル/カテゴリ/主な目的):
```
| `check_docs_content_policy.py` | ドキュメントポリシー | `skills/DESIGN.md` Docs content policy — remove / Avoid implementation-reference duplication に基づく実装詳細コンテンツ違反検出(15カテゴリ) |
```

Line 72 (second table — columns ファイル/対象ドメイン/主なチェック内容; 対象ドメイン列は変更しない):
```
| `check_docs_content_policy.py` | `docs/*.md` 全体(`docs/adr/`等サブディレクトリ含む再帰スキャン) | `skills/DESIGN.md`の「Docs content policy — remove」等が定める実装詳細カテゴリ15種(ASCIIファイルツリー、ツリー/テーブルに埋め込まれた1行説明、クラス/関数/メソッドのインデックス表、実装箇所マッピング、リテラルなポート番号、テーブル外のデフォルト値再掲、Field/Type/Defaultテーブル、config-fileインベントリ対応表、CLIコマンド列挙、環境構築コマンド列、DDL/スキーマブロック、TypedDict/DTOフィールド表、CLI引数表、例外処理表、JSON全文例)を検出する。report-only(Warning)運用、`rules/env.md`は`docs/*.md`外のためスキャン対象外(`GV-021`) |
```

### Details

- Both replacements are single-line, single-cell edits — no other cell in either
  row changes.
- The second table's "対象ドメイン" (target domain) cell is unchanged — the scan
  scope itself does not change, only the count and naming of categories detected
  within that scope.

## Compatibility considerations

Documentation-only change with no behavioral effect — this file is descriptive
metadata about `tools/`, not executable code, and is not imported by any script
(confirmed: `tools/TOOL_DESCRIPTIONS.md` is Markdown, not Python).

## Security considerations

N/A: documentation-only change, no code or external input involved.

## Rollback considerations

Revert this file's diff. No other file depends on this file's content
programmatically — `tools/check_tool_descriptions_sync.py` reads it to verify
sync (see Validation plan), but a revert only returns that check to its prior
(also-passing, pre-this-pass) description drift, not a new failure.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` — confirm the module list
  and this file's entries remain in sync (this checker validates file/entry
  correspondence, not description accuracy, but must still pass after this edit).
- Manual review: confirm the corrected description text lists all 15 categories
  and matches `tools/check_docs_content_policy.py`'s actual function names after
  seq 01 (this same pass) is applied.

## Completion criteria

- Both `check_docs_content_policy.py` entries in `tools/TOOL_DESCRIPTIONS.md` list
  the module's full, current 15-category check set.
- `uv run python tools/check_tool_descriptions_sync.py` passes.

## Out of scope

- Any other tool's entry in either table.
- The actual detection-function implementation (covered by seq 01, this same
  pass) or its tests (seq 02).
- The `routing.md` "When to run which tool" registration (covered by seq 04, this
  same pass).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-092000 | 20260920-092000 | Both lines (21, 72) confirmed unchanged before editing, then replaced exactly as specified. |
| 2 | Add or update tests per Validation plan | Completed | 20260920-092000 | 20260920-092000 | N/A: documentation entry, no test applicable |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-092000 | 20260920-092000 | `uv run python tools/check_tool_descriptions_sync.py`: No issues found. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-092000 | 20260920-092000 | This document's Implementation step is itself the documentation update |

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
- **Requirement ID**: `REQ-005` (correct the two stale `check_docs_content_policy.py` entries)
- **Source issue**: issues/done/20260920-084638_docreftool01_add-a-docs-checker-for-implementation-reference-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-085652_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-090331
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
