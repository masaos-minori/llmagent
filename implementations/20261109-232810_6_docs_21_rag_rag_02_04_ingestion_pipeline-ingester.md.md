## Goal

- State in the ingester documentation which failures are deterministic and routed to `failed/`, and which database errors stay retryable (`REQ-006`: deterministic-failure routing documented).

## Scope
**Release unit**: N/A: not part of a release unit

- Section 4.6 (Error Handling) of `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`; failure behavior only.

## Assumptions

- The routing cases at L104-110 currently cover `validation_failure()` group routing (signature mismatch, parse failure) but not the three deterministic cases this plan adds (verified in Step 3 of the plan cycle).

## Design decisions

- Extend the existing section 4.6 paragraph instead of adding a new section; keep the "See `scripts/rag/ingestion/ingester.py` for the exact raise/catch sites" framing.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
- `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`

### Procedure
- In section 4.6, name the deterministic failures that route the whole group to `failed/` with a `.error.json` reason: embedding BLOB size mismatch (`VALIDATION_FAILED`), out-of-schema `chunk_type` at read time (`PARSE_FAILED`), and `sqlite3.IntegrityError` from the commit (`STORAGE_FAILED`).

### Method
- Append to the section 4.6 list (after the existing grouping sentence at L110): deterministic integrity/validation failures are quarantined — a wrong-dimension embedding is rejected before the transaction (`VALIDATION_FAILED`), an invalid `chunk_type` is rejected at read (`PARSE_FAILED`), and a `sqlite3.IntegrityError` from `TransactionManager.commit` routes the whole group to `failed/` (`STORAGE_FAILED`), rolled back with no partial rows.

### Details
- State the contrast: every other `sqlite3.Error` (for example a lock `OperationalError`) is treated as possibly transient — files stay in `chunk/` for the next run.
- Match the enum names exactly as in `scripts/rag/exceptions.py`.

## Compatibility considerations

- Section 4.4 already documents the fixed embedding dimension constant (L91-95); the new text refers to the same `get_embedding_dims()` surface, no duplication needed.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Docs gates per `routing.md`: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` — no findings.

## Completion criteria

- Section 4.6 names the three deterministic cases with their reason values and the transient-kept rule (AC-6), and all docs checkers pass.

## Out of Scope

- Any `docs/` file other than the target; behavior changes (covered by seq-1..seq-4 documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update section 4.6 per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document deterministic-failure routing)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`
