## Goal

Clean up redundant information in ChunkSplitter documentation: replace mechanical constant/method tables with prose in Part 1, simplify the `--force` description in Part 2, and document the (unconfirmed) rationale for `MIN_HEADING_LINES_FOR_MARKDOWN=2`.

## Scope

- **In-Scope**:
  - `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`: Replace tables with prose and add rationale for `MIN_HEADING_LINES_FOR_MARKDOWN`.
  - `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`: Update `--force` description.
- **Out-of-Scope**:
  - Any modification to `scripts/rag/ingestion/chunk_splitter.py`.
  - Removal of "Typed dict" table, "継承" note, or sections §3.1.1, §3.1.2 in Part 1.
  - Modification of any other documentation files.

## Assumptions

1. The replacement text for `--force` in Part 2 must match the requested wording exactly.
2. The rationale for `MIN_HEADING_LINES_FOR_MARKDOWN` should be presented as "Needs Confirmation" based on the investigation provided in the requirement.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire ChunkSplitter doc: rejected because scope is limited to removing redundancy.
- Create a separate document for MIN_HEADING_LINES_FOR_MARKDOWN rationale: rejected because scope is limited to these two docs.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.
- If table removal breaks downstream references, restore tables.

## Implementation

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`

### Procedure

1. Locate the "モジュールレベルの定数" and "公開メソッド" tables in Part 1.
2. Identify insertion points for:
   - Prose description replacing the constants table.
   - Prose description replacing the methods table.
   - Rationale for `MIN_HEADING_LINES_FOR_MARKDOWN=2` marked as "Needs Confirmation".
3. Remove the two tables and add prose descriptions.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the constant table
grep -n "モジュールレベル.*定数\|Module.*Level.*Constant" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Find the method table
grep -n "公開メソッド\|Public.*Method" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Find MIN_HEADING_LINES_FOR_MARKDOWN mentions
grep -n "MIN_HEADING_LINES_FOR_MARKDOWN\|最小見出し行数" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
```

Insertion pattern:
- After constants table header, add prose: "このモジュールは以下の定数を定義しています。詳細はソースコードを参照してください。"
- After methods table header, add prose: "このモジュールは以下の公開メソッドを提供します。詳細はソースコードを参照してください。"
- Near `MIN_HEADING_LINES_FOR_MARKDOWN` mention, add: "この値の設計根拠は未確認です（Needs Confirmation）。"

### Target file

`docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`

### Procedure

1. Locate the `--force` row in the CLI arguments table.
2. Update the `--force` description with the specified wording.

### Method

Direct file edit using sed.

### Details

```bash
# Find the --force row
grep -n "\-\-force\|強制" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md
```

Update the `--force` description row with the exact wording from the requirement.

### Target file

Verification

### Procedure

1. Manually verify that no required elements (Typed dict, etc.) were accidentally removed from Part 1.
2. Verify both files still render correctly as Markdown.
3. Run lint check on modified files.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify Typed dict preserved
grep -c "Typed dict\|typed.*dict" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Verify inheritance note preserved
grep -c "継承\|inheritance" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Verify sections 3.1.1 and 3.1.2 preserved
grep -c "§3\.1\.1\|§3\.1\.2" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Verify tables removed
grep -c "モジュールレベル.*定数.*Table\|公開メソッド.*Table" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md

# Verify --force updated
grep -n "\-\-force" docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md

# Run lint check
ruff check docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part*.md
```

Expected outcomes:
- Two tables removed from Part 1, replaced with prose
- `MIN_HEADING_LINES_FOR_MARKDOWN` rationale documented as "Needs Confirmation"
- `--force` description updated in Part 2
- Zero lint errors on both files
- Protected elements (Typed dict, inheritance note, sections 3.1.1/3.1.2) preserved in Part 1

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_*` | Docs files | 0 errors |
| Manual | Visual/Grep | Table removal & wording | Tables gone in P1, correct wording in P2 |

## Out of scope

- Modifications to `scripts/rag/ingestion/chunk_splitter.py`.
- Removal of "Typed dict" table, "継承" note, or sections §3.1.1, §3.1.2 in Part 1.
- Modifications to any other documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-181157_require.md
- Source plan: plans/20260805-122830_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-212919
- Related target files: docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md, docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md
