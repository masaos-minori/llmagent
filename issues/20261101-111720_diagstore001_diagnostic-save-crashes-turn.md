# Unhandled RuntimeError from DiagnosticStore.save crashes the interactive turn

## Priority

Medium

## Summary

Contain the best-effort `DiagnosticStore.save()` refusal so a sensitive-pattern rejection (a raised `RuntimeError`) degrades to a logged warning instead of propagating out of the LLM turn and surfacing as a fatal, user-visible error.

## Background

`DiagnosticStore.save()` enforces an opt-in encryption posture: when no encryption key is configured and the redacted payload matches `_SENSITIVE_PATTERNS`, `save()` raises `RuntimeError("Sensitive information detected in diagnostic content without encryption enabled.")` instead of persisting. This is intentional at the unit level — `tests/agent/test_diagnostic_store_security.py` asserts `pytest.raises(RuntimeError, match="Sensitive information detected")`. The shipped default ships an empty key (`config/agent.toml` `[diagnostics] encryption_key = ""`), so the refusal path is live by default.

Diagnostics are a best-effort channel: `save()` already catches `_filter_sensitive_fields` failures and logs them (`scripts/agent/diagnostic_store.py` lines 156-166) so persistence proceeds without filtering. Two turn-path call sites do not share that discipline. Confirmed by reading current source (evidence label: Confirmed by repository evidence; confidence: high).

## Problem

The two turn-path callers of `DiagnosticStore.save()` do not catch the `RuntimeError`, so a sensitive-pattern match turns a best-effort diagnostic write into an unhandled exception that breaks the turn.

Callers:
- `LLMTurnRunner._handle_llm_error` (`scripts/agent/llm_turn_runner.py` ~line 202 and ~line 218): saves transport-failure / partial-text diagnostics with no `try/except` around the `save()` calls.
- `ToolLoopGuard._save_guard_hint` (`scripts/agent/tool_loop_guard.py` ~line 151): called from `check_empty_result_repeat`, `check_unavailable_repeat`, `check_dedup`, `check_retry`, `check_cycle`, and `_check_progress_stagnation`; none wrap the `save()` call. Five of these run inside `ToolLoopGuard.check_all` (`scripts/agent/tool_loop_guard.py` lines 433-444); `check_unavailable_repeat` is invoked directly from `LLMTurnRunner.run()` (`scripts/agent/llm_turn_runner.py` line 173), so it is on the turn path even though it is not part of `check_all`.

Propagation path:
`save()` raises → `LLMTurnRunner.run()` (only `except LLMTransportError`, line 127) → `LlmTurnExecutor.handle_llm_turn` (`try/finally` only, `scripts/agent/llm_turn_executor.py` lines 95-108) → `WorkflowEngineAdapter._run_execute_stage` (`scripts/agent/workflow_engine_adapter.py` line 344) → REPL generic handler → `_surface_turn_error` → `view.write_fatal(f"{exc.__class__.__name__}: {exc}")`.

Net effect: a mid-turn LLM error or guard event that happens to carry sensitive-looking text surfaces to the operator as a fatal `RuntimeError` instead of the normal graceful fail `TurnResult`, and the turn's own error-handling path is bypassed.

## Reason for Change

The current behavior lets a side-channel (diagnostics) abort the primary turn. The security boundary (no unencrypted secret persisted) is preserved either way, but the crash is an unintended blast radius for a non-critical, best-effort subsystem. It is reachable today with the shipped default (empty `encryption_key`) whenever a diagnostic payload contains a string matching the sensitive pattern — for example partial LLM output or an error detail that echoes a token, `api_key`, or `password`.

## Implementation Intent

Contain the `RuntimeError` at the best-effort boundary. The responsibility: a diagnostic save must never propagate a refusal or I/O failure into the turn. Options:
- (a) Wrap the `save()` calls in the two turn-path callers with a narrow `try/except` that logs a warning and continues, mirroring the existing `_filter_sensitive_fields` failure handling inside `save()`.
- (b) Centralize by having `save()` convert the sensitive-pattern refusal into a logged skip (log + return) instead of raising, so every caller inherits safe degradation.

