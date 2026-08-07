## Goal

Consolidate duplicated documentation sections (JSON output format and logging) in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` by moving them to their canonical locations (`docs/03_rag_04_01_dto-models_data.md` for JSON and `docs/03_rag_05_3-logging.md` for logging) and replacing the original sections with references.

## Scope

- **In-Scope**:
  - Move JSON example from `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` to `docs/03_rag_04_01_dto-models_data.md`.
  - Replace the JSON section in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` with a reference.
  - Replace the logging section in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` with a reference to `docs/03_rag_05_3-logging.md`.
- **Out-of-Scope**:
  - Modifying `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`.
  - Modifying `scripts/` or other source code.
  - Changing the responsibility attribution section in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`.

## Assumptions

1. `docs/03_rag_04_01_dto-models_data.md` is the preferred canonical home for the `CrawlPayload` JSON example.
2. `docs/03_rag_05_3-logging.md` is the canonical source for crawler logging information.

## Design decisions

- Treat duplication consolidation as a read-move operation — verify content exists at destination before removing from source.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Keep duplicates but add cross-references: rejected because it leaves redundant content.
- Merge all three RAG docs into one: rejected because scope is limited to this specific duplication issue.

## Compatibility considerations

- Cross-references must use existing Markdown link conventions.
- Section headings in destination files must exist or be created before adding references.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If JSON example is lost during move, restore from git history.
- If cross-reference links break, revert to original duplicate sections.

## Implementation

### Target file

`docs/03_rag_04_01_dto-models_data.md`

### Procedure

1. Search for `CrawlPayload` JSON example in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`.
2. Verify the JSON example does not already exist in `docs/03_rag_04_01_dto-models_data.md`.
3. Copy the JSON example block to `docs/03_rag_04_01_dto-models_data.md` under appropriate section.
4. Add section heading if missing.

### Method

Direct file edit using sed or manual editing.

### Details

- Extract JSON example block from source (typically between code fence markers).
- Insert into destination file after verifying no duplicate exists.
- Preserve markdown formatting (code fences, indentation).

### Target file

`docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`

### Procedure

1. Identify the JSON output format section boundaries.
2. Replace the entire JSON section with a cross-reference link to `docs/03_rag_04_01_dto-models_data.md`.
3. Identify the logging section boundaries.
4. Replace the entire logging section with a cross-reference link to `docs/03_rag_05_3-logging.md`.

### Method

Direct file edit.

### Details

```bash
# Find JSON section boundaries
grep -n "JSON\|json" docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md | head -20

# Find logging section boundaries
grep -n "log\|Log\|LOG" docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md | head -20
```

- Replace with Markdown link syntax: `[See CrawlPayload JSON example](../03_rag_04_01_dto-models_data.md)`
- Replace with Markdown link syntax: `[See logging details](../03_rag_05_3-logging.md)`
- Preserve surrounding paragraph structure.

### Target file

Verification

### Procedure

1. Verify JSON example exists in `docs/03_rag_04_01_dto-models_data.md`.
2. Verify cross-reference links in `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` are valid.
3. Verify no broken links remain.

### Method

Manual verification + grep.

### Details

```bash
# Verify JSON example moved
grep -c "CrawlPayload" docs/03_rag_04_01_dto-models_data.md

# Verify cross-references added
grep -n "03_rag_04_01_dto-models_data.md\|03_rag_05_3-logging.md" docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md

# Verify old sections removed
grep -c "JSON output format\|logging configuration" docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_04_01_dto-models_data.md` | Manual review | `grep CrawlPayload` | JSON example present |
| `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` | Manual review | `grep` on cross-references | Duplicate sections replaced, links valid |

## Out of scope

- Modifications to `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md`.
- Changes to any source code (`scripts/`).
- Restructuring of destination doc sections beyond what's needed for the copy.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-185027_require.md
- Source plan: plans/20260805-113913_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-211809
- Related target files: docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md, docs/03_rag_04_01_dto-models_data.md, docs/03_rag_05_3-logging.md
