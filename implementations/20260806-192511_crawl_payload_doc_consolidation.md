## Goal

Consolidate documentation by moving the `CrawlPayload` JSON example from crawler-part2.md to its canonical location in dto-models_data.md, and removing redundant logging section.

## Scope

- **In-Scope**:
  - Move JSON example from `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` (lines 79-93) to `docs/03_rag_04_01_dto-models_data.md`.
  - Replace "2.4 出力JSON形式" section in crawler-part2.md with a pointer to `docs/03_rag_04_01_dto-models_data.md`.
  - Remove "2.6 ロギング" section from crawler-part2.md and replace with a pointer to `docs/03_rag_05_3-logging.md`.
- **Out-of-Scope**:
  - Modifying `docs/03_rag_05_3-logging.md`.
  - Any changes to `scripts/rag/ingestion/crawler.py`.

## Assumptions

1. The existing field descriptions in `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` are sufficient as context.
2. The canonical DTO models document (`03_rag_04_01_dto-models_data.md`) should contain all data model examples including CrawlPayload.

## Design decisions

- Use copy-before-delete strategy: extract the JSON block first, then remove the source section, ensuring nothing is lost.
- Place the CrawlPayload section after CrawlTarget in the DTO models doc — maintains logical grouping of related types.

## Alternatives considered

- Inline the JSON example in both documents: rejected because it creates maintenance burden and inconsistency risk.
- Create a separate CrawlPayload-specific doc: over-engineered for a single example.

## Compatibility considerations

- Readers who previously found the JSON example in crawler-part2.md will need to follow the new cross-reference.
- Logging documentation readers will be redirected to the centralized logging doc.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the JSON example is corrupted during the move, restore from git history of crawler-part2.md.
- If the section heading placement in dto-models_data.md causes rendering issues, adjust the heading level.

## Implementation

### Target file

`docs/03_rag_04_01_dto-models_data.md`

### Procedure

1. Extract the CrawlPayload JSON example from crawler-part2.md (lines 79-93).
2. Insert a `### CrawlPayload` section header in dto-models_data.md after the CrawlTarget description.
3. Paste the extracted JSON example under the new header.

### Method

Copy-paste operation followed by insertion.

### Details

- Read lines 79-93 from crawler-part2.md.
- In dto-models_data.md, find the end of the CrawlTarget section.
- Insert:
  ```markdown
  ### CrawlPayload
  
  <JSON example from crawler-part2.md lines 79-93>
  ```

### Target file

`docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md`

### Procedure

1. Replace "### 2.4 出力JSON形式" section body with a cross-reference to dto-models_data.md.
2. Replace "### 2.6 ロギング" section body with a cross-reference to the logging doc.

### Method

Direct file edit using sed or manual editing.

### Details

- Find "### 2.4 出力JSON形式" section.
- Replace the entire section body (the JSON example) with prose: "For the complete CrawlPayload schema, see [dto-models_data](03_rag_04_01_dto-models_data.md)."
- Find "### 2.6 ロギング" section.
- Replace the entire section body with prose: "For log message formats, see [logging documentation](03_rag_05_3-logging.md)."

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_04_01_dto-models_data.md` | Manual review | `cat docs/03_rag_04_01_dto-models_data.md` | `CrawlPayload` JSON example exists. |
| `docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` | Manual review | `cat docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md` | Duplicated sections replaced by references. |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to the logging documentation itself.
- Modifications to other RAG documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-120000_plan_185027.md
- Source implementation procedure: N/A
- Generated at: 20260806-192511
- Related target files: docs/03_rag_04_01_dto-models_data.md, docs/03_rag_02_02_ingestion_pipeline-crawler-part2.md
