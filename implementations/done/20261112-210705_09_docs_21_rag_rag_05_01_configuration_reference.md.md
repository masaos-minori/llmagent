## Goal

Add `rag_pipeline_service_url` to the rejected removed-key sentence in `docs/21_rag/rag_05_01-configuration-reference.md` (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `rag_05_07` contains no gate wording and is not edited (verified in the Plan).
- The sentence currently lists the three already-rejected keys; adding the fourth keeps it accurate.

## Design decisions

- Insert `rag_pipeline_service_url` into the enumerated key list, before `rag_identity_mismatch_policy`, preserving Oxford-comma style.

## Alternatives considered

N/A: single-list insertion in a docs sentence; no design trade-off.

## Implementation
### Target file
`docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure
Add the key to the rejected removed-key sentence.

### Method
Edit.

### Details
Change the bullet under the `config/agent.toml` section (line ~92):

```
- RAG has no remote-delegation keys: a configuration file that carries `rag_query_service_url`, `rag_auth_token`, or `rag_identity_mismatch_policy` is rejected when it is loaded.
```

to:

```
- RAG has no remote-delegation keys: a configuration file that carries `rag_query_service_url`, `rag_auth_token`, `rag_pipeline_service_url`, or `rag_identity_mismatch_policy` is rejected when it is loaded.
```

## Compatibility considerations

Documentation only; no code impact.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- All report no findings.

## Completion criteria

`rag_05_01` lists `rag_pipeline_service_url` among the rejected removed keys; the docs checkers pass.

## Out of Scope

Any config value or file list beyond the one sentence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 2 | Add or update tests per Validation plan | Completed | 20261112-215927 | 20261112-215927 | N/A: documentation-only change (no tests) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |

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
- **Requirement ID**: REQ-006 — name `rag_pipeline_service_url` among rejected removed keys
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: docs/21_rag/rag_05_01-configuration-reference.md
