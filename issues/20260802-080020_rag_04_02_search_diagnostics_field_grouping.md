# Group docs/03_rag_04_02 SearchDiagnostics fields by local vs. remote-added

## Priority
Low

## Summary
`docs/03_rag_04_02_dto-models_result.md`'s `SearchDiagnostics` field table (8 fields) lists all fields in a flat, parallel list, without indicating that some are original local-execution counters while others (`http_result_kind`, `remote_*`) were added later specifically for the HTTP RAG service integration.

## Reason for Change
Without grouping by origin/purpose, a reader can't easily tell which fields are only meaningful in HTTP-delegated mode versus always-populated local-execution fields.

## Implementation Intent
Split the field table into 2 groups: local-execution-origin counters, and HTTP-integration-added fields (meaningful only when delegated to the remote service).

## Target Files or Areas
`docs/03_rag_04_02_dto-models_result.md`

## Required Changes
- Reorganize the `SearchDiagnostics` field table into 2 groups: "ローカル系" (e.g. `fallback_count` and similar always-populated counters) and "HTTP導入後追加" (`http_result_kind`, `remote_*` fields — meaningful only when delegated to the remote service).

## Acceptance Criteria
The field table is grouped into local vs. HTTP-integration-added fields, with a note that the latter group is meaningful only in delegated/remote execution.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_04_02` table reorganized.

## Out of Scope
Do not change the actual `SearchDiagnostics` dataclass in this issue — documentation only.

## AI Implementation Instruction
Verify each field's actual origin/purpose against the dataclass definition and its usage before assigning it to a group.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §3 要約候補 item 6
- Generated at: 2026-08-02
