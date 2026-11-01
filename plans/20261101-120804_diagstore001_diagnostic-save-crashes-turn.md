# Plan: Contain DiagnosticStore.save() RuntimeError so a sensitive-pattern refusal degrades to a warning instead of crashing the turn

**Task Classification:** Path B (more than 3 files; touches the `DiagnosticStore.save` contract surface and two turn-path callers; adds regression tests). Path B analysis applied (`skills/issue-to-plan/workflow-path-b.md`); design choices recorded in `Design`.

## Goal
- Contain the best-effort `DiagnosticStore.save()` sensitive-pattern refusal so a raised `RuntimeError` degrades to a logged warning and never propagates out of the interactive LLM turn, while preserving the no-unencrypted-secret-persisted security boundary and the unit-level raise contract asserted by existing tests.

## Priority

Medium

## Scope
- **In-Scope**:
  - Contain the `RuntimeError` from `DiagnosticStore.save()` on the two live turn-path call sites (`LLMTurnRunner._handle_llm_error`, `ToolLoopGuard._save_guard_hint`) so a refusal or I/O failure cannot escape the turn.
  - Log the refusal at warning level with `session_id` and `kind` for observability.
  - Preserve that detected-sensitive content is still not persisted unencrypted.
  - Add a regression test proving the two turn-path callers no longer propagate a `RuntimeError` when `save()` hits the sensitive-pattern refusal, and produce a warning log record.
  - Leave `tests/agent/test_diagnostic_store_security.py` unchanged under the recommended option (a); update it only if the owner selects option (b) and the unit-level raise contract is converted to a logged skip.
- **Out-of-Scope**:
  - Changing `_SENSITIVE_PATTERNS` detection logic or `_SENSITIVE_FIELDS` allowlist.
  - Deciding the production encryption posture (owned by `issues/done/20261025-210357_config001_diagnostics-encryption-posture.md`).
  - Encrypting other tables.
  - Touching the other `save()` call sites outside the two identified turn-path callers under option (a).
  - Fixing the same-pattern call sites in `scripts/agent/llm_transport_errors.py` and `scripts/agent/error_injection_service.py` (no production caller; see `Design`).
- **Dependencies**:
  - `issues/done/20261025-210357_config001_diagnostics-encryption-posture.md` (closed): if production enables a Fernet key, the empty-key trigger in `save()` no longer fires and this crash path becomes unreachable in production. Closed dependency — no sequencing gate. Re-verify against current source after that issue resolves; the robustness gap remains for any deployment still shipping an empty key.

## Background

`DiagnosticStore.save()` enforces an opt-in encryption posture: when no encryption key is configured and the redacted payload matches `_SENSITIVE_PATTERNS`, `save()` raises `RuntimeError("Sensitive information detected in diagnostic content without encryption enabled.")` instead of persisting. This is intentional at the unit level — `tests/agent/test_diagnostic_store_security.py` asserts `pytest.raises(RuntimeError, match="Sensitive information detected")`. The shipped default ships an empty key (`config/agent.toml` `[diagnostics] encryption_key = ""`, line 237), so the refusal path is live by default.

Diagnostics are a best-effort channel: `save()` already catches `_filter_sensitive_fields` failures and logs them (`scripts/agent/diagnostic_store.py` lines 156-166) so persistence proceeds without filtering. Two turn-path call sites do not share that discipline. Confirmed by reading current source (evidence label: Confirmed by repository evidence; confidence: high).

## Problem

The two turn-path callers of `DiagnosticStore.save()` do not catch the `RuntimeError`, so a sensitive-pattern match turns a best-effort diagnostic write into an unhandled exception that breaks the turn.

Callers:
- `LLMTurnRunner._handle_llm_error` (`scripts/agent/llm_turn_runner.py` lines 202 and 218): saves transport-failure / partial-text diagnostics with no `try/except` around the `save()` calls.
- `ToolLoopGuard._save_guard_hint` (`scripts/agent/tool_loop_guard.py` line 151): called from `check_empty_result_repeat`, `check_unavailable_repeat`, `check_dedup`, `check_retry`, `check_cycle`, and `_check_progress_stagnation`; none wrap the `save()` call. Five of these run inside `ToolLoopGuard.check_all` (`scripts/agent/tool_loop_guard.py` lines 433-444); `check_unavailable_repeat` is invoked directly from `LLMTurnRunner.run()` (`scripts/agent/llm_turn_runner.py` line 173), so it is on the turn path even though it is not part of `check_all`.

