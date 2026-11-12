## Goal

Reword the two RAG startup-consistency warnings in `scripts/agent/startup_validation.py` so they no longer describe a gate that refuses fallback or cite `REQ-007`, while keeping severity, the `RAG identity-unverified:` prefix, and the continue-startup behavior (REQ-005 / AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `tests/agent/test_startup_validation.py` asserts only the `RAG identity-unverified:` prefix, the "timed out" case, and the failure category; it does not assert the gate text, so rewording is safe.
- The identity gate still fails closed where fallback is decided; this module only stops *describing* that clause.

## Design decisions

- Drop only the "the gate refuses fallback while unverified (REQ-007)" clause and the `REQ-007` reference in the adjacent comment; keep "startup continues" and the prefix. Append "with the corpus identity unverified" so the operator still learns the identity is unverified.

## Alternatives considered

Ending the sentence at "startup continues." was considered but drops the operator signal that identity is still unverified; the appended clause preserves it without the gate claim.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
Reword the `TimeoutError` warning, the adjacent comment, and the generic-exception warning.

### Method
Edit.

### Details
1. Comment on the `except Exception` handler (line ~253):

```
            # the unverified state is fail-closed at the gate (REQ-007), not here.
```

to:

```
            # the unverified state is fail-closed downstream, not here.
```

2. The `TimeoutError` warning:

```
            pipeline.add_warning(
                "rag_consistency",
                "RAG identity-unverified: consistency check timed out after 30s; "
                "startup continues but the gate refuses fallback while unverified "
                "(REQ-007).",
            )
```

to:

```
            pipeline.add_warning(
                "rag_consistency",
                "RAG identity-unverified: consistency check timed out after 30s; "
                "startup continues with the corpus identity unverified.",
            )
```

3. The generic-exception warning:

```
            pipeline.add_warning(
                "rag_consistency",
                "RAG identity-unverified: "
                f"{category} ({type(exc).__name__}): {exc}; startup continues but "
                "the gate refuses fallback while unverified (REQ-007).",
            )
```

to:

```
            pipeline.add_warning(
                "rag_consistency",
                "RAG identity-unverified: "
                f"{category} ({type(exc).__name__}): {exc}; startup continues "
                "with the corpus identity unverified.",
            )
```

## Compatibility considerations

Severity, warning category (`rag_consistency`), and fail-open-with-warning behavior are unchanged.

## Security considerations

N/A: warning-text change only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `rg -n "gate refuses fallback" scripts docs` returns nothing (AC-5).
- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py` pass unchanged.
- `uv run ruff format` / `ruff check` clean.

## Completion criteria

Neither warning nor the comment mentions a gate refusing fallback or `REQ-007`; behavior is unchanged.

## Out of Scope

The `RAG identity-unverified:` prefix (kept; decided by `rmcompat003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 2 | Add or update tests per Validation plan | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
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
- **Requirement ID**: REQ-005 — reword the two startup warnings without the gate clause or `REQ-007`
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: scripts/agent/startup_validation.py
