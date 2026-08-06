## Goal

Add design rationale to the "identity vs truthiness" note in `docs/03_rag_03_01_query_pipeline-overview.md` to clarify why `is not None` checks are used (distinguishing empty results from unexecuted stages).

## Scope

- **In-Scope**: Modifying `docs/03_rag_03_01_query_pipeline-overview.md` to append a rationale sentence to the specific note.
- **Out-of-Scope**: Any modification to `scripts/rag/pipeline.py` or any other documentation files.

## Assumptions

1. The new rationale will be added in Japanese to maintain consistency with the document.
2. The phrasing will follow the provided suggestion: 「」は有効な(空の)結果として扱われ、Noneは未実行を表す。これにより「検索したが0件だった」と「まだ検索していない」を区別できる。

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire query pipeline doc: rejected because scope is limited to adding rationale.
- Create a separate document for identity vs truthiness: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/03_rag_03_01_query_pipeline-overview.md`

### Procedure

1. Locate the "identity vs truthiness" note in the document.
2. Identify insertion point at the end of that note.
3. Append the rationale sentence to the note.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the identity vs truthiness note
grep -n "identity.*truthiness\|truthiness.*identity\|is not None" docs/03_rag_03_01_query_pipeline-overview.md
```

Insertion pattern:
- After the existing "identity vs truthiness" note, append:
  「」は有効な(空の)結果として扱われ、Noneは未実行を表す。これにより「検索したが0件だった」と「まだ検索していない」を区別できる。

### Target file

Verification

### Procedure

1. Manually verify the addition using `grep` to ensure it matches the intended rationale and hasn't broken the note's structure.
2. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify rationale added
grep -c "identity.*truthiness\|is not None.*有効な.*結果\|未実行.*表す" docs/03_rag_03_01_query_pipeline-overview.md

# Verify note structure intact
sed -n '/identity.*truthiness/,/^$/p' docs/03_rag_03_01_query_pipeline-overview.md

# Run lint check
ruff check docs/03_rag_03_01_query_pipeline-overview.md
```

Expected outcomes:
- Rationale sentence appended to the "identity vs truthiness" note
- Zero lint errors on the file
- Note structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_03_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Note content | Rationale present and correctly phrased |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`.
- Modifications to any other documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-181913_require.md
- Source plan: plans/20260805-122900_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-213446
- Related target files: docs/03_rag_03_01_query_pipeline-overview.md