Propagation path (all confirmed against current source):
`save()` raises → `LLMTurnRunner.run()` (only `except LLMTransportError`, line 127) → `LlmTurnExecutor.handle_llm_turn` (`try/finally` only, `scripts/agent/llm_turn_executor.py` lines 95-108) → `WorkflowEngineAdapter._run_execute_stage` (`scripts/agent/workflow_engine_adapter.py` line 344, no `except`) → `Orchestrator._execute_turn` (`except BaseException`, `scripts/agent/orchestrator.py` line 188, re-raises) → REPL generic handler (`except Exception`, `scripts/agent/repl_input_loop.py` line 318) → `_surface_turn_error` → `view.write_fatal(f"{exc.__class__.__name__}: {exc}")` (line 135).

Net effect: a mid-turn LLM error or guard event that happens to carry sensitive-looking text surfaces to the operator as a fatal `RuntimeError` instead of the normal graceful fail `TurnResult`, and the turn's own error-handling path is bypassed.

## Reason for Change

The current behavior lets a side-channel (diagnostics) abort the primary turn. The security boundary (no unencrypted secret persisted) is preserved either way, but the crash is an unintended blast radius for a non-critical, best-effort subsystem. It is reachable today with the shipped default (empty `encryption_key`) whenever a diagnostic payload contains a string matching the sensitive pattern — for example partial LLM output or an error detail that echoes a token, `api_key`, or `password`.

## Implementation Intent

Contain the `RuntimeError` at the best-effort boundary. The responsibility: a diagnostic save must never propagate a refusal or I/O failure into the turn. Two approaches, both preserving the security property (detected-sensitive content is still not written in plaintext) and the unit-level raise contract used by the existing tests:

- **(a) Caller-local (recommended):** wrap the `save()` calls in the two turn-path callers with a narrow `try/except Exception` that logs a warning (with `session_id` and `kind`) and continues, mirroring the existing `_filter_sensitive_fields` failure handling inside `save()`. Does not touch `save()` or the unit-test contract.
- **(b) Centralized (owner sign-off required):** have `save()` convert the sensitive-pattern refusal into a logged skip (log + return) instead of raising, so every caller inherits safe degradation. Changes the unit-level contract asserted by `tests/agent/test_diagnostic_store_security.py`; those tests must be updated consistently. Prefer only if the owner accepts the broader blast radius and the test change.

The implementation selects one option and documents which in the Execution Status; option (b) requires re-freezing the Implementation Target Files table (see `Design`).

## Requirements

- `REQ-001`: A `RuntimeError` (or any exception) from `DiagnosticStore.save()` must not escape `LLMTurnRunner._handle_llm_error` or `ToolLoopGuard._save_guard_hint`.
- `REQ-002`: The refusal is logged at warning level with `session_id` and `kind` for observability.
- `REQ-003`: Detected-sensitive content is still not persisted unencrypted (security boundary intact).
- `REQ-004`: The unit-level raise behavior asserted by `tests/agent/test_diagnostic_store_security.py` is preserved under option (a); if option (b) is selected, those tests are updated consistently to assert the logged skip.
- `REQ-005`: A normal (non-sensitive) turn completes and returns its `TurnResult` unchanged (no new errors, no dropped answers).

## Implementation Target Files

