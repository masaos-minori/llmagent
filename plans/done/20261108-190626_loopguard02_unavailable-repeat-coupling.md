## Goal
- Give the `ToolLoopGuard` unavailable-repeat guard its own configuration threshold (`tool_unavailable_repeat_max_repeats`) so it can be toggled independently of the empty-result repeat guard (`tool_empty_result_max_repeats`). Currently both guards read the single knob, so enabling one silently enables the other.

## Priority
Medium

## Scope
- **In-Scope**: Add a new default-`0` integer field to `ToolConfig`; wire it through `_build_tool_config`; repoint `scan_unavailable_repeat` / `check_unavailable_repeat` at the new field; add tests proving independent on/off for both guards; document the two independent knobs.
- **Out-of-Scope**: Changing the empty-result guard's knob name, default, or disable semantics; redesigning the `availability_hint` channel or how `_unavailable_counts` accumulates; touching retry-suppression or dedup guards; adding a config-field-registry entry or validator for the new knob (siblings do not have one).
- **Dependencies**: `N/A: none`
  - Sequencing note: independent of secmask002; both are additive and can be implemented in either order.

## Background
`scripts/agent/tool_loop_guard.py` implements per-turn guards. Two of them count repeats and fire a guard hint at a threshold:
- Empty-result repeat guard: `record_tool_result` / `scan_empty_result_repeat` / `check_empty_result_repeat` reads `ctx.cfg.tool.tool_empty_result_max_repeats`.
- Unavailable-repeat guard: `observe_availability` / `scan_unavailable_repeat` / `check_unavailable_repeat` also reads `ctx.cfg.tool.tool_empty_result_max_repeats` (see `scan_unavailable_repeat` line 277 and the `check_unavailable_repeat` docstring at line 287).

Both default to `0` (disabled) per `config_dataclasses.py:178`. A prior item (`issues/done/20261017-123510_retrysup01_...`) made retry-suppression and empty-result defaults observable at startup but did not address this coupling.

## Problem
Both guards read the single knob `tool_empty_result_max_repeats`. Consequences:
- **No independent toggling.** Setting the knob above 0 flips BOTH guards on together; an operator cannot enable empty-result detection while leaving unavailable-repeat detection off (and vice versa).
- **Threshold conflation.** The guards detect different failure modes (repeated empty tool value vs. a server repeatedly reporting unavailability) with different natural cadences, yet share one threshold.
- **Silent activation.** The unavailable-repeat guard surfaces no enabled/disabled signal, so the operator is unaware that turning on empty-result detection also armed the unavailable-repeat guard.

Verified against current HEAD: `scan_unavailable_repeat` (line 277) reads `self._ctx.cfg.tool.tool_empty_result_max_repeats`; `check_unavailable_repeat` (line 287) documents this reuse.

## Reason for Change
The coupling makes the effective behavior of a single config value ambiguous and prevents scoping the unavailable-repeat guard independently. Decoupling restores one-threshold-per-guard semantics.

## Implementation Intent
Additive change. Add a new default-`0` integer field `tool_unavailable_repeat_max_repeats` to `ToolConfig`, wire it through `_build_tool_config` alongside the other wired tool knobs (e.g. `tool_dedup_max_repeats`), and repoint `scan_unavailable_repeat` / `check_unavailable_repeat` to it. Keep `tool_empty_result_max_repeats` as the sole input for the empty-result guard. Preserve the `<= 0` disables-check contract and the default-off posture.

## Requirements
- `REQ-001`: A new integer field `tool_unavailable_repeat_max_repeats` exists on `ToolConfig`, defaulting to `0`.
- `REQ-002`: `scan_unavailable_repeat` and `check_unavailable_repeat` read `tool_unavailable_repeat_max_repeats`, not `tool_empty_result_max_repeats`.
- `REQ-003`: The empty-result guard still reads only `tool_empty_result_max_repeats`.
- `REQ-004`: The new knob honors `<= 0` disables-check; default `0` leaves the unavailable-repeat guard off.
- `REQ-005`: The two guards toggle independently — empty-result ON with unavailable-repeat OFF, and vice versa.
- `REQ-006`: Backward compatible — existing serialized configs without the new field load unchanged (additive-only).

