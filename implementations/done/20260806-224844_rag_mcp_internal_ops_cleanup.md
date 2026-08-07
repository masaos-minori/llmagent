## Goal
Remove verbatim `list_documents()` Python signature and `--help` output blocks from `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`, replacing them with pointers to the implementation tree; consolidate the three identical crawler/chunk_splitter/ingester sections into one.

## Scope
- **In-Scope**:
  - `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` — remove mechanical content, consolidate duplicate sections
- **Out-of-Scope**:
  - Modifying source code (`scripts/mcp_servers/rag_pipeline/document_manager.py`, `scripts/rag/ingestion/document_manager.py`)
  - Modifying `tools/gen_rag_reference.py` (already has CLI-help generation removed)
  - Modifying any other documentation files

## Assumptions
- The deletion-order description (2-stage, `chunks_vec → documents`, CASCADE removes `chunks`) is correct and must remain unchanged.
- The opening responsibility-boundary declaration is correct and must remain unchanged.
- The existing pointers to `list_documents()` and CLI scripts are adequate; no further content needed beyond consolidation.

## Design decisions
- Replace verbatim CLI `--help` output and Python method signatures with concise pointers to the authoritative source locations.
- Use a single consolidated subsection for all three CLI tools rather than repeating nearly-identical paragraphs.
- Keep the responsibility-boundary declaration and `delete_document()` section untouched.

## Alternatives considered
- Retaining the verbatim `--help` output as-is — rejected because it drifts from reality and adds no value over pointing to the actual CLI.
- Keeping three separate sections for each CLI tool — rejected because the content is functionally identical across all three.

## Implementation

### Target file
`docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`

### Procedure
1. **Verification**: Confirm `tools/gen_rag_reference.py` has no CLI-help generation dependency elsewhere (check CI workflows, pyproject.toml, other docs).
2. **Consolidate duplicate sections**: Replace the three identical sections (`## crawler`, `## chunk_splitter`, `## ingester`) with a single consolidated section:
   ```markdown
   ## CLI Tools
   For current CLI usage, run `crawler.py --help`, `chunk_splitter.py --help`, or `ingester.py --help` in `scripts/rag/ingestion/`.
   ```
3. **Remove verbatim signatures**: Remove the `list_documents()` Python method signature block and replace with a pointer to `scripts/mcp_servers/rag_pipeline/document_manager.py`.
4. **Validate**: Re-read the edited document end-to-end to confirm no verbatim `--help` output or method signature remains.

### Method
Manual Markdown editing — no code generation or tooling required.

### Details
- **Deletion order section**: Must remain unchanged — confirms 2-stage deletion (`chunks_vec → documents`, CASCADE removes `chunks`).
- **Responsibility boundary declaration**: Must remain unchanged — establishes that the MCP server operates on the SQLite database directly, not through ORM.
- **CLI tools consolidation**: All three tools share the same pattern (Python script in `scripts/rag/ingestion/`, invoked via `python -m ...` or direct execution). A single paragraph suffices.
- **`list_documents()` signature**: The verbatim signature shows `(self, doc_id: str)` return type and body — this is redundant when the source file is accessible. Replace with: "See `scripts/mcp_servers/rag_pipeline/document_manager.py::DocumentManager.list_documents`."

## Compatibility considerations
N/A — documentation-only change. No API or behavioral compatibility impact.

## Security considerations
N/A — no security-relevant changes.

## Rollback considerations
Simple revert: restore the original three-section layout and verbatim signatures. No database migration or config rollback needed.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` | Manual Review | Visual inspection of rendered Markdown | Single consolidated CLI section instead of three identical sections; no verbatim signatures/help output |

## Out of scope
- Source code modifications in `scripts/mcp_servers/rag_pipeline/document_manager.py` or `scripts/rag/ingestion/document_manager.py`
- Changes to `tools/gen_rag_reference.py`
- Changes to any other `docs/*.md` files

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-222912_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-224844
- Related target files: docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md
