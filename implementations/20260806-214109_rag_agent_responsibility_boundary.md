## Goal

Add a subsection to `docs/04_mcp_05_04_mdq-rag-boundary.md` clarifying the responsibility boundary between `RagPipeline` (core logic) and `rag-pipeline-mcp` (production boundary), including the fact that direct imports are currently a convention rather than an enforced rule.

## Scope

- **In-Scope**: Modifying `docs/04_mcp_05_04_mdq-rag-boundary.md` to add the "RAG and Agent Responsibility Boundary" subsection.
- **Out-of-Scope**:
  - Creating a new file for this purpose (unless the existing doc becomes too large during implementation).
  - Modifying any source code (`scripts/`).
  - Adding new `.importlinter` contracts.

## Assumptions

1. The new subsection will be integrated into the "Agent access patterns" section of `docs/04_mcp_05_04_mdq-rag-boundary.md`.
2. The language used will match the existing document's bilingual (Japanese-primary/English-secondary) style.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Create a separate document for RagPipeline responsibility: rejected because scope is limited to this doc.
- Rewrite the entire mdq-rag-boundary doc: rejected because scope is limited to adding subsection.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/04_mcp_05_04_mdq-rag-boundary.md`

### Procedure

1. Verify existence of the target file.
2. Perform a final `grep` on `scripts/agent/` to confirm no direct `RagPipeline` imports exist (as specified in requirements).
3. Locate the "Agent access patterns" (エージェントのアクセスパターン) section in the document.
4. Append/Insert the "RAG and Agent Responsibility Boundary" subsection.
5. Ensure the following points are covered:
   - `RagPipeline` (`scripts/rag/pipeline.py`) = core RAG logic.
   - `rag-pipeline-mcp` (`scripts/mcp_servers/rag_pipeline/`) = production boundary via `RagPipelineMCPService`/`RagPipelineMCPServer`.
   - Direct imports are for tests/dev only.
   - Explicitly state that this is currently a **convention**, not enforced by `.importlinter` (the `agent -> rag` direction is currently permitted).

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the agent access patterns section
grep -n "Agent.*access.*pattern\|エージェント.*アクセス.*パターン" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify no direct RagPipeline imports in agent scripts
grep -c "from.*rag.*import.*RagPipeline\|import.*RagPipeline" scripts/agent/

# Verify RagPipeline location
grep -rn "class RagPipeline" scripts/rag/pipeline.py

# Verify rag-pipeline-mcp location
grep -rn "RagPipelineMCPService\|RagPipelineMCPServer" scripts/mcp_servers/rag_pipeline/

# Verify importlinter status
grep -rn "agent.*rag\|rag.*agent" .importlinter/
```

Insertion pattern:
- After the "Agent access patterns" section header, insert:
  ```markdown
  ### RAG and Agent Responsibility Boundary

  RagPipeline (`scripts/rag/pipeline.py`) はコアなRAGロジックを担います。
  rag-pipeline-mcp (`scripts/mcp_servers/rag_pipeline/`) は、RagPipelineMCPService / RagPipelineMCPServer を通じて生産環境の境界を提供します。
  直接インポートはテストや開発用途のみです。
  なお、これは現在 **慣習** であり、`.importlinter` で強制されているわけではありません（`agent -> rag` の方向は現在許可されています）。
  ```

### Target file

Verification

### Procedure

1. Manually verify the document structure and content.
2. Check for broken internal links or formatting issues.
3. Run lint check on modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify subsection added
grep -c "RAG.*Agent.*Responsibility.*Boundary\|RAG.*Agent.*責任.*境界" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify convention statement present
grep -c "慣習\|convention" docs/04_mcp_05_04_mdq-rag-boundary.md

# Verify importlinter note present
grep -c "importlinter.*許可\|importlinter.*permitted" docs/04_mcp_05_04_mdq-rag-boundary.md

# Run lint check
ruff check docs/04_mcp_05_04_mdq-rag-boundary.md
```

Expected outcomes:
- New subsection added under "Agent access patterns" section
- All key points covered (RagPipeline core logic, rag-pipeline-mcp production boundary, direct imports for dev/test only, convention not enforced)
- Zero lint errors on the file
- Document structure preserved (no accidental restructuring)

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/04_mcp_05_*.md` | Docs files | 0 errors |
| Manual | Visual/Grep | Content accuracy | All key points from requirement included without asserting technical enforcement where none exists |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Adding new `.importlinter` contracts.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-152841_require.md
- Source plan: plans/20260805-123000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-214109
- Related target files: docs/04_mcp_05_04_mdq-rag-boundary.md
