## Goal

Correct the exception-catching-location sentence in the augment-stages document so it names the live runner, `RagPipelineStageLifecycle._run_stage()`, instead of the removed `RagPipeline._run_stage()` (`REQ-005`: name the lifecycle as the catch location).

## Scope
**Release unit**: ragrev009-delete

- In scope: the `Exception Catching Location` paragraph of `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`.
- Plan step 3, second bullet; apply together with `..._01_scripts_rag_pipeline.py.md`.

## Assumptions

- Re-verified at generation time: the paragraph says any exception other than `RagRerankError` propagates to `RagPipeline._run_stage()`, which catches `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, and `TimeoutError` and converts them into `StageResult(status="failure", fallback_reason=<exception_message>)`; the live runner in `scripts/rag/stage_lifecycle.py` catches the same five types with the same result.
- `rg "_run_stage" docs/21_rag` finds only this sentence, so no other document needs the same fix.
- Overlap with `implementations/20261109-104558_06_docs_21_rag_rag_03_05_query_pipeline-augment-stages.md.md` (ragrev002): compatible; that procedure edits a different paragraph. Re-read the paragraph before editing if the file changed.
- Docs are English (`skills/DESIGN.md` Output language); the Docs content policy applies.

## Design decisions

- Replace only the class name in the sentence; keep the list of absorbed exceptions and the continuation behavior as written, since they are accurate for the lifecycle runner.

## Alternatives considered

N/A: one-token documentation edit.

## Implementation
### Target file
`docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`

### Procedure
1. In the `Exception Catching Location` paragraph, change `RagPipeline._run_stage()` to `RagPipelineStageLifecycle._run_stage()`.

### Method
- Single in-place edit; no other sentence, heading, or link changes.

### Details
- After the edit, `rg "RagPipeline\._run_stage" docs` returns nothing.
- Do not edit another document; a needed change elsewhere is an additional target file discovery.

## Compatibility considerations

N/A: documentation only; no file is renamed or removed.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The paragraph names `RagPipelineStageLifecycle._run_stage()` as the catch location and no document references `RagPipeline._run_stage`.
- All five checkers report no findings.

## Out of Scope

- Code, tests, and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the catch-location sentence | Completed | — | — |  |
| 2 | Run the documentation checkers named in Validation plan | Completed | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (name the lifecycle as the catch location)
- **Source issue**: issues/20261108-131122_ragrev009_dead-pipeline-stage-runner.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-135456
- **Related target files**: `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`