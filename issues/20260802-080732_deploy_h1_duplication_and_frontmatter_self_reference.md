# Fix H1 heading duplication and part2's incorrect frontmatter self-reference (docs/02_deployment part1/part2)

## Priority
Medium

## Summary
Both `docs/02_deployment-part1.md` and `docs/02_deployment-part2.md` use the identical H1 heading "# 導入手順・デプロイ," which would collide if the two files are ever combined into a unified view. Separately, `part2`'s frontmatter `source` field points to `part1` itself rather than a genuine external source — likely a copy-paste artifact left over from when `part2` was split off from `part1`.

## Reason for Change
Identical H1 headings across split files is a structural risk for any tooling that generates a combined/unified view of the document set. The incorrect `source` frontmatter is a metadata error that misrepresents the file's provenance.

## Implementation Intent
Differentiate the two H1 headings to reflect each file's actual content scope (e.g. "環境構築・起動" for part1, "DB初期化・失敗モード" for part2, matching this review's own characterization), and correct part2's frontmatter `source` field to its actual, correct value (or remove it if no genuine external source applies).

## Target Files or Areas
`docs/02_deployment-part1.md`, `docs/02_deployment-part2.md`

## Required Changes
- Change `part1`'s H1 to reflect its actual scope (environment setup / startup).
- Change `part2`'s H1 to reflect its actual scope (DB initialization / failure modes).
- Fix `part2`'s frontmatter `source` field: determine the correct value (likely should not self-reference; check whether this field should point to an original pre-split document, be removed, or be corrected to a different value) and correct it.

## Acceptance Criteria
`part1` and `part2` no longer share an identical H1 heading; `part2`'s frontmatter `source` field no longer incorrectly self-references `part1` (or itself).

## Testing Expectations
Not required (documentation-only). Verify any tooling that parses frontmatter `source` (if it exists) still functions correctly after the change.

## Documentation Impact
Both files' headings and `part2`'s frontmatter corrected.

## Out of Scope
Do not restructure the files' content or split boundary in this issue — heading/frontmatter fixes only.

## AI Implementation Instruction
Before changing `part2`'s frontmatter `source`, check whether other tooling (e.g. a documentation index generator) depends on this field's current value — if so, coordinate the fix accordingly rather than changing it blindly.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §1 (連結文書としての問題), §複数ファイルにまたがる重複・矛盾
- Generated at: 2026-08-02
