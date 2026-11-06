## Goal

Update §4.6 so `IngestUrlResult.validation_failure()` is described as routing the failed chunk group to `failed/` with `.error.json` instead of leaving it in `chunk/` (REQ-007: ingester doc update).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 3 documentation row)

## Assumptions

- Only the `validation_failure()` clause in §4.6 (lines 105-108) changes; the surrounding raise/catch list stays as written.

## Design decisions

- Replace the "no `WARNING` is logged at this layer" phrasing with the routing behavior (whole group moved to `failed/`, `.error.json` names the reason); grouping-rejected files are also routed there, which the overview doc covers — keep §4.6 focused on the ingester's own failure sites (Plan Documentation Impact).

## Alternatives considered

N/A: clause-level wording update.

## Implementation
### Target file
`docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`
### Procedure

- In §4.6 Error Handling, change the `IngestUrlResult.validation_failure()` clause: the whole URL's chunk group fails and is routed to `failed/` with a `.error.json` file naming the failure reason (group signature mismatch, parse failure), instead of staying in `chunk/`.
- Note that chunk files rejected during grouping reach `failed/` the same way (one short clause).

### Method

- Keep the clause list's existing sentence structure and length comparable; behavior description only (`skills/DESIGN.md` Docs content policy).

### Details

- Verify the claim "no `WARNING` is logged at this layer" against the shipped code before removing it: sibling procedure 01 adds per-file `WARNING` lines in the grouping layer; §4.6 describes the ingester layer, so drop only the sentence this Plan's evidence (lines 105-108, no routing) pins as now-wrong.

## Compatibility considerations

- Prose must match the behavior shipped by sibling procedures 01-02; execute this document after they land (Plan Phase 3).

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Check | Command |
|---|---|
| Docs structural rules | `uv run python tools/check_docs_quality.py` |
| Docs structure | `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` |
| Docs content policy | `uv run python tools/check_docs_content_policy.py` |
| Domain claim consistency | `uv run python tools/check_docs_consistency.py --domain rag` |

## Completion criteria

- AC-5: §4.6 describes validation-failed groups as routed to `failed/` with `.error.json`; all four docs checkers pass.

## Out of Scope

- `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` (sibling procedure 05).
- §4.7 Logging section (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the §4.6 validation_failure description per Procedure | Completed | 20261106-143204 | 20261106-143204 | Execute after sibling procedures 01-02 land |
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
- **Requirement ID**: `REQ-007` (ingester §4.6 doc update)
- **Source issue**: `issues/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-115721
- **Related target files**: `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`