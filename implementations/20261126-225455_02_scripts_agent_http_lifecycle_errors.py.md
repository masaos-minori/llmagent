## Goal

Make the public lifecycle error summary safe for terminal capture: stable error codes and no
absolute paths in public error text (REQ-002 — safe public summaries).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `__str__` already masks the stderr tail through `_mask_secrets`; only the `reason` component is
  unsafe today (it can embed the absolute log directory).
- Needs confirmation (non-blocking, Plan UNK-02): the stable public error-code vocabulary is
  decided at implementation against the existing `StrEnum` values in this module; existing values
  are kept as the code set unless a collision is found.
- No overlap with a sibling Plan on this file.

## Design decisions

- Add a stable code field to `StartupFailure` so `__str__` prints `code` instead of the raw
  `reason` when the reason contains a path.
- Redaction of the `reason` uses `redact_path` from `scripts/agent/secrets_masker.py` (document 01),
  not a local regex.

## Alternatives considered

- Introducing a dedicated error-code enum — deferred to implementation per UNK-02; rejected as a
  pre-decision because the existing `StrEnum` already provides the code set.

## Implementation
### Target file
`scripts/agent/http_lifecycle_errors.py`
### Procedure
- Add `code` (new) to `StartupFailure` with the stable code value.
- In `HttpStartupError.__str__`, print the code plus a redacted summary; redact the `reason`
  through `redact_path` (new helper, document 01) before truncation.
### Method
- `__str__` builds `"{server_key}: {code}: {redacted_reason}"`; the stderr tail continues to go
  through `_mask_secrets` with the existing 512-byte tail.
- Redaction happens before truncation, so a truncated tail cannot cut a masked value open.
### Details
- No call sites change: `reason` remains a field, only its rendering changes.
- `TerminationOutcome` values are reused as the code set unless a collision is found (UNK-02).
- The assertions for this change are added in `tests/agent/test_http_lifecycle.py`, which is not a
  companion here because that test row is also cited by the `scripts/agent/http_lifecycle.py` row;
  it has its own procedure document.

## Compatibility considerations

- Public error text changes; consumers that compare `reason` values are unaffected because the
  field itself is unchanged.

## Security considerations

- This is the public-facing disclosure boundary for REQ-002 (AC-1): no absolute path, raw config
  value, command path, or token-derived detail may appear in the rendered text.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit: safe summaries and stable codes — `uv run pytest tests/agent/test_http_lifecycle.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A `StartupFailure` whose `reason` contains the log directory renders without an absolute path,
  and the rendered code is stable across runs.

## Out of Scope

- Process ownership and health semantics (issues cliplc007, cliplc008).
- Changing `_mask_secrets` behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | assertions live in `tests/agent/test_http_lifecycle.py` (its own document) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (stable public error codes and safe summaries)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/http_lifecycle_errors.py`
