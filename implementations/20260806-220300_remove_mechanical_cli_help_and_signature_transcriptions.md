## Goal

Clean up `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` by replacing verbatim `--help` outputs and method signatures with pointers to their source implementations. Also, evaluate whether to remove the CLI-help generation capability from `tools/gen_rag_reference.py`.

## Scope

- **In-Scope**: 
  - Modifying `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` to replace verbatim content with pointers.
  - Investigating/modifying `tools/gen_rag_reference.py` to remove the `generate_cli_help` feature if it has no other dependents.
- **Out-of-Scope**: 
  - Modifying any source code.
  - Modifying any other documentation files.

## Assumptions

1. The requirements regarding what to keep (responsibility boundary and deletion order) are clearly stated in the requirement.
2. Removing the CLI-help generation from `tools/gen_rag_reference.py` is safe if no other parts of the repo depend on it.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite all RAG docs: rejected because scope is limited to converting references.
- Create a separate document for each file: rejected because scope is limited to these specific docs.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Phase 1: Investigation

#### Procedure

1. Verify existence of `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` and `tools/gen_rag_reference.py`.
2. Search the entire repository for any usage of the CLI-help generation logic within `tools/gen_rag_reference.py` (e.g., searching for strings related to `CLI_HELP_DOC` or similar constants used in that tool).

#### Method

Manual verification + tool execution.

#### Details

```bash
# Verify file existence
ls -la docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md
ls -la tools/gen_rag_reference.py

# Search for CLI help generation dependencies
grep -rn "CLI_HELP_DOC\|generate_cli_help\|cli_help" . --include="*.py" --include="*.md"

# List current doc content structure
head -100 docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md
```

### Phase 2: Core Logic Implementation

#### Procedure

For each target file:
1. Locate the `<file>.py:<line>` pattern.
2. Identify the corresponding symbol (function, method, class, etc.) in the source file.
3. Replace the line-number reference with the name-based reference following the established pattern (`<name>() 関数`, etc.).
4. Ensure existing "根拠分類" annotations are preserved.

#### Method

Direct file edit using sed or manual editing.

#### Details

```bash
# Example: Convert pipeline.py:123 to pipeline.py::RagPipeline class
# Search for the symbol in the source file
grep -n "class RagPipeline\|def run\|def execute" scripts/rag/pipeline.py

# Replace pipeline.py:123 with pipeline.py::RagPipeline() 関数
sed -i 's/pipeline\.py:[0-9]\+/pipeline.py::RagPipeline()/g' docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
```

Repeat for each target file and each symbol type:
- Class: `<file>.py::<ClassName>() クラス`
- Function: `<file>.py::<function_name>() 関数`
- Method: `<file>.py::<ClassName>::<method_name>() メソッド`

### Phase 3: Verification

#### Procedure

1. Re-run `grep -rnE '\.py:[0-9]+' docs/03_rag_*.md` to ensure no numeric references remain.
2. Spot-check converted references to ensure they point to correct symbols.

#### Method

Manual verification + tool execution.

#### Details

```bash
# Verify no numeric references remain
grep -rnE '\.py:[0-9]+' docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_04_query_pipeline-search-stages.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_05_query_pipeline-augment-stages.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
grep -rnE '\.py:[0-9]+' docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md
grep -rnE '\.py:[0-9]+' docs/03_rag_02_07_ingestion_pipeline-utils.md
grep -rnE '\.py:[0-9]+' docs/03_rag_04_04_dto-models_config.md
grep -rnE '\.py:[0-9]+' docs/03_rag_91_design_notes-part2.md

# Verify root cause classification annotations preserved
grep -c "根拠分類\|Root.*Cause" docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md

# Run lint check
ruff check docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md docs/03_rag_03_04_query_pipeline-search-stages.md docs/03_rag_03_05_query_pipeline-augment-stages.md docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md docs/03_rag_02_07_ingestion_pipeline-utils.md docs/03_rag_04_04_dto-models_config.md docs/03_rag_91_design_notes-part2.md
```

Expected outcomes:
- All line-number references converted to name-based references
- Root cause classification annotations preserved
- Zero lint errors on all modified files
- Document structure preserved (no accidental restructuring)

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All Target Docs | Manual Review | `grep -rnE '\.py:[0-9]+' docs/03_rag_*.md` | No output (no numeric references found) |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-190046_require.md
- Source plan: plans/20260805-144902_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-215636
- Related target files: docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md, docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md, docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md, docs/03_rag_03_04_query_pipeline-search-stages.md, docs/03_rag_03_05_query_pipeline-augment-stages.md, docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md, docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md, docs/03_rag_02_07_ingestion_pipeline-utils.md, docs/03_rag_04_04_dto-models_config.md, docs/03_rag_91_design_notes-part2.md
