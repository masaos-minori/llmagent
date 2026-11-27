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
- Step 3b correction (UNK-02): a collision was found — `TerminationOutcome` values describe
  termination semantics and cannot classify startup failures (command not found, log-directory
  creation failure, arbitrary `ValueError` messages), so a dedicated `StartupCode` StrEnum is
  added. `code` is a dataclass field with default `StartupCode.GENERAL`; call sites are not
  changed (user decision), so the vocabulary starts with `GENERAL` and gains values as call
  sites adopt codes.
- Step 3b correction: `reason` is free text, so `redact_path` is applied to each absolute-path
  substring found in it, not to the whole string.

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
- Step 3b correction: the claim above is wrong for tests that pin the rendered string. Three
  assertions in `tests/agent/test_lifecycle.py` (`TestHttpStartupError`) compare `str(err)` and
  were updated to the new `"{server_key}: {code}: {reason}"` form in this cycle.
- Step 3b correction: the class docstring must not carry a requirement marker, because
  `tools/check_docs_quality.py` reads it into the generated reference table and flags traceability
  text in an active document. The docstring was reduced to the current-behavior sentence and the
  table regenerated with `tools/generate_reference_table.py --manifests`.

## Security considerations

- This is the public-facing disclosure boundary for REQ-002 (AC-1): no absolute path, raw config
  value, command path, or token-derived detail may appear in the rendered text.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit: safe summaries and stable codes — `uv run pytest tests/agent/test_http_lifecycle.py`.
- Step 3b correction: `tests/agent/test_http_lifecycle_command_validator.py` is not listed as a
  companion, but seven assertions there pin the unredacted absolute path in the rendered error
  (`str(exe.resolve()) in str(exc_info.value)`, `/opt/llm/bin`, and one `str(error)` equality without
  the code). They were updated to the redacted form — basename or logical identifier plus the code — as
  a fallout change per the owner's decision; the producer is unchanged. 85 passed; the file's one
  pre-existing mypy `unused-ignore` error is unchanged.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-004000 | UNK-02 collision found: dedicated StartupCode StrEnum added; code field with default GENERAL (user decision); redact_path applied per absolute-path substring in reason |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-004000 | assertions live in `tests/agent/test_http_lifecycle.py` (its own document) no test change this cycle; assertions added by procedure 14; existing tests/agent/test_http_lifecycle.py 15 passed pinned str(err) assertions in tests/agent/test_lifecycle.py TestHttpStartupError updated to the new render form (3 tests) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; changed files: scripts/agent/http_lifecycle_errors.py, registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md; awaiting end-of-batch full suite gates pass; changed files: scripts/agent/http_lifecycle_errors.py, registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md; awaiting end-of-batch full suite |

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