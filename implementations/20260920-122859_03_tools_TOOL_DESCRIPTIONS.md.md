## Goal
Update `tools/TOOL_DESCRIPTIONS.md`'s two `check_docs_content_policy.py`
entries (REQ-003) from "15カテゴリ"/"実装詳細カテゴリ15種" to
"16カテゴリ"/"実装詳細カテゴリ16種", naming the new
code-fallback-vs-operational-value comparison category in line 72's
enumeration.

## Scope
In scope: exactly the 2 confirmed lines (21, 72). Out of scope: any other
`tools/TOOL_DESCRIPTIONS.md` entry, including any other tool's row.

## Assumptions
Both sibling implementation procedures (`seq` 01: the check function;
`seq` 02: its unit tests) have already landed before this row is
implemented, per table order (this is `seq` 03, the last row).

## Design decisions
Append the new category name to line 72's parenthetical enumeration in the
same style as the 15 existing category names (a short Japanese noun
phrase), consistent with how the enumeration was previously extended (per
this file's own history — the entry already reads "実装詳細カテゴリ15種"
as a count that must move in lockstep with the enumeration's actual item
count). Use "コードのフォールバック値と運用値の比較記述" (code
fallback-value vs. operational-value comparison description) as the new
category's name, matching the existing entries' terse, noun-phrase style
(e.g. "リテラルなポート番号", "テーブル外のデフォルト値再掲").

## Alternatives considered
A longer, more explanatory category name — rejected: every existing
category name in this enumeration is a short noun phrase (typically
4-12 characters), not a sentence; matching that established terseness
keeps the enumeration internally consistent.

## Implementation
### Target file
tools/TOOL_DESCRIPTIONS.md

### Procedure
1. Line 21: change `実装詳細コンテンツ違反検出(15カテゴリ)` to
   `実装詳細コンテンツ違反検出(16カテゴリ)`.
2. Line 72: change `実装詳細カテゴリ15種(` to `実装詳細カテゴリ16種(`,
   and append `、コードのフォールバック値と運用値の比較記述` immediately
   before the closing `)` of the enumeration (after `JSON全文例`, i.e. the
   new category becomes the 16th and final item in the parenthetical list).

### Method
Two separate `Edit` calls (old_string/new_string), one per line — each is
independently revertable.

### Details
Do not alter any other part of either line (the tool-name column, the
`skills/DESIGN.md` cross-reference, the `report-only(Warning)運用` /
`rules/env.md` / `GV-021` trailing clause on line 72) — only the category
count and the enumeration's item list change.

## Compatibility considerations
Documentation-only; no code or CLI behavior change. No compatibility
impact.

## Security considerations
N/A: documentation content change only.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit
reverting each Edit — no data migration or state change is involved.

## Validation plan
Direct `Read` of both edited lines after the change, confirming: line 21
states "16カテゴリ"; line 72 states "16種" and its enumeration includes
the new category name as the 16th item, with no other text on either line
altered.

## Completion criteria
Both lines state "16カテゴリ"/"16種"; line 72 names the new category;
`tools/check_docs_content_policy.py`'s actual `check_*` count (confirmed 16
after the sibling `seq` 01 procedure lands) matches the stated count.

## Out of scope
- The `check_code_fallback_value_comparison` function and its tests —
  tracked in the two sibling procedure documents (REQ-001, REQ-002).
- Any other `tools/TOOL_DESCRIPTIONS.md` row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-134553 | 20260920-134553 | Both lines confirmed unchanged at 15カテゴリ/15種 before edit. Applied both Edits. |
| 2 | N/A: no test suite applies to a Markdown documentation-count change | Completed | 20260920-134553 | 20260920-134553 | N/A: no test suite applies to a Markdown documentation-count change. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-134553 | 20260920-134553 | Direct Read confirms both lines now state 16カテゴリ/16種; new category named as 16th item; actual check_* count in tools/check_docs_content_policy.py confirmed 16 (matches). |
| 4 | N/A: no further documentation update needed beyond this file itself | Completed | 20260920-134553 | 20260920-134553 | N/A: no further documentation update needed beyond this file itself. |

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
- **Requirement ID**: `REQ-003` — update TOOL_DESCRIPTIONS.md category count
- **Source issue**: issues/20260920-102200_doccfgtool01_detect-code-fallback-vs-operational-value-duplication-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-114319_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-122859
- **Related target files**: tools/TOOL_DESCRIPTIONS.md