**Freeze status:** Frozen (all four rows `Verified` this cycle, checked in Step 2/3; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)). Option (b) scope is documented in `Design` and is NOT part of this frozen table.

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify `_save_guard_hint` (line 151) | Wrap the single `ctx.diagnostics.save(...)` call in a narrow `try/except Exception` that logs a warning with `session_id`/`kind` and returns without propagating; all six callers inherit the containment. (REQ-001, REQ-002) | `_save_guard_hint` calls `save()` unguarded; confirmed 6 callers, `check_unavailable_repeat` reached directly from `LLMTurnRunner.run():173` (checked in Step 2) | `test_tool_loop_guard.py`, `test_llm_turn_runner.py` | Verified |
| `scripts/agent/llm_turn_runner.py` | Modify `_handle_llm_error` (lines 202, 218) | Wrap the two `ctx.diagnostics.save(...)` calls in a narrow `try/except Exception` that logs a warning with `session_id`/`kind` and continues to build the fail `TurnResult`. (REQ-001, REQ-002) | Both `save()` calls are unguarded on the turn path; `run()` catches only `LLMTransportError` (line 127) (checked in Step 2) | `test_llm_turn_runner.py` | Verified |
| `tests/agent/test_tool_loop_guard.py` | Add regression test | Assert `check_unavailable_repeat` / `_save_guard_hint` do not propagate a `RuntimeError` when `ctx.diagnostics.save()` raises the sensitive-pattern refusal, and produce a warning log record. (REQ-001, REQ-002, AC-regression) | Existing guard tests mock `ctx.diagnostics`; extend with a raising `save()` (checked in Step 3) | `test_tool_loop_guard.py` | Verified |
| `tests/agent/test_llm_turn_runner.py` | Add regression test | Assert `_handle_llm_error` returns a `TurnResult` (no raise) when `ctx.diagnostics.save()` raises the sensitive-pattern refusal, and produces a warning log record. (REQ-001, REQ-002, AC-regression) | Existing `_handle_llm_error` tests mock `runner._ctx.diagnostics.save` and assert call count (checked in Step 3) | `test_llm_turn_runner.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

> Option (b) alternative scope (NOT frozen — requires owner sign-off, then re-freeze):
> modify `scripts/agent/diagnostic_store.py` (`save()`) and
> `tests/agent/test_diagnostic_store_security.py` (update the two raise-asserting tests).
> See `Design`.

## Reference Files

Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/diagnostic_store.py` | Source of the `RuntimeError` (lines 168-174) and the `_filter_sensitive_fields` failure handling (lines 156-166); defines `_SENSITIVE_PATTERNS`/`_SENSITIVE_FIELDS` (must not change). Read to preserve the raise contract under option (a). | `REQ-003`, `REQ-004` |
| `tests/agent/test_diagnostic_store_security.py` | Asserts the unit-level raise contract (`test_save_with_encrypt_but_no_key_raises_on_sensitive_data`, `test_refuse_when_sensitive_data_present_without_key`). Read to confirm the contract is preserved under option (a); modified only under option (b). | `REQ-004` |
| `scripts/agent/llm_turn_executor.py` | Propagation-path evidence: `handle_llm_turn` is `try/finally` only (lines 95-108), so an unhandled `RuntimeError` propagates. | Confirms `REQ-001` blast |
| `scripts/agent/workflow_engine_adapter.py` | Propagation-path evidence: `_run_execute_stage` calls `handle_llm_turn` with no `except` (line 344). | Confirms `REQ-001` blast |
| `scripts/agent/orchestrator.py` | Propagation-path evidence: `_execute_turn` re-raises via `except BaseException` (line 188). | Confirms `REQ-001` blast |
| `scripts/agent/repl_input_loop.py` | Propagation-path evidence: generic `except Exception` handler surfaces the error via `write_fatal` (lines 318, 135). | Confirms `REQ-001` blast |
| `scripts/agent/llm_transport_errors.py` | Same unguarded `save()` pattern (`handle_partial_completion`, `handle_non_partial_error`) but **no production caller** (test-only). Known related context; out of scope. | Not a target (checked in Step 3) |
| `scripts/agent/error_injection_service.py` | Same unguarded `save()` pattern (`inject_mid_turn_error`) but **no production caller** (test-only per current source). Known related context; out of scope. | Not a target (checked in Step 3) |

## Acceptance Criteria

- [ ] **AC-001** (`REQ-001`): A `DiagnosticStore.save()` that hits the sensitive-pattern refusal with an empty encryption key no longer raises out of `_handle_llm_error` or `_save_guard_hint`; the caller returns its normal result.
- [ ] **AC-002** (`REQ-002`): The refusal is logged at warning level with `session_id` and `kind`.
- [ ] **AC-003** (`REQ-003`): Sensitive content is still not persisted in plaintext (security boundary intact) — verified by the existing `test_refuse_when_sensitive_data_present_without_key` suite.
- [ ] **AC-004** (`REQ-005`): A normal (non-sensitive) turn completes and returns its `TurnResult` unchanged.
- [ ] **AC-005** (`REQ-004`): Existing `diagnostic_store` tests pass; under option (a) `test_diagnostic_store_security.py` is unchanged; under option (b) the two raise-asserting tests are updated consistently.

## Tests

