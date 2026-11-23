## Goal

Update the version pins that the bump breaks and add tests for result classification, metadata persistence, redaction before preview, and `call_state_view`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: this file only. Verified pins: the `PRAGMA user_version` assertion expecting 1 (about line 297) and the drift test that sets `PRAGMA user_version = 2` (about line 362), which would no longer mismatch.

## Assumptions

- Verified: the table-set assertion near line 304 stays valid (columns only, three tables); the plan's claim that it needs changing is limited to the version assertions.
- Verified: `test_result_truncation` and `test_truncated_completed_is_replay_unavailable` keep the sentinel shape and must stay green unchanged.

## Design decisions

- Compare the first pin with `_USER_VERSION` and make the drift test set `_USER_VERSION + 1`, so it keeps exercising the stamp refusal after any later bump.

## Alternatives considered

Rejected: literals 2 and 3 (they break again at the next version bump).

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py`

### Procedure
1. Update the two version assertions (use `_USER_VERSION` / `_USER_VERSION + 1`).
2. Add tests: a small result stores class `complete` with correct sha256 and byte size; a 9000-character result stores `redacted_preview`; a preview containing a Bearer value, a `sig=` query parameter, and an absolute path is redacted before slicing; `record_failed` stores `replay_unavailable` with the error class as `result_code`; a supplied `external_ref` stores `secure_reference`.
3. Add `call_state_view` tests: pending with a live lease maps to in_progress, pending with an expired lease maps to reconciliation_required, completed and failed map as in the table, an unknown key returns `None`, and `attempts_exhausted` reflects `max_attempts`.
4. Add an `append_reconcile_evidence` test that checks the history row and that the ledger row is unchanged.

### Method
Use the existing `store` fixture and `now_epoch` parameters instead of sleeping.

### Details
- Use dummy secrets and fake paths in redaction inputs.

## Compatibility considerations

Existing tests keep their intent.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py`

## Completion criteria

- Version pins follow `_USER_VERSION`; classification, metadata, redaction, view, and evidence tests pass.

## Out of Scope

Identity-test fixtures (row 27) and API tests (row 29).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (result metadata and result classes at finalization), `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/shared/test_mcp_dedup.py`
