## Goal

Update the chunk-file lifecycle table so validation-failed groups drain to `failed/` with `.error.json`, and note the per-generation grouping of chunk files (REQ-007: lifecycle doc).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 3 documentation row)

## Assumptions

- Only the `chunk/` row of the lifecycle table (line 36) changes; the crawl-file and `registered/` rows stay as written.

## Design decisions

- Extend the existing `Deletion Policy` cell wording rather than add a table row: group-validation failures end in `failed/` like other failures, and the grouping change is a one-sentence note below the table (Plan Documentation Impact).

## Alternatives considered

N/A: table-cell wording update; no alternative doc layout proposed by the Plan.

## Implementation
### Target file
`docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`
### Procedure

- In the lifecycle table's `chunk/` row (line 36), extend "Moved out of `chunk/` after ingestion" to state that chunk files rejected by URL-group validation (group signature mismatch, parse failure, invalid/empty url) also leave `chunk/` to `failed/` with a `.error.json` file naming the failure reason.
- Add one sentence after the table: chunk files are grouped per URL and per crawl generation (payload `fetched_at`), processed oldest first, so files from distinct generations of one URL never compete in one group.

### Method

- Keep table structure and cell brevity comparable; behavior description only, no implementation detail (`skills/DESIGN.md` Docs content policy).

### Details

- No `group_validation_failed`-specific failure-reason vocabulary beyond what `.error.json` already names; keep the row readable.

## Compatibility considerations

- Prose must match the behavior shipped by sibling procedures 01-02; execute this document after they land (Plan Phase 3).
- Co-target: this doc is also targeted by plan `20261106-102010_raging005_retry-dir-no-consumer.md` (overlap tool) — verify the two doc edits do not contradict each other before/while implementing.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Check | Command |
|---|---|
| Docs structural rules | `uv run python tools/check_docs_quality.py` |
| Docs structure | `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` |
| Docs content policy | `uv run python tools/check_docs_content_policy.py` |
| Domain claim consistency | `uv run python tools/check_docs_consistency.py --domain rag` |

## Completion criteria

- AC-5: the lifecycle table states every validation-failure path drains to `failed/` with `.error.json`; the generation-grouping sentence is present; all four docs checkers pass.

## Out of Scope

- `docs/21_rag/rag_05_03-logging.md` (documents log formats, not message inventory — no change, Plan Documentation Impact).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the lifecycle table and grouping note per Procedure | Completed | 20261106-143204 | 20261106-143204 | Execute after sibling procedures 01-02 land |
| 2 | Run the docs checkers in the Validation plan | Completed | 20261106-143204 | 20261106-143204 | `routing.md` Tools "When to run which tool" |

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
- **Requirement ID**: `REQ-007` (chunk-file lifecycle doc update)
- **Source issue**: `issues/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-115721
- **Related target files**: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`