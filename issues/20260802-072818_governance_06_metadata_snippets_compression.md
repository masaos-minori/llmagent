# Compress docs/00_governance_06 "Recommended Additional Fields" YAML snippets into a table

## Priority
Low

## Summary
The "Recommended Additional Fields" section of `docs/00_governance_06_ai-reading-metadata.md` lists 8 individual one-line YAML snippets (e.g. `scope: agent`) that duplicate information already present in the file's combined "Usage Examples" front-matter example.

## Reason for Change
The 8 snippets are a mechanical, redundant enumeration; the same field names/values/purpose are already demonstrated together in Usage Examples.

## Implementation Intent
Replace the 8 individual snippets with a compact 3-column table (field name / allowed values / purpose), keeping the full combined example only in Usage Examples.

## Target Files or Areas
`docs/00_governance_06_ai-reading-metadata.md`

## Required Changes
- Remove the 8 individual YAML snippet lines under "Recommended Additional Fields".
- Add a 3-column table: フィールド名 / 許容値 / 目的, covering the same 8 fields.
- Add a note pointing to "Usage Examples" for the full combined example.

## Acceptance Criteria
"Recommended Additional Fields" shows a table instead of repeated individual snippets; Usage Examples remains the sole place with a full worked example.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_06` restructured — no information introduced or removed, only reformatted.

## Out of Scope
Do not change the field names, allowed values, or their meaning. Do not touch the Markdown-notation-rules or 記載方針 sections (tracked in a separate issue).

## AI Implementation Instruction
Preserve every field name/value/purpose currently documented; only change presentation format.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 1, §5 例2
- Generated at: 2026-08-02
