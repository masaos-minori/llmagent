# Implementation Procedure: 01_overview-files-03-scripts-part1.md

## Goal

Add `repository_gateway.py` as an explicit row in the `scripts/agent/` responsibility
table in `docs/01_overview-files-03-scripts-part1.md`, so the write-boundary/policy-
enforcement responsibility is discoverable from the table, not only from the existing
"変更時の注意点" bullet that references it in passing.

## Scope

- In scope: one new table row in the "エージェント REPL パッケージ (`scripts/agent/`)"
  responsibility table (lines 27-49 of the current file).
- Out of scope: modifying source code; modifying any other table or section; modifying
  `01_overview-files-03-scripts-part2.md`/`part3.md`/etc. (part3 is handled by a separate
  procedure document).

## Assumptions

- `repository_gateway.py` is the enforcement boundary for repository mutations (policy
  check, execution, audit) — stated in the source plan (`plans/20260803-141200_plan.md`,
  assumption 1) and corroborated by the existing caution bullet at line 69 of the target
  file ("ツール承認フローの変更時は `tool_approval.py` と `repository_gateway.py` の両方を確認").
- The file `scripts/agent/repository_gateway.py` exists (not verified by reading its
  contents in this document-only phase; verification is left to the implementation step).

## Design decisions

- Add `repository_gateway.py` as its own responsibility row rather than folding it into
  an existing row (e.g. "ツール実行"), because its responsibility (write-boundary
  enforcement across policy/execution/audit) is distinct from the existing rows and
  matches the plan's exact wording: 責務 = "書き込み境界 (リポジトリ操作のポリシーチェック・実行・監査)".
- Preserve the existing table's row ordering convention (roughly execution-flow order);
  place the new row near "ツール実行" / "ツールガード" / "ツール監査" rows since it is
  conceptually adjacent (write-boundary sits alongside tool execution and audit).

## Alternatives considered

- Folding `repository_gateway.py` into the existing "ツール実行" row family — rejected,
  since it would blur a distinct responsibility (write-boundary enforcement) that the
  plan explicitly calls out with its own description string.
- Adding a new caution bullet instead of a table row — rejected: the caution bullet
  already exists (line 69); the plan's gap is specifically that the file is missing from
  the responsibility *table*.

## Implementation

### Target file

`docs/01_overview-files-03-scripts-part1.md`

### Procedure

1. Open `docs/01_overview-files-03-scripts-part1.md`.
2. Locate the "エージェント REPL パッケージ (`scripts/agent/`)" table (starts at line 27,
   header `| 責務 | ファイル群 |`).
3. Insert a new row: `| 書き込み境界 | \`repository_gateway.py\` |` with description text
   "書き込み境界 (リポジトリ操作のポリシーチェック・実行・監査)" reflected either as the 責務
   cell value or as adjacent explanatory text, matching the table's existing terse style
   (責務 cell holds the short label; keep it consistent with e.g. "ツールガード" style,
   single short noun phrase).
4. Do not modify any other row or the "メモリサブパッケージ" table below it.
5. Do not modify the existing "変更時の注意点" section (lines 66-70) — it already
   references `repository_gateway.py` correctly; no changes needed there for this item.

### Method

Direct manual Markdown edit (single table-row insertion). No script or automation
required — this is a one-line, one-file change.

### Details

- Current table content (lines 27-49) lists responsibility rows such as "ツール実行",
  "ツールガード", "ツール監査" — the new row should sit among these since write-boundary
  enforcement is part of the same execution-time concern family.
- File does not currently list `repository_gateway.py` in the table (confirmed by grep:
  only the caution bullet at line 69 mentions it).

## Compatibility considerations

- N/A — documentation-only change; no API, schema, or behavioral compatibility surface.

## Security considerations

- N/A — no security-sensitive content is added; the description merely documents an
  existing enforcement boundary, it does not alter it.

## Rollback considerations

- Trivial revert: `git checkout -- docs/01_overview-files-03-scripts-part1.md` or revert
  the single commit that adds the row. No downstream artifacts depend on this doc's exact
  table contents.

## Validation plan

- Manual review: re-read the edited table to confirm the new row matches the existing
  style (short 責務 label, backtick-quoted filename) and that no other row was altered.
- Confirm the file still renders as valid Markdown (table alignment, no broken pipes).
- Cross-check against `skills/python-design/workflow.md` review habits: verify the change
  is minimal and does not introduce unrelated edits (Step 9 checklist analog: no
  over-specification, no speculative content).

## Out of scope

- Any change to source code under `scripts/agent/`.
- Any change to `docs/01_overview-files-03-scripts-part2.md`, `part3.md`, `part4.md`,
  `part5.md`.
- Adding cautions or table rows for any file other than `repository_gateway.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-141200_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-111844
- Related target files: 01_overview-files-03-scripts-part1.md
