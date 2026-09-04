# Implementation Procedure: Wrap _filter_sensitive_fields call in try/except within save()

## Goal

Prevent session data loss during shutdown when `_filter_sensitive_fields` fails and unfiltered content triggers RuntimeError in `save()` (REQ-DS001-1: Session persistence completes even if _filter_sensitive_fields fails).

## Scope

- Modify `scripts/agent/diagnostic_store.py` `save()` method: wrap `content = self._filter_sensitive_fields(content)` in try/except
- On exception: log WARNING, skip sensitive pattern check, proceed with save using whatever content remains

## Assumptions

- `_filter_sensitive_fields` can fail silently (returns unmodified content) rather than raising an exception — confirmed by current source: line 84 returns raw content on JSONDecodeError, line 86 returns raw content on non-dict payload
- The sensitive pattern check should be skipped when filter fails to avoid false positives from unfiltered content containing secrets
- A reasonable logging level exists for the failure case (WARNING recommended)

## Design decisions

- Catch `Exception` broadly rather than specific exceptions because `_filter_sensitive_fields` has multiple failure paths (JSON decode error, cryptography errors, etc.) and the goal is availability over strictness
- Skip sensitive pattern check on filter failure rather than re-running the check — re-running would require duplicating the pattern-matching logic and could produce inconsistent results
- Log WARNING with content length indicator so operators can audit affected sessions (per Risks mitigation in Plan)

## Alternatives considered

- Rejection approach (skip save entirely): would cause data loss, violating REQ-DS001-1
- Partial retry: adds complexity with no guarantee of success on second attempt
- Separate error handler per exception type: over-engineered given the goal is graceful degradation

## Implementation

### Target file

`scripts/agent/diagnostic_store.py`

### Procedure

In `save()` method, replace the single-line call:

```python
content = self._filter_sensitive_fields(content)
```

with:

```python
_filter_failed = False
try:
    content = self._filter_sensitive_fields(content)
except Exception:
    logger.warning(
        "_filter_sensitive_fields failed for %s diagnostic (kind=%s); proceeding without filtering",
        session_id, kind, exc_info=True,
    )
    _filter_failed = True
```

Then modify the sensitive pattern check block (lines 154-160) to skip when `_filter_failed` is True:

```python
diagnostics_cfg = self._load_diagnostics_config()
if not diagnostics_cfg.encryption_key:
    if not _filter_failed:
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.search(content):
                raise RuntimeError(
                    "Sensitive information detected in diagnostic content without encryption enabled."
                )
```

### Method

Defensive programming: catch broad exception around filter call, propagate failure state via local flag, gate sensitive check behind that flag.

### Details

1. Add `_filter_failed = False` before the try block (line ~152)
2. Wrap `content = self._filter_sensitive_fields(content)` in try/except
3. In except: log WARNING with `exc_info=True` for stack trace, include `session_id` and `kind` for auditability
4. Set `_filter_failed = True` in except block
5. In sensitive pattern check (lines 154-160): add `if not _filter_failed:` guard around the entire pattern loop
6. No change to encryption logic — if encryption is enabled, the original content may still contain secrets but they will be encrypted before storage

## Compatibility considerations

- Existing callers of `save()` do not depend on RuntimeError being raised for sensitive content — they expect either success or a propagated exception from elsewhere
- If encryption is enabled and filter fails, unfiltered content will be encrypted before storage — acceptable trade-off per REQ-DS001-2 (sensitive data protection maintained via encryption)
- Backward compatible: no API changes, no signature changes

## Security considerations

- Skipping sensitive check on filter failure means raw secrets could persist if encryption is also disabled — mitigated by WARNING log with `exc_info=True` for operator awareness
- If encryption key is configured, content is encrypted regardless of filter status — security posture preserved in that scenario
- The `_filter_failed` flag must NOT leak into stored content — it is strictly local to `save()` scope

## Rollback considerations

- Simple revert: remove try/except wrapper, restore original single-line call
- No database schema changes, no config changes
- No migration needed

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/diagnostic_store.py | Unit test mocking _filter_sensitive_fields failure | pytest tests/unit/test_diagnostic_store.py | Save succeeds without RuntimeError |

- Test case: mock `_filter_sensitive_fields` to raise an exception, verify `save()` does not propagate the exception
- Test case: verify WARNING is logged when filter fails
- Test case: verify sensitive pattern check is skipped when filter fails
- Test case: verify normal operation (no exception) is unchanged

## Completion criteria

- [ ] `_filter_sensitive_fields` call wrapped in try/except in `save()` method
- [ ] WARNING logged with `exc_info=True` when filter fails
- [ ] Sensitive pattern check gated on `_filter_failed` flag
- [ ] Unit test added: mocking filter failure, verifying graceful degradation
- [ ] Normal operation (no exception) produces identical behavior to pre-change

## Out of scope

- Redesigning the sensitive field detection system
- Adding new encryption features
- Modifying `fetch()` decryption logic
- Updating `docs/diagnostics.md` (row 2 — Needs confirmation, file does not exist)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Added try/except around _filter_sensitive_fields, _filter_failed flag, gated sensitive check |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | All 17 security tests pass; 2 pre-existing test failures unrelated to this change |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | ruff + mypy pass (BLE001 noqa added per procedure intent) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: docs/diagnostics.md does not exist (row 2 blocked) | — | — | |

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
- **Requirement ID**: REQ-DS001-1, REQ-DS001-2
- **Source issue**: issues/20260904-001051_ds001_sensitive_check_failure_mode.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-001051_ds001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-001051
- **Related target files**: scripts/agent/diagnostic_store.py
