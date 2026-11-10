## Goal

- Document the stale-skip rule and the `file://` / `force` exceptions in the ETagManager section of the supporting-components documentation (`REQ-005`: doc states the rule).

## Scope
**Release unit**: N/A: not part of a release unit

- Section 4.9 of `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`; failure behavior only.

## Assumptions

- Section 4.9 currently states the stale guard for DB values ("the existing DB values are preserved", L31) but is silent about `chunks` / `chunks_vec` (verified in Step 3 of the plan cycle).

## Design decisions

- Add one short subsection (4.9.2) after 4.9.1 stating the whole-replacement skip and the two exceptions; keep 4.9's intro and 4.9.1 edge-case list unchanged.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`

### Procedure
- State that for HTTP documents without `force`, a stale incoming generation skips the whole replacement in `TransactionManager.commit` (no delete, no insert; chunks and `chunks_vec` untouched; the files are routed as a skip), and that `file://` sources and `force=True` are exceptions where the incoming generation always wins and its metadata is persisted with it.

### Method
- Under section 4.9, after 4.9.1, add `### 4.9.2 Stale payload skips the replace` with: the HTTP stale-skip rule (returns the skip outcome; content and validators stay at the stored generation), the `file://` exception (content hash is the change signal, older mtime does not block replacement), and the `force` exception (operator intent wins over freshness).

### Details
- Name the consumer (`scripts/rag/ingestion/transaction_commit.py`) the way 4.9 already names its subjects; no line-number citations.

## Compatibility considerations
N/A: docs-only; no other doc references 4.9's chunk behavior.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Docs gates per `routing.md`: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` — no findings.

## Completion criteria

- Section 4.9 states the stale-skip rule and both exceptions, and all docs checkers pass (AC-5).

## Out of Scope

- The `DocumentManager` HTTP skip decision (ragrev010), UNK-02's both-`None` fetched_at semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add subsection 4.9.2 per Implementation > Procedure/Method/Details | Completed | 20261110-1030 | 20261110-1045 | Added `### 4.9.2 Stale Payload Skips the Replace` after 4.9.1: HTTP stale-skip skips the whole replace (no delete/insert; chunks/chunks_vec untouched; files routed as skip); `file://` (content hash is the change signal, older `fetched_at` does not block) and `force=True` (operator intent wins) are the two exceptions that persist incoming metadata. 4.9 intro and 4.9.1 unchanged. Gate (plans/...ragrev015 phase 3) evaluated stale — cleared per prior user approval. |
| 2 | Run the documentation checkers (Validation plan) | Completed | 20261110-1045 | 20261110-1050 | check_docs_quality ✓ / check_docs_structure ✓ / check_docs_content_policy ✓ / check_docs_consistency --domain rag ✓ / check_docs_japanese ✓ — no findings. |

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
- **Requirement ID**: `REQ-005` (document the stale-skip rule and exceptions)
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234108
- **Related target files**: `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`
