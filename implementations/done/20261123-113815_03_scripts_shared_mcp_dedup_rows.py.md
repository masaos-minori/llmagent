## Goal

Classify a stored result once at store time: compute the hash, size, and result class, redact before the preview is created, and extend the row and view types with the metadata.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `DedupRow` fields, `_row_from_record`, the stored-result classification built on `_cap_result`, and the new `CallStateView` (new) projection type. The module must stay under the 24,576 B size gate (now about 4.3 KB).

## Assumptions

- Verified: the plan evidence named a nonexistent prepare_completed_record; the real hook is `_cap_result` (it already hashes the full serialized payload and builds the truncated sentinel). Plan corrected in this cycle.
- Verified: `_acquire_locked` reads the stored sentinel shape (`truncated`, `sha256`, `preview`), so that shape must not change.
- Verified: no redaction exists upstream (`dispatch.py` passes the raw result), so the preview redaction is implemented here.

## Design decisions

- Add `StoredResult` (new) (frozen dataclass: `payload`, `sha256`, `size_bytes`, `result_class`) and `classify_result(result)`; keep `_cap_result` returning the payload string by delegating to it so existing callers are unchanged.
- Classification: serialized length <= `RESULT_MAX_CHARS` gives `complete`; longer gives `redacted_preview` (new). `sha256` and `size_bytes` always describe the full serialized payload (UTF-8).
- `redact_preview(text)` masks Bearer values, secret-like query parameters (sig, signature, token, key, secret, password), and absolute filesystem paths (/home, /opt, /var, /tmp, /root, /Users); the preview is `redact_preview(serialized)[:RESULT_PREVIEW_CHARS]`, so redaction precedes truncation.

## Alternatives considered

Rejected: redacting the stored full result (replay of a `complete` result must return the exact payload; redaction applies to previews only).

## Implementation
### Target file
`scripts/shared/mcp_dedup_rows.py`

### Procedure
1. Add the five optional fields to `DedupRow` (default `None`) and read them in `_row_from_record`.
2. Add `StoredResult` (new), `redact_preview` (new), and `classify_result` (new); make `_cap_result` return `classify_result(result).payload`.
3. Add the frozen `CallStateView` (new) dataclass (key, tool_name, ledger_status, attempt_number, lease_live, lease_expires_epoch, result_class, result_code, result_size_bytes, result_sha256, external_ref, attempts_exhausted, agent_state, reconciliation_required, error_code).

### Method
Pure functions and dataclasses; no SQL here. `CallStateView.agent_state` is filled by the ledger through `agent_state_for` from the contract module.

### Details
- `secure_reference` (new) is selected by the ledger only when an `external_ref` is supplied; `classify_result` (new) itself returns `complete` or `redacted_preview` (new).
- Keep `json.dumps(..., ensure_ascii=False)` so the character-based cap is unchanged.

## Compatibility considerations

Existing construction of `DedupRow` keeps working through defaults; the stored sentinel is byte-compatible.

## Security considerations

Redaction runs before preview creation; `sha256` is of the full payload and reveals nothing. The view type carries no raw arguments, paths, or exceptions.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py` (row 26 adds the classification and redaction tests)
- `uv run python tools/check_module_size.py --top 5` stays green

## Completion criteria

- `classify_result` (new) returns the right class, hash, and size; the preview is redacted before slicing; `DedupRow` and `CallStateView` (new) carry the metadata; the sentinel shape is unchanged.

## Out of Scope

SQL changes (row 04) and re-exports (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-135004 | 20261123-135004 | StoredResult, classify_result, redact_preview, CallStateView, DedupRow fields |
| 2 | Add or update tests per Validation plan | Completed | 20261123-135004 | 20261123-135004 | row 26 TestResultMetadata |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-135004 | 20261123-135004 | gates pass |

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
- **Requirement ID**: `REQ-003` (result metadata and result classes at finalization)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/mcp_dedup_rows.py`
