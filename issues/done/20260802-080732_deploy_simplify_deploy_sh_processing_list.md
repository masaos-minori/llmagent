# Simplify deploy.sh processing list in docs/02_deployment-part1.md

## Priority
Low

## Summary
`docs/02_deployment-part1.md` §2.2 (~lines 106-110) verbatim-lists `deploy.sh`'s copy operations ("Copies pyproject.toml to /opt/llm/", etc.) — mechanical content directly derivable from reading the script.

## Reason for Change
This listing goes stale whenever `deploy.sh`'s copy targets change, and provides no design-intent value beyond what the script's own comments already convey.

## Implementation Intent
Compress the bullet list to a one-sentence summary of intent, deferring exact copy-target detail to `deploy/deploy.sh`'s own comments.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.2, ~lines 106-110)

## Required Changes
- Replace the bullet list with: "deploy.sh は本番稼働に必要なランタイム成果物(依存定義・スクリプト・設定・スキーマ)を `/opt/llm/` 配下にコピーし、必要なディレクトリ構成を作成する。詳細な対応関係は `deploy/deploy.sh` のコメントを正とする。"

## Acceptance Criteria
The bullet-list transcription is replaced with the one-sentence summary; no copy-target detail is duplicated in the document.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/02_deployment-part1.md` shortened.

## Out of Scope
Do not change `deploy/deploy.sh`'s actual copy logic in this issue — documentation only.

## AI Implementation Instruction
Verify `deploy.sh`'s comments actually convey equivalent detail before removing the bullet list, so no information is genuinely lost.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §2 削除候補 item 2, §5 例5
- Generated at: 2026-08-02
