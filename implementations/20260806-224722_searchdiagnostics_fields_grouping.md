## Goal
Split the flat `SearchDiagnostics` field table in `docs/03_rag_04_02_dto-models_result.md` into two clearly labeled groups matching the dataclass's own conceptual separation: local-execution counters and HTTP-integration-added fields.

## Scope
- **In-Scope**:
  - `docs/03_rag_04_02_dto-models_result.md` — restructure the `SearchDiagnostics` field table into two subgroups
- **Out-of-Scope**:
  - Modifying source code (`scripts/rag/models_result.py`)
  - Modifying any other documentation files
  - Adding automated tests (documentation-only change)

## Assumptions
- The existing prose in the "実装意図" section correctly describes the local vs. remote split; no content rewrite needed beyond structural reorganization.
- All existing Type/Default/Description values for all 8 fields must be preserved unchanged.

## Design decisions
- Use two separate Markdown tables rather than a single flat table, each with a clear Japanese label indicating its conceptual group.
- Keep the same column headers (Field, Type, Default, Description) for both tables to maintain consistency.
- Add an explicit annotation under Group 2 stating these fields are meaningful only when search was delegated to remote HTTP RAG service.

## Alternatives considered
- Single table with inline annotations per row — rejected because it does not provide the visual separation the requirement demands.
- Adding a subsection header within the existing table — rejected because Markdown tables do not support row-spanning headers natively.

## Implementation

### Target file
`docs/03_rag_04_02_dto-models_result.md`

### Procedure
1. Verify the current doc state still contains a single flat `SearchDiagnostics` field table (not yet grouped).
2. Identify the 8 fields currently listed in the flat table.
3. Split into two tables:
   - **Group 1 (ローカル実行系カウンタ)**: `embed_ok`, `embed_failed`, `fts_errors`
   - **Group 2 (HTTP導入後追加フィールド)**: `result_source`, `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `fallback_reason`
4. For Group 2, add a note above the table stating these fields are meaningful only when search was delegated to remote HTTP RAG service.
5. Preserve all existing Type/Default/Description cell values exactly.
6. Leave the "実装意図" section as-is or lightly tighten if redundant.

### Method
Manual Markdown editing — no code generation or tooling required.

### Details
- **Group 1 fields** (local execution counters):
  - `embed_ok` — count of successful embedding operations
  - `embed_failed` — count of failed embedding operations
  - `fts_errors` — count of FTS query errors
- **Group 2 fields** (HTTP integration additions):
  - `result_source` — indicates local vs. remote result origin
  - `http_result_kind` — kind literal from `HttpAugmentResult`
  - `remote_status_code` — HTTP status code from remote service
  - `remote_latency_ms` — latency measurement for remote call
  - `fallback_reason` — reason for fallback to local processing
- Column format preserved: `| Field | Type | Default | Description |` for both tables.
- No changes to the `RagPipeline.get_diagnostics()` method or `SearchDiagnostics` dataclass definition in `scripts/rag/models_result.py`.

## Compatibility considerations
N/A — documentation-only change. No API or behavioral compatibility impact.

## Security considerations
N/A — no security-relevant changes.

## Rollback considerations
Simple revert: restore the original flat table structure. No database migration or config rollback needed.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_04_02_dto-models_result.md` | Manual Review | Visual inspection of rendered Markdown | Two separate field tables with clear labels instead of one flat 8-row table |

## Out of scope
- Source code modifications in `scripts/rag/models_result.py`
- Changes to any other `docs/*.md` files
- Automated test additions

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260806-222637_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-224722
- Related target files: docs/03_rag_04_02_dto-models_result.md