Prefer (b) only if it does not contradict the unit-test contract; otherwise (a). Preserve the security property (detected-sensitive content is still not written in plaintext) and the unit-level raise contract used by the existing tests.

## Target Files or Areas

- `scripts/agent/diagnostic_store.py` (`DiagnosticStore.save`)
- `scripts/agent/llm_turn_runner.py` (`_handle_llm_error`)
- `scripts/agent/tool_loop_guard.py` (`_save_guard_hint`)
- `tests/agent/test_diagnostic_store_security.py` (contract reference)

## Required Changes

- Ensure a sensitive-pattern refusal (or any exception) from `DiagnosticStore.save()` cannot escape the turn path.
- Log the refusal at warning level with `session_id` and `kind` for observability.
- Preserve that detected-sensitive content is still not persisted unencrypted (security boundary).
- Keep the unit-level raise behavior that existing tests assert, OR update those tests if the refusal is converted to a logged skip.

## Constraints

- Must not weaken the security boundary: sensitive-looking content must still not be written in plaintext.
- Must not change the `_SENSITIVE_PATTERNS` detection logic or the `_SENSITIVE_FIELDS` allowlist.
- Must preserve public turn behavior for non-sensitive payloads (no new errors, no dropped answers).
- If the fix is localized to the two callers, do not touch other `save()` call sites.

## Acceptance Criteria

- [ ] A `DiagnosticStore.save()` that hits the sensitive-pattern refusal with an empty encryption key no longer raises out of `_handle_llm_error` or `_save_guard_hint`.
- [ ] The refusal is logged at warning with `session_id` and `kind`.
- [ ] Sensitive content is still not persisted in plaintext (security boundary intact).
- [ ] A normal (non-sensitive) turn completes and returns its `TurnResult` unchanged.
- [ ] Existing `diagnostic_store` tests pass; any test asserting the raise is updated consistently.

## Testing Expectations

- Unit: add a test that calling the two turn-path callers with a mock `ctx.diagnostics` whose `save()` hits the sensitive-pattern refusal does not propagate a `RuntimeError` and produces a warning log record.
- Regression: run `tests/agent/test_diagnostic_store_security.py` and the full agent turn/session suite.
- Type / lint: `mypy` and `ruff` clean on changed files.

## Documentation Impact

If the refusal is converted to a logged skip in `save()`, record the changed failure behavior in the `DiagnosticStore.save` docstring (failure behavior / operational note). Do not add implementation details forbidden by `skills/DESIGN.md` docs policy.

## Out of Scope

- Changing the sensitive-pattern regex or the sensitive-field allowlist.
- Deciding the production encryption posture (owned by a separate issue).
- Encrypting other tables.

## Dependencies

- depends on `issues/done/20261025-210357_config001_diagnostics-encryption-posture.md`: if production enables a Fernet key (`[diagnostics] encryption_key`), the empty-key trigger in `save()` no longer fires and this crash path becomes unreachable in production. Re-verify against current source after that issue resolves; the robustness gap remains for any deployment still shipping an empty key.

## Unresolved Questions

- Whether converting the raise to a logged skip in `save()` (option b) is acceptable to the owner, since it changes the unit-level contract asserted by `tests/agent/test_diagnostic_store_security.py` (不明: which containment approach — caller-local vs. `save()`-centralized — the owner prefers).
- Whether guard-hint payloads can ever contain a sensitive-pattern match in practice, or whether the reachable trigger is limited to the `_handle_llm_error` partial-text / error-detail path (不明: confirm via a payload survey).

## AI Implementation Instruction

Do not change `_SENSITIVE_PATTERNS`, `_SENSITIVE_FIELDS`, or the encryption decision. Preserve that sensitive content is never written unencrypted. Choose caller-local `try/except` (minimal, preserves the unit raise contract) or a `save()`-level logged skip only if the owner accepts updating the security tests. Add a regression test proving the turn path no longer raises. Stop and report if the reachability of the guard-hint trigger is unclear.

## Traceability

- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-111720
- **Related target files**: `scripts/agent/diagnostic_store.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_loop_guard.py`