## Implementation Target Files
**Freeze status**: Frozen (Implementation Target Files Validation passed all rows `Verified`; Step 8 complete).
Amended 2026-11-08 (fallout): added tests/agent/test_llm_turn_runner.py — TestUnavailableRepeatBoundIntegration._real_guard_runner (line 970) drives the real unavailable-repeat guard through tool_empty_result_max_repeats; repoint it to tool_unavailable_repeat_max_repeats so the three runner-level tests keep passing

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Modify | Add `tool_unavailable_repeat_max_repeats: int = 0` to `ToolConfig` near `tool_empty_result_max_repeats` (line 178) | REQ-001, REQ-006 | `scripts/agent/config_dataclasses.py:178` `tool_empty_result_max_repeats: int = 0`; class at line 154 | REQ-001 | Verified |
| `scripts/agent/config_section_builders.py` | Modify | Wire `tool_unavailable_repeat_max_repeats` via `_get_or_default(cfg, "tool_unavailable_repeat_max_repeats", _get_int, 0)` in `_build_tool_config` | REQ-001, REQ-006 | `scripts/agent/config_section_builders.py:180-223` explicit `_get_or_default` list; note `tool_empty_result_max_repeats` is NOT currently wired here | REQ-001 | Verified |
| `scripts/agent/tool_loop_guard.py` | Modify | Repoint `scan_unavailable_repeat` (line 277) and `check_unavailable_repeat` (line ~288) to the new field; update the reuse docstring | REQ-002, REQ-004 | `scripts/agent/tool_loop_guard.py:277` reads `tool_empty_result_max_repeats`; docstring at line 287 | REQ-002, REQ-004 | Verified |
| `tests/agent/test_tool_loop_guard.py` | Modify | Re-point the existing `TestUnavailableRepeat._guard` (line 527) from the old knob to the new one; add independent-toggle tests for both guards, a default-off test for the new knob and an empty-result regression | REQ-003, REQ-005, REQ-006 | `tests/agent/test_tool_loop_guard.py` exists (verified via `find tests`); sibling `test_tool_loop_guard_wiring.py` also present | REQ-005 | Verified |
| `tests/agent/test_tool_loop_guard_wiring.py` | Add | Confirm config wiring (new field flows through `_build_tool_config`) reaches `ToolLoopGuard`; additive-load regression | REQ-006 | `tests/agent/test_tool_loop_guard_wiring.py` exists (verified via `find tests`) | REQ-006 | Verified |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Modify | Document the two independent knobs and their separate semantics (config reference) | REQ-001 | `docs/23_agent/agent_08_03_configuration-tools-memory.md:39` enumerates tool loop limits | REQ-001 | Verified |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Modify | Correct the statement that unavailable-repeat is "bounded by the existing empty-result repeat configuration" (line 87) | REQ-002, REQ-005 | `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md:87` states the unavailable-repeat bound is "the existing empty-result repeat configuration (`tool_empty_result_max_repeats`)"; agent_06_03 has no such statement (its line 41 only says the knob disables the empty-result guard, which stays true) | REQ-002 | Verified |
| `tests/agent/test_llm_turn_runner.py` | Modify | TestUnavailableRepeatBoundIntegration._real_guard_runner (line 970) drives the real unavailable-repeat guard through tool_empty_result_max_repeats; repoint it to tool_unavailable_repeat_max_repeats so the three runner-level tests keep passing | REQ-002 / N/A: none cites REQ-002 | tests/agent/test_llm_turn_runner.py:970 ctx.cfg.tool.tool_empty_result_max_repeats = limit in _real_guard_runner; assertions at :1020 and :1072 depend on the unavailable guard firing/not firing | tests/agent/test_llm_turn_runner.py::TestUnavailableRepeatBoundIntegration | Verified |

Rules: one row per file; the two doc rows are recorded separately from the source rows per the freeze rules.

