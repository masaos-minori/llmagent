## Goal

Update `docs/03_rag_02_08_ingestion_pipeline-shared.md` to state that the `_MAX_FTS_TOKENS=20` constant lacks a documented measurement or load-test basis and should be considered an unconfirmed rule-of-thumb.

## Scope

- **In-Scope**: Modifying `docs/03_rag_02_08_ingestion_pipeline-shared.md` to append a note to the "FTS5クエリのトークン数上限" subsection.
- **Out-of-Scope**:
  - Modifying any source code.
  - Modifying the "利用元" (usage-source) table.

## Assumptions

1. The current value is indeed `20` and there is no documented basis for it in the git history.
2. The project uses a specific way to flag "Needs Confirmation" or unverified claims in documentation (I will look for patterns in existing docs).

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire ingestion pipeline shared doc: rejected because scope is limited to adding a note.
- Create a separate document for FTS token limit rationale: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/03_rag_02_08_ingestion_pipeline-shared.md`

### Procedure

1. Verify existence of the target file.
2. Search `docs/` for existing "Needs Confirmation" or similar markers/phrasing to ensure consistency.
3. Locate the "### FTS5クエリのトークン数上限" subsection in the document.
4. Append a sentence/note stating that the value `20` has no documented empirical basis (measurement/load testing) in the repository history and is currently an unconfirmed rule-of-thumb estimate. Use Japanese prose consistent with the document.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the FTS5 token limit section
grep -n "FTS5.*クエリ.*トークン数.*上限\|FTS5.*Query.*Token.*Limit" docs/03_rag_02_08_ingestion_pipeline-shared.md

# Find the _MAX_FTS_TOKENS mention
grep -n "_MAX_FTS_TOKENS\|MAX_FTS_TOKENS" docs/03_rag_02_08_ingestion_pipeline-shared.md

# Find existing "Needs Confirmation" patterns in docs
grep -rn "Needs Confirmation\|未確認\|要確認\|unverified" docs/

# Verify current value in source
grep -rn "_MAX_FTS_TOKENS\|MAX_FTS_TOKENS" scripts/rag/
```

Insertion pattern:
- After the existing text about `_MAX_FTS_TOKENS = 20`, append:
  ```markdown
  > この値の根拠は、リポジトリの履歴に測定データや負荷テストの結果として文書化されていません。現在、これは未確認の経験則的な見積もりです（Needs Confirmation）。
  ```

### Target file

Verification

### Procedure

1. Manually verify the addition.
2. Ensure no other parts of the document were accidentally changed.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify Needs Confirmation note added
grep -c "Needs Confirmation\|未確認" docs/03_rag_02_08_ingestion_pipeline-shared.md

# Verify _MAX_FTS_TOKENS still present
grep -c "_MAX_FTS_TOKENS" docs/03_rag_02_08_ingestion_pipeline-shared.md

# Verify util table untouched
grep -c "利用元\|usage.*source" docs/03_rag_02_08_ingestion_pipeline-shared.md

# Run lint check
ruff check docs/03_rag_02_08_ingestion_pipeline-shared.md
```

Expected outcomes:
- Needs Confirmation note appended to FTS5 token limit subsection
- Value `20` context preserved
- Util table untouched
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_02_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | Correct note added without affecting other sections |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-181614_require.md
- Source plan: plans/20260805-123430_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-215133
- Related target files: docs/03_rag_02_08_ingestion_pipeline-shared.md
