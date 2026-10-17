## Goal

Make the `requested_target` value that `scripts/mcp_servers/audit.py` already accepts reach the
audit log, so a call that was rejected before path resolution still records the caller-supplied
path alongside the canonical one (REQ-003: the parameter is accepted and then discarded).

## Scope

- Add the optional `requested_target` key to `AuditRecord`.
- Emit it from `_build_audit_record` when the caller supplies a non-empty value.
- No signature, parameter, or call-site change: `scripts/mcp_servers/git/git_server.py` already
  passes the value at three call sites.

## Assumptions

- Only callers that already redact the value pass it; `scripts/mcp_servers/git/git_server.py`
  passes the output of `_sanitize_for_audit`.
- Consumers read the record by key and tolerate a missing optional key, which is already true for
  `canonical_target`, `detail`, `pre_condition`, and `post_condition`.

## Design decisions

- Emit only when non-empty, mirroring the existing `canonical_target` handling, so servers that
  never supply the value keep their current key set.
- Declare the key immediately before `canonical_target` in `AuditRecord` so the requested/canonical
  pair reads as one concept.

## Alternatives considered

- Always emit the key with an empty string: rejected — it changes the record shape for every MCP
  server and breaks the whole-record comparisons in `tests/agent/test_audit_log_format.py`.

## Implementation

### Target file

`scripts/mcp_servers/audit.py`

### Procedure

1. Add `requested_target: NotRequired[str]` (new) to `AuditRecord`, immediately above the existing
   `canonical_target` entry.
2. Add the conditional assignment in `_build_audit_record`, immediately above the existing
   `canonical_target` assignment.

### Method

Copy the shape of the existing `canonical_target` emission: a truthiness test on the parameter
followed by one key assignment. No normalization, truncation, or path handling is added at this
layer — redaction stays the caller's responsibility.

### Details

- `AuditRecord` currently ends with `canonical_target: NotRequired[str]` at
  `scripts/mcp_servers/audit.py:57`.
- `_build_audit_record` currently ends with `if canonical_target:` at
  `scripts/mcp_servers/audit.py:116-118`; the new block is inserted above it:

```
    if requested_target:
        record["requested_target"] = requested_target
```

- The parameter already exists on both `_build_audit_record`
  (`scripts/mcp_servers/audit.py:71`) and `_audit_log` (`scripts/mcp_servers/audit.py:132`), and
  `_audit_log` already forwards it to `_build_audit_record`; neither signature changes.

## Compatibility considerations

- Additive optional key only. `orjson.OPT_SORT_KEYS` serialization order is unaffected because
  ordering is applied at serialization time, not at dict construction.
- Existing record-shape tests compare every field except `ts`; they keep passing because the key is
  absent unless a caller supplies it.

## Security considerations

- The value is a caller-supplied path. This layer must not resolve, normalize, or widen it; the only
  current supplier already redacts it.
- The field records a path identity only — never file content, token, or command text.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/agent/test_audit_log_format.py tests/mcp_servers/git/test_git_service_dispatch.py`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`
- `uv run python tools/generate_reference_table.py --check` (this file is in the generated-reference domain)

## Completion criteria

- A record built with a non-empty `requested_target` contains that key with the supplied value, and
  a record built without it does not contain the key (AC-002).
- The Git audit-record tests that already pass the value still pass, and no other server's record
  shape changed.

## Out of scope

- Changing the `_audit_log` or `_build_audit_record` signatures.
- Supplying `requested_target` from the file servers (Plan target rows 2 and 3).
- Documenting the field (Plan target row 17's procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `requested_target` key to `AuditRecord` and the conditional emission in `_build_audit_record` | Pending | — | — | REQ-003 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests are owned by Plan row 11 |
| 3 | Confirm `tools/generate_reference_table.py --check` passes | Pending | — | — | Generated-reference domain |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `scripts/mcp_servers/audit.py`