- **Unit (REQ-001, REQ-002):** In `tests/agent/test_tool_loop_guard.py` and `tests/agent/test_llm_turn_runner.py`, add a test that calls the turn-path caller with a mock `ctx.diagnostics` whose `save()` raises the sensitive-pattern `RuntimeError`, and assert (a) no `RuntimeError` propagates and (b) a warning log record is produced with `session_id`/`kind`.
- **Regression (REQ-003, REQ-005):** Run `tests/agent/test_diagnostic_store_security.py` and the full agent turn/session suite; confirm the security suite still asserts the raise and that a normal non-sensitive turn returns its `TurnResult`.
- **Type / lint (REQ-005):** `mypy` and `ruff` clean on changed files.

## Documentation Impact

`N/A: no `docs/*.md` requires updating under the recommended option (a).` If option (b) is selected and `save()`'s failure behavior changes from raise to logged skip, record the changed failure behavior in the `DiagnosticStore.save` docstring (failure behavior / operational note) per `skills/DESIGN.md` docs policy — no implementation details forbidden there.

## Assumptions

- The recommended option (a) is adopted unless the owner selects option (b); the plan's frozen scope reflects option (a).
- The narrow `try/except Exception` should mirror the existing `save()` filter-failure handling (`except Exception` with `# noqa: BLE001` and a warning log), consistent with the codebase's best-effort-diagnostics convention.
- `session_id` and `kind` are available at both call sites (`_save_guard_hint` receives `ctx.session.session_id` and uses `kind="guard_hint"`; `_handle_llm_error` passes the diagnostic `kind` string to `save()`).
- The two dead-code call sites (`llm_transport_errors.py`, `error_injection_service.py`) remain out of scope because they have no production caller under current source.

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which containment approach the owner prefers: caller-local `try/except` (option a, preserves the unit raise contract, minimal blast radius) vs `save()`-centralized logged skip (option b, changes the unit contract, broad blast radius across ~40 `save()` call sites). | Owner preference (不明 in issue). | Non-blocking: implement option (a) as default; re-freeze Implementation Target Files if the owner selects option (b). See `Design`. | False |
| UNK-02 | Whether guard-hint payloads can ever contain a sensitive-pattern match in practice, or whether the reachable trigger is limited to the `_handle_llm_error` partial-text / error-detail path. | Payload survey of `guard_hint` and `llm_transport_error` contents. | Non-blocking: the fix is defensive regardless; note reachability in the implementation. Stop and report only if the guard-hint trigger is provably reachable and the owner wants it covered beyond option (a). | False |

## Affected areas

`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify `_save_guard_hint` | Low (single guarded site; all six callers inherit) | N/A: `git-fame` unavailable | N/A: historical analysis unavailable | N/A: no deploy/config change |
| `scripts/agent/llm_turn_runner.py` | Modify `_handle_llm_error` | Low (two guarded sites on the turn path) | N/A: `git-fame` unavailable | N/A: historical analysis unavailable | N/A: no deploy/config change |
| `tests/agent/test_tool_loop_guard.py` | Add regression test | Low | N/A: `git-fame` unavailable | N/A: historical analysis unavailable | N/A: no deploy/config change |
| `tests/agent/test_llm_turn_runner.py` | Add regression test | Low | N/A: `git-fame` unavailable | N/A: historical analysis unavailable | N/A: no deploy/config change |

> Under option (b), `scripts/agent/diagnostic_store.py` `save()` would be `Modify` with a
> **High** blast radius: `save()` is referenced ~42 times across `session.py`,
> `session_persister.py`, `tool_runner.py`, `error_injection_service.py`,
> `llm_transport_errors.py`, and three internal `self.save()` helpers. This is a
> widely-referenced symbol; measure impact before changing its contract (see
> `rules/toolchain.md` impact-radius check).

## Design

**Blast-radius analysis (Step 5, grimp/rg).** `DiagnosticStore.save()` is a
widely-referenced symbol: ~42 call references across the repo. Direct turn-path and
helper callers include `session.py:104`, `session_persister.py:159`,
`tool_runner.py:175` (via `save_transport_failure`), `error_injection_service.py:46`,
`llm_transport_errors.py:35,52`, plus three internal `self.save()` helpers
(`save_serialization_event`, `save_partial_completion`, `save_transport_failure`). This
is why option (b) carries a High blast radius and why `rules/toolchain.md`'s
impact-radius check applies before changing `save()`'s contract.

**Dead-code same-pattern sites (Step 3).** `scripts/agent/llm_transport_errors.py`
(`handle_llm_transport_error` / `handle_partial_completion` / `handle_non_partial_error`)
and `scripts/agent/error_injection_service.py` (`inject_mid_turn_error`) contain the
same unguarded `save()` pattern, but neither has a production caller under current
source (only test imports, confirmed by `grep`). They are therefore not on the live
turn path and are out of scope for this Issue; recorded here as known related context.
If option (b) is chosen, these sites inherit the logged-skip automatically; if option
(a) is chosen, they remain unguarded but unreachable.

**Decision: option (a) vs option (b).** Both preserve the security property and the
unit-level raise contract's intent.

- Option (a) caller-local: minimal, preserves the unit raise contract, blast radius Low, does not touch `save()` or `test_diagnostic_store_security.py`. Aligns with the Issue constraint "do not touch other `save()` call sites."
- Option (b) centralized: robust for all current and future callers, but changes a broadly-referenced symbol's contract and requires updating the two raise-asserting tests in `test_diagnostic_store_security.py`. Requires owner sign-off.

**Recommendation:** option (a) as the default (minimal blast radius, preserves the
unit contract). Option (b) only if the owner accepts the broader blast radius and the
test change; selecting it requires re-freezing the Implementation Target Files table
(moving `diagnostic_store.py` and `test_diagnostic_store_security.py` into the frozen
scope and removing the two caller-local rows). This is the open design choice tracked as
`UNK-01`.

## Implementation steps

Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Contain the RuntimeError in `_save_guard_hint`** (`scripts/agent/tool_loop_guard.py`, REQ-001, REQ-002)
   - [ ] Wrap the `ctx.diagnostics.save(ctx.session.session_id, "guard_hint", json_dumps(payload))` call (line 151) in a narrow `try/except Exception` (`# noqa: BLE001`) that logs a warning including `session_id` and `kind="guard_hint"` and returns without propagating on any exception.
   - [ ] Verify all six callers (`check_empty_result_repeat`, `check_unavailable_repeat`, `check_cycle`, `_check_progress_stagnation`, `check_dedup`, `check_retry`) inherit the containment with no per-caller change.

2. **Phase 2: Contain the RuntimeError in `_handle_llm_error`** (`scripts/agent/llm_turn_runner.py`, REQ-001, REQ-002)
   - [ ] Wrap the partial-text `ctx.diagnostics.save(...)` (line 202) and the `elif ctx.diagnostics is not None` `ctx.diagnostics.save(...)` (line 218) in narrow `try/except Exception` blocks that log a warning with `session_id` and the diagnostic `kind`, then continue to build the fail `TurnResult`.
   - [ ] Confirm `save_partial_completion` (line 209) remains consistent: it internally calls `self.save()`; either contain via the same caller-local pattern or note that option (a) leaves it to `save()`'s own contract. Document the choice.

3. **Phase 3: Regression tests** (`tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`, REQ-001, REQ-002, AC-regression)
   - [ ] Add a test in `test_tool_loop_guard.py`: mock `ctx.diagnostics.save` to raise the sensitive-pattern `RuntimeError`; assert `check_unavailable_repeat()` / `_save_guard_hint()` do not propagate and emit a warning log record.
   - [ ] Add a test in `test_llm_turn_runner.py`: mock `runner._ctx.diagnostics.save` to raise; assert `_handle_llm_error` returns a `TurnResult` (no raise) and emits a warning log record.

4. **Phase 4: Deployment & Verification** (all target files, REQ-003, REQ-005)
   - [ ] Run `uv run pytest tests/agent/test_diagnostic_store_security.py tests/agent/test_tool_loop_guard.py tests/agent/test_llm_turn_runner.py` and confirm the security suite still asserts the raise and the new regression tests pass.
   - [ ] Run `uv run mypy` and `uv run ruff` on the changed files; require clean.
   - [ ] Commit and push via `skills/deploy` / `git-commit-and-sync` hand-off (production deploy is the user's decision behind an approval gate).

> If the owner selects option (b) instead: replace Phases 1-2 with a single change to
> `scripts/agent/diagnostic_store.py` (`save()` converts the refusal to a logged skip),
> update the two raise-asserting tests in `tests/agent/test_diagnostic_store_security.py`,
> and drop the caller-local regression tests (or keep them as behavior guards). Re-freeze
> the Implementation Target Files table before this runs.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` `_save_guard_hint` | Unit: raising `save()` must not propagate; warning emitted | `uv run pytest tests/agent/test_tool_loop_guard.py` | Test passes; no `RuntimeError` escapes; warning record present |
| `scripts/agent/llm_turn_runner.py` `_handle_llm_error` | Unit: raising `save()` must not propagate; warning emitted | `uv run pytest tests/agent/test_llm_turn_runner.py` | Test passes; `_handle_llm_error` returns a `TurnResult` |
| `scripts/agent/diagnostic_store.py` `save()` | Security regression: sensitive content still refused unencrypted | `uv run pytest tests/agent/test_diagnostic_store_security.py` | Existing raise assertions still pass (option a) / updated (option b) |
| Full agent turn/session suite | Regression: normal non-sensitive turn unchanged | `uv run pytest tests/agent/` (turn + session suites) | No new failures; normal turns return `TurnResult` |
| Changed files | Type / lint | `uv run mypy`, `uv run ruff` | Clean on changed files |

Baseline recorded (Step 5): `radon cc` on the three scripts targets reports only A/B complexity (no high-complexity functions introduced); `vulture --min-confidence 80` reports no findings in the targets; `bandit -r scripts/ -c pyproject.toml` reports 51 low / 8 medium / 0 high, all pre-existing in unrelated files (e.g. `shared/security/shadow_validation.py`); `diff-cover` unavailable in this environment.

## Risks

- **Risk**: Under option (a), the other ~40 `save()` call sites (e.g. `session.py`, `session_persister.py`, `tool_runner.py`, `error_injection_service.py`, `llm_transport_errors.py`) remain unguarded and could raise the same `RuntimeError` if ever reached on a live path. → **Mitigation**: These are not on the identified crash path under current source; option (a) is scoped to the reachable turn path per the Issue constraint. If broader coverage is desired, select option (b) or file a follow-up.
- **Risk**: Under option (b), changing `save()`'s contract affects every caller at once, and the blast radius was not validated by a full run before landing (cf. `rules/toolchain.md` impact-radius principle). → **Mitigation**: Prefer option (a); if option (b) is chosen, run the full agent test suite before merge and update both raise-asserting tests explicitly.
- **Risk**: The guard-hint trigger reachability is uncertain (`UNK-02`) — guard payloads may never contain a sensitive pattern in practice. → **Mitigation**: The fix is defensive regardless; note reachability in the implementation and stop/report only if provably reachable and the owner wants explicit coverage.
- **Risk**: Over-broad `except Exception` in the callers could mask unrelated failures. → **Mitigation**: Keep the handler narrow and specific to the diagnostic-save call only, log with `exc_info=True`, and re-raise nothing that should surface (the turn already fails gracefully via `TurnResult`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Contain the RuntimeError in `_save_guard_hint` (`scripts/agent/tool_loop_guard.py`) | Pending | — | — | Option (a); REQ-001, REQ-002 |
| 2 | Contain the RuntimeError in `_handle_llm_error` (`scripts/agent/llm_turn_runner.py`) | Pending | — | — | Option (a); REQ-001, REQ-002 |
| 3 | Regression tests (`tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`) | Pending | — | — | REQ-001, REQ-002 |
| 4 | Deployment & verification (type/lint/full suite) | Pending | — | — | REQ-003, REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-120804
- **Related target files**: `scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py`, `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Required Changes | `scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py` | Phase 1, Phase 2 | AC-001 | `test_tool_loop_guard.py`, `test_llm_turn_runner.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / Testing Expectations | `scripts/agent/tool_loop_guard.py`, `scripts/agent/llm_turn_runner.py` | Phase 1, Phase 2 | AC-002 | warning log record assertion | Explicit in issue |
| REQ-003 | Constraints / Acceptance Criteria | `scripts/agent/diagnostic_store.py` (reference) | Phase 4 | AC-003 | `test_diagnostic_store_security.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / Testing Expectations | `tests/agent/test_diagnostic_store_security.py` (reference) | Phase 4 | AC-005 | `test_diagnostic_store_security.py` | Explicit in issue |
| REQ-005 | Constraints / Acceptance Criteria | `scripts/agent/llm_turn_runner.py`, tests | Phase 2, Phase 3, Phase 4 | AC-004, AC-005 | full agent suite, mypy, ruff | Explicit in issue |