## Reference Files
Files that must be read to implement the targets but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/config_field_registry.py` | Confirm whether a new field requires a registry entry; siblings `tool_dedup_max_repeats` / `tool_cycle_detect_window` are NOT registered (validator-only) | `scripts/agent/config_dataclasses.py` (REQ-006) |
| `scripts/agent/services/config_validators.py` | Confirm no validator is required for the new knob (matches siblings) and that `_require_non_negative`-style validation is optional | `scripts/agent/config_dataclasses.py` |
| `scripts/agent/llm_turn_executor.py` | Confirm the guards are invoked as expected after repointing; no caller depends on the shared knob | `scripts/agent/tool_loop_guard.py` (REQ-005) |
| `scripts/agent/llm_turn_runner.py` | Confirm guard invocation at the runner level is unaffected by repointing | `scripts/agent/tool_loop_guard.py` (REQ-005) |

## Acceptance Criteria
- `REQ-001`: `ToolConfig().tool_unavailable_repeat_max_repeats == 0` by default; the field exists.
- `REQ-002`: `scan_unavailable_repeat` / `check_unavailable_repeat` read `tool_unavailable_repeat_max_repeats`; docstring updated.
- `REQ-003`: The empty-result guard still reads only `tool_empty_result_max_repeats`.
- `REQ-004`: With the new knob `<= 0`, the unavailable-repeat guard never fires regardless of `tool_empty_result_max_repeats`.
- `REQ-005`: A test sets `tool_empty_result_max_repeats > 0` and `tool_unavailable_repeat_max_repeats <= 0` and confirms empty-result fires while unavailable-repeat does not; the inverse holds too.
- `REQ-006`: Building `ToolConfig` from a raw dict without the new key yields `0` and no validation error.

## Tests
- Independent-toggle tests (REQ-005): four combinations of the two knobs (>0 / <=0) asserting which guard fires.
- Default-off test (REQ-004): new knob defaults to `0`; unavailable-repeat guard off.
- Regression (REQ-003): empty-result guard still honors `tool_empty_result_max_repeats`.
- Config-load test (REQ-006): build `ToolConfig` from a minimal raw dict; assert additive field is `0`.
- Confirm any pinned config-count / pattern assertions are re-checked after adding the field.

## Documentation Impact
- `docs/23_agent/agent_08_03_configuration-tools-memory.md` (ToolConfig/MemoryConfig config reference) — document the two independent knobs and separate semantics. Driven by REQ-001.
- `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` line 87 — correct the coupling statement. Driven by REQ-002.
- Names resolved via `docs/00_index.md` "Document References by Task" mapping (do not hardcode filenames downstream).

## Assumptions
- Adding a dataclass field with a default is additive and does not break existing `ToolConfig(...)` construction sites (all callers pass keyword args or rely on defaults); verified via consumer scan that no caller positional-binds every field.
- The new knob does not require a `CONFIG_FIELD_REGISTRY` entry or validator, matching sibling knobs `tool_dedup_max_repeats` / `tool_cycle_detect_window` (registered validators only, not as hot-reloadable fields).
- Adversarial verification (plan-to-implementation-procedure, 2026-11-08) corrected two claims: the coupling sentence lives in `agent_06_01` line 87 (not `agent_06_03`, which has no line 87 and whose line 41 stays accurate), and `tests/agent/test_llm_turn_runner.py::TestUnavailableRepeatBoundIntegration` (line 970) also drives the unavailable guard via the old knob (added as a fallout row). Existing tests that set `tool_empty_result_max_repeats` for empty-result behaviour (`test_tool_runner.py`, `test_tool_loop_guard_wiring.py`, `test_orchestrator.py`, `test_agent_repl_tool_exec.py`) are unaffected.
- `tests/agent/test_tool_loop_guard_wiring.py` covers the empty-result guard at turn level and builds its ctx directly; the builder-level check of REQ-006 belongs in `tests/agent/test_tool_loop_guard.py`, which already uses `build_agent_config`.
- No config-version schema exists (no `config_version`/serialization write-back for `ToolConfig`), so no serialized-config version bump is needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should the new knob get the same startup enabled/disabled observability the empty-result guard has (startup log/warn)? The issue flags this as needing confirmation. | Product/owner preference on observability parity | Verified 2026-11-08: `ToolLoopGuard.report_effective_state()` already logs a once-per-process startup diagnostic, but only for retry suppression and empty-result detection. Decision: NOT added here (new behavior outside REQ-001..006; the Out-of-Scope list excludes it). Follow-up issue candidate: add `unavailable_repeat_detection=on/off` to that diagnostic and to `agent_03_02` line 110. | False |
| UNK-02 | Is a serialized-config version bump required for the additive field? | None — no config-version schema found in repo | Resolved: no version/schema write-back mechanism exists for `ToolConfig`; additive field needs no bump | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Additive `ToolConfig` field | Medium: new public dataclass field; scanned consumers (`production_config_validator`, `config_validators`, tests) all tolerate additive fields | Low | High | None: no new module |
| `scripts/agent/config_section_builders.py` | Add one `_get_or_default` wiring line | Low: only the tool-config build path | Low | High | None |
| `scripts/agent/tool_loop_guard.py` | Repoint two method reads to the new field | Low: internal to `ToolLoopGuard`; invoked by `llm_turn_executor`/`llm_turn_runner` | Low | High | None |
| `tests/agent/test_llm_turn_runner.py` | Modify | Not assessed (amendment 2026-11-08) | N/A | N/A | Not assessed (amendment 2026-11-08) |

## Design
- Current coupling: `scan_unavailable_repeat` (line 277) does `limit = self._ctx.cfg.tool.tool_empty_result_max_repeats`; `check_unavailable_repeat` (line 287) documents the reuse. The empty-result guard (lines 217/229) reads the same field.
- Add `tool_unavailable_repeat_max_repeats: int = 0` to `ToolConfig` immediately after `tool_empty_result_max_repeats` (line 178), preserving the default-off comment convention.
- Wire in `_build_tool_config` using the same `_get_or_default(cfg, "tool_unavailable_repeat_max_repeats", _get_int, 0)` pattern as sibling knobs (`tool_dedup_max_repeats` at line 191). Note: `tool_empty_result_max_repeats` is **not** currently wired in the builder (it stays at its dataclass default `0`); this pre-existing condition is out of scope and does not affect the new knob, which IS wired.
- Repoint the two guard methods to the new field; update the `check_unavailable_repeat` docstring to drop the "reuses the empty-result bound" claim.
- `<= 0` disables-check contract preserved for the new knob.

## Implementation steps
1. **Phase 1: Core Logic Implementation**
   - [ ] Add `tool_unavailable_repeat_max_repeats: int = 0` to `ToolConfig` in `scripts/agent/config_dataclasses.py` (REQ-001).
   - [ ] Wire it through `_build_tool_config` in `scripts/agent/config_section_builders.py` (REQ-001).
   - [ ] Repoint `scan_unavailable_repeat` / `check_unavailable_repeat` in `scripts/agent/tool_loop_guard.py` and update the docstring (REQ-002, REQ-004).
2. **Phase 2: Tests**
   - [ ] Add independent-toggle tests (REQ-005), default-off test (REQ-004), empty-result regression (REQ-003), and additive config-load test (REQ-006).
   - [ ] Modify (REQ-002; `tests/agent/test_llm_turn_runner.py`) — amendment 2026-11-08
3. **Phase 3: Documentation & Verification**
   - [ ] Document the two independent knobs in `docs/23_agent/agent_08_03_configuration-tools-memory.md` (REQ-001).
   - [ ] Correct the coupling statement in `docs/23_agent/agent_06_01_...:87` (REQ-002).
   - [ ] Run the tool-loop-guard and config suites; confirm no pinned assertion broke (REQ-003..REQ-006).

### Release units
N/A: no release unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Unit: default value + additive load | `uv run pytest tests/agent/services/test_config_reload.py` | `tool_unavailable_repeat_max_repeats == 0`; load from minimal dict succeeds |
| `scripts/agent/tool_loop_guard.py` | Unit: independent toggling of both guards | `uv run pytest tests/agent/test_tool_loop_guard.py` | All four knob combinations behave as asserted |
| `scripts/agent/config_section_builders.py` | Integration: build from raw dict with/without the key | `uv run pytest tests/agent/services/test_config_reload.py` | New key honored; absent key defaults to `0` |

## Risks
- **Risk**: Adding a dataclass field could shift a pinned count of `ToolConfig` fields or a config-schema snapshot test. → **Mitigation**: run the config test suite first to discover any pinned counts; update them if present (documented in Phase 2).
- **Risk**: Re-pointing the guard without updating the docstring leaves a stale "reuses the empty-result bound" claim. → **Mitigation**: update the docstring in the same commit (Phase 1).
- **Risk**: Pre-existing unwiring of `tool_empty_result_max_repeats` (always `0`) means the empty-result guard is currently disabled regardless of config. → **Mitigation**: out of scope for this issue; recorded here so it is not silently assumed functional.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Core Logic Implementation (config field, builder wiring, guard repoint) | Completed | 2026-11-09 | 2026-11-09 | Procedures _1_, _2_, _3_ executed and archived to implementations/done/ |
| 2 | Phase 2: Tests (independence matrix, default-off, additive load; repoint existing tests) | Completed | 2026-11-09 | 2026-11-09 | Procedures _4_, _5_, _8_ archived; execution-time fallout: extra MagicMock-ctx pins in test_llm_turn_runner.py fixtures and the shared ctx helpers of test_orchestrator.py / test_orchestrator_integration.py (recorded in procedure 8 Details) |
| 3 | Phase 3: Documentation & Verification | Completed | 2026-11-09 | 2026-11-09 | Procedures _6_, _7_ archived; docs checkers (quality, structure, content-policy --strict, consistency --domain agent, japanese) all pass; full suite: 11982 passed, 9 skipped; diff-cover 100% |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-195023_1_scripts_agent_config_dataclasses.py.md | 1 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_2_scripts_agent_config_section_builders.py.md | 1 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_3_scripts_agent_tool_loop_guard.py.md | 1 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_4_tests_agent_test_tool_loop_guard.py.md | 2 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_5_tests_agent_test_tool_loop_guard_wiring.py.md | 2 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_6_docs_23_agent_agent_08_03_configuration-tools-memory.md.md | 3 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_7_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md | 3 | Procedure | Completed | 2026-11-09 | — |
| implementations/20261108-195023_8_tests_agent_test_llm_turn_runner.py.md | 2 | Procedure | Completed | 2026-11-09 | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-191650_loopguard02_unavailable-repeat-coupling.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-190626
- **Related target files**: `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/tool_loop_guard.py`, `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_tool_loop_guard_wiring.py`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `tests/agent/test_llm_turn_runner.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent (new knob) | `scripts/agent/config_dataclasses.py` | Phase 1 | REQ-001 | default `== 0` assertion | Confirmed by repository evidence |
| REQ-001 | Implementation Intent | `scripts/agent/config_section_builders.py` | Phase 1 | REQ-001 | raw-dict build honors key | Confirmed by repository evidence |
| REQ-001 | Implementation Intent (document knobs) | `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Phase 3 | REQ-001 | doc lists two knobs | Confirmed by repository evidence |
| REQ-002 | Problem (shared knob) | `scripts/agent/tool_loop_guard.py` | Phase 1 | REQ-002 | method reads new field | Confirmed by repository evidence |
| REQ-002 | Problem (silent activation) | `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Phase 3 | REQ-002 | coupling statement corrected | Confirmed by repository evidence |
| REQ-003 | Constraints (empty-result knob untouched) | `scripts/agent/tool_loop_guard.py` | Phase 1 | REQ-003 | empty-result regression test | Confirmed by repository evidence |
| REQ-004 | Constraints (`<= 0` disables) | `scripts/agent/tool_loop_guard.py` | Phase 1 | REQ-004 | default-off test | Confirmed by repository evidence |
| REQ-005 | Problem (no independent toggling) | `scripts/agent/tool_loop_guard.py` | Phase 2 | REQ-005 | four-combination toggle tests | Confirmed by repository evidence |
| REQ-006 | Constraints (additive-only) | `scripts/agent/config_dataclasses.py` | Phase 1 | REQ-006 | additive-load test | Confirmed by repository evidence |
| REQ-006 | Constraints (additive-only) | `tests/agent/test_tool_loop_guard_wiring.py` | Phase 2 | REQ-006 | wiring reaches ToolLoopGuard | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-08: TestUnavailableRepeatBoundIntegration._real_guard_runner (line 970) drives the real unavailable-repeat guard through tool_empty_result_max_repeats; repoint it to tool_unavailable_repeat_max_repeats so the three runner-level tests keep passing | tests/agent/test_llm_turn_runner.py | Phase 2 | N/A: none cites REQ-002 | tests/agent/test_llm_turn_runner.py::TestUnavailableRepeatBoundIntegration | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-195023 -->
