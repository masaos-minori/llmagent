# Consolidate the diagnostic guard onto the shared detector

## Goal

Replace `_SENSITIVE_PATTERNS` and its loop in `DiagnosticStore.save()` with a call to the shared
`detects_secrets` (new) function, keeping the refusal contract byte-identical (Plan REQ-001 single
implementation, REQ-004 unchanged `RuntimeError` contract and carve-outs).

## Scope

- Delete `_SENSITIVE_PATTERNS` (`scripts/agent/diagnostic_store.py:29-33`) and the now-unused
  `import re` (line 11).
- Add `from agent.secrets_masker import detects_secrets` (new) to the `from agent.` import group
  (after `agent.config_dataclasses`).
- Replace the guard block in `save()` (the `for pattern in _SENSITIVE_PATTERNS: if
  pattern.search(content)` loop at ~line 168) with one `detects_secrets(content)` (new) call raising the
  same `RuntimeError` message.
- `_filter_sensitive_fields()`, the encryption path, and everything else in `save()` untouched.

## Assumptions

- Verified 20261102: `re` is imported (line 11) and used only by `_SENSITIVE_PATTERNS` (line 30);
  the guard sits inside `if not diagnostics_cfg.encryption_key:` and `if not _filter_failed:`
  (carve-out preserved by keeping the nesting unchanged).
- `detects_secrets` (new) exists after row 01 lands (earlier-`seq` row in this Plan) — this document
  executes after it.
- Behavior widening (short values, new key names, empty-value exemption) comes from row 01's
  pattern set; this row changes no pattern text.

## Design decisions

- Keep the exception construction in `save()` (not inside `detects_secrets` (new)): the `RuntimeError`
  and its exact message are the `save()` contract callers depend on (REQ-004); the shared
  function stays a pure predicate.
- Single call site: the guard's two nested conditions collapse to
  `if not diagnostics_cfg.encryption_key and not _filter_failed and detects_secrets(content):` (new)
  only if the existing structure can hold the identical message — otherwise keep the nesting and
  swap just the loop body (either form passes AC-1/AC-4; prefer minimal diff).

## Alternatives considered

- Import `SECRET_PATTERNS` and run `search` here — rejected: re-creates the split implementation
  the Plan removes (REQ-001) and mishandles already-masked markers (Plan Decision 2).

## Implementation
### Target file
`scripts/agent/diagnostic_store.py`

### Procedure
Three edits: import group, delete the pattern block, swap the guard body.

### Method
```python
from agent.secrets_masker import detects_secrets
```
```python
        if not diagnostics_cfg.encryption_key:
            if not _filter_failed:
                if detects_secrets(content):
                    raise RuntimeError(
                        "Sensitive information detected in diagnostic content without encryption enabled."
                    )
```

### Details
- The message string must stay byte-identical (AC-4); `save()`'s docstring is untouched.
- No change to the `encrypt and diagnostics_cfg.encryption_key` branch below the guard.

## Compatibility considerations

- Callers (`session.py`, `session_persister.py`, `orchestrator`, `llm_transport_errors.py`,
  `repl`, `error_injection_service.py`) keep the same exception type and message; the widened
  detection surface is UNK-03, recorded for an owner decision (this row changes no caller).
- The old guard's 16-char minimum disappears (row 01 decision): short secrets now refuse; pinned
  by row 04's tests.

## Security considerations

- Closes the Issue's core gap: guard and masker can no longer drift apart (one pattern list).

## Rollback considerations

- Revert this commit; `_SENSITIVE_PATTERNS` returns with it. Revert before row 01's revert if both
  landed (the guard would otherwise call a missing function).

## Validation plan

- `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_diagnostic_store.py
  tests/agent/test_regression_diagnostic_persist.py` — new and pre-existing guard tests pass.
- `uv run pytest tests/agent/test_session_persister.py tests/agent/test_http_lifecycle_command_validator.py
  tests/agent/test_startup_mcp_starter.py` — unchanged (caller regression).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`,
  `uv run python tools/check_module_size.py`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`,
  `uv run lint-imports`.

## Completion criteria

- `rg "_SENSITIVE_PATTERNS" scripts/agent/diagnostic_store.py` returns nothing; the file no longer
  imports `re`; `save()` refuses exactly what `detects_secrets` (new) flags with the unchanged message;
  the encrypted path and `_filter_failed` carve-out pass their tests unchanged (AC-1, AC-4).

## Out of Scope

- Pattern content (row 01); tests (rows 03-04); caller `RuntimeError` handling (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Swap the guard block for `detects_secrets` (new) and delete `_SENSITIVE_PATTERNS` + `re` import | Completed | — | — | After row 01 lands (Plan Phase 3) _SENSITIVE_PATTERNS removed; guard consolidated onto detects_secrets; message byte-identical; red phase 12 failed/32 passed resolved; 151 targeted tests green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy, bandit -ll -r scripts/, lint-imports (6 kept), check_module_size, full suite 11276 passed/8 skipped, diff-cover 100%, docs checkers exit 0 |

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
- **Requirement ID**: REQ-001 (guard calls the shared function), REQ-004 (refusal contract unchanged)
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: scripts/agent/diagnostic_store.py