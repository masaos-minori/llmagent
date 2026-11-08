## Goal
Replace the two `assert` statements in the production turn path of `workflow_engine_adapter.py` with explicit typed guards, and remove the `# noqa: B101` directive that suppresses nothing in this repository's configured linters.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — L172 engine-injection guard and L407 persistence-boundary guard (in `_run_execute_stage`, def L367) become explicit `if ... is None: raise <typed>` forms with two new module-local typed errors; the L407 `# noqa: B101` comment is deleted with the assert it annotates.
  - Tests: guard-behavior tests in `tests/agent/workflow/test_adapter_guards.py` (new) asserting the typed exception (not `AssertionError`) is raised when the dependency is missing.
- **Out-of-Scope**:
  - Removing asserts elsewhere in `scripts/` — measured 2026-11-08: 29 bandit `B101` findings across `scripts/` at HEAD (27 remain after this plan), far too many to fix here; follow-up issue (`UNK-01`, resolved).
  - `pyproject.toml` lint-select changes: ruff 0.15.16 (the pinned version) does not implement `B101` — `--select B101` and `ruff rule B101` fail with "invalid value" — and `--select B scripts/ tests/` measures 171 findings, so `REQ-005`'s enablement condition is unmeetable; the row is demoted to Reference Files and the enablement goes to the follow-up issue (see Notes 2026-11-08).
  - Bandit configuration changes: `# nosec` markers are not introduced — replacing the asserts removes the finding at its source instead.
  - Changing when the guards fire (both stay at the same points in the turn flow).
- **Dependencies**: None blocking. Shares `workflow_engine_adapter.py` with `wfaudit006` (flag removal, procedure `155554_01`: L104, L254-258, L290-294) and `wfaudit008` (alias deletion, procedure `162804_01`: L106-146, L336-341, docstring L7-8); the two assert sites (L172, L407) and the new-error insertion point (after the `TYPE_CHECKING` block, before `_status_for_exit` L49) are outside those regions. Landing order: `155554_01` and `162804_01` land first (batch chronology); their combined 46-line deletion shifts this plan's HEAD anchors (L172 → L130, L407 → L361); locate guards by quoted text, not line number.

## Background
Live verification at HEAD (issue `## Adversarial Validation`): `assert self._workflow_engine is not None` (`scripts/agent/workflow_engine_adapter.py:172`, engine-start path of `execute_turn`) and `assert boundary is not None` (L407, in `_run_execute_stage` (def L367), persist-as-assistant path before `boundary.save("assistant", answer)`; reached from `execute_turn` via the `execute_fn` stage callback). Bandit reports exactly two `B101: assert_used` findings for the file (measured with `grep -c ">> Issue: \[B101"`; a raw `grep -c B101` counts 3 because the L407 code-context echo line also matches). Only L407 carries `# noqa: B101`; L172 carries none. The ruff select list is `["E", "W", "F", "I", "UP", "BLE001"]` (`pyproject.toml:106`) — no `B` family — so `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports the L407 directive as unused (1 error, auto-fixable, verified 2026-11-08), confirming it suppresses nothing. Correction 2026-11-08 (procedure pass): ruff 0.15.16 does not implement `B101` at all (`--select B101` and `ruff rule B101` exit "invalid value"; `B101` absent from the `--select B` statistics), so no ruff select entry can enforce it. Asserts vanish under `python -O`, silently removing both guards.

## Problem
Two production invariants in the turn path are enforced only by `assert`, which a production interpreter run with `-O` strips; one of them is annotated with a suppression comment that the project's linters do not even honor.

## Reason for Change
Guards that must hold in production cannot depend on a construct whose defining property is that it can be disabled. The replacement is mechanical, and the file's bandit `B101` findings drop from 2 to 0 (bandit — not ruff, which no longer ships `B101` — is the tool that reports `B101` in this repository; see Notes 2026-11-08).

## Implementation Intent
Guard with typed errors the surrounding `execute_turn` handling already plans for: a missing injected engine is a wiring bug, so raise a typed wiring error rather than let `engine = self._workflow_engine` proceed; a missing turn boundary is a turn-protocol violation raised at the same point today's assert fires. Delete the inert noqa with the assert. Measure whether adding `"B"` to ruff select is green across `scripts/` before adding it.

## Requirements
- `REQ-001`: `grep -n "assert " scripts/agent/workflow_engine_adapter.py` returns nothing; no `# noqa: B101` remains in the file.
- `REQ-002`: Both guards raise typed exceptions: L172 path raises a typed constructor-wiring error (no existing project error type fits — the errors module inventory has no wiring error; a new module-local typed error is created instead of reusing `WorkflowHaltError`/`WorkflowTimeoutError` or a generic `RuntimeError`); L407 path raises a typed turn-protocol error at the same point the assert fired. Both are plain `Exception` subclasses that pass through `execute_turn`'s except branches exactly as today's `AssertionError` does (recorded via the `finally` and the orchestrator's `except BaseException` branch) so the turn fails observably (logged) rather than crashing differently than today.
- `REQ-003`: Behavior for the healthy path is unchanged: identical outputs for every existing test fixture (both guards only fire on states no healthy fixture reaches).
- `REQ-004`: `uv run bandit -q scripts/agent/workflow_engine_adapter.py` reports zero `B101` findings for the file.
- `REQ-005`: Resolved by the 2026-11-08 measurement: `pyproject.toml` select stays unchanged — ruff 0.15.16 has no `B101` rule, and `uv run ruff check --select B scripts/ tests/` measures 171 findings (B008: 70, B904: 42, B007: 15, B023: 12, B905: 9, others). The repository-wide enablement question (ruff `B` family, or bandit `B101` low-severity gating: 29 findings across `scripts/` at HEAD) is filed as a follow-up issue with these measured counts.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Replace L172 and L407 asserts with typed guards (`WorkflowEngineWiringError` (new), `TurnBoundaryMissingError` (new)); delete the inert L407 noqa | `REQ-001`/`REQ-002`/`REQ-004` | Bandit count + live ruff RUF100 run (verified 2026-11-08 at HEAD `ad48bfa28`) | `tests/agent/workflow/test_adapter_guards.py` (new); regression: `tests/agent/test_orchestrator.py` | `Verified` |
| `tests/agent/workflow/test_adapter_guards.py` (new) | Modify | Guard tests: adapter constructed with `workflow_engine=None` raises the typed wiring error; persist-as-assistant path with `persistence_boundary=None` raises the typed protocol error | `REQ-002`/`REQ-003` | Constructor kwarg `workflow_engine: WorkflowEngine` (adapter L86, non-Optional: the guard test passes `None` against the annotation; the runtime guard exists despite the type) | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` (`execute_turn` except branches; `_status_for_exit`/`_record_exit_status`) | Determines which exception types the turn flow already plans for — constrains the typed-error choice | `REQ-002` |
| `scripts/agent/workflow/workflow_engine.py` (`WorkflowHaltError` L84 / `WorkflowTimeoutError` L88 / `WorkflowStageFailure` L92; corrected 2026-11-08: the previously cited `scripts/agent/workflow/errors.py` does not exist) | Inventory of existing typed errors to reuse before inventing a new one | `REQ-002` |
| `scripts/agent/context.py` (`turn.persistence_boundary`, L255: `TurnPersistence \| None = None`) | Type of the boundary object and where a turn legitimately has none | `REQ-002`/`REQ-003` |
| `rules/toolchain.md` | Validation sequence that the changed code must satisfy | `REQ-003`/`REQ-004` |
| `pyproject.toml` (Confirmed no-change, measured 2026-11-08: ruff 0.15.16 has no `B101` rule; `--select B` measures 171 findings; select list at L106 stays `["E", "W", "F", "I", "UP", "BLE001"]`) | The demoted conditional row's evidence; follow-up issue input for `REQ-005` | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: grep-clean asserts and B101 noqas in the adapter file.
- `REQ-002`: `WorkflowEngineAdapter(..., workflow_engine=None, ...).execute_turn(...)` raises the typed wiring error (test asserts the exception type name); a persist-as-assistant turn with `ctx.turn.persistence_boundary = None` raises the typed protocol error and the answer is not saved.
- `REQ-003`: Full `tests/agent/` suite green with unchanged assertions on healthy paths.
- `REQ-004`: Bandit `B101` count for the file is 0 (down from 2; count with `uv run bandit -q scripts/agent/workflow_engine_adapter.py | grep -c ">> Issue: \[B101"`).
- `REQ-005`: Measured 2026-11-08: `pyproject.toml` select unchanged; a follow-up issue records the measured counts (171 ruff `B` findings in `scripts/`+`tests/`; 29 bandit `B101` findings across `scripts/`, 27 after this plan).

## Tests
- Two guard tests in `tests/agent/workflow/test_adapter_guards.py` (new) — `test_missing_engine_raises_wiring_error` (new), `test_missing_boundary_raises_protocol_error` (new) — asserting typed exception types and no side effects (no engine call, no save).
- RUF100 cleanliness: after the change, `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports no errors (the unused directive is gone; verified 2026-11-08: exactly 1 error before the change).
- Regression: existing orchestrator/adapter suites unchanged (`tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`).

## Documentation Impact
- None expected (behavior contract is internal error typing). If `docs/23_agent` describes adapter construction requirements, confirm the wording already says the engine must be injected; no speculative doc edits.
- Run `routing.md` checkers only if a doc file is touched.

## Assumptions
- Both guarded states are unreachable in production today — `Orchestrator.__init__` (`scripts/agent/orchestrator.py` L81, L137-148; corrected 2026-11-08: the previously cited `startup_component_init.py:121` constructs the `Orchestrator`, not the engine/adapter) always constructs or forwards a `WorkflowEngine` and injects it as `workflow_engine=_engine` into the adapter; boundaries are always set inside a turn (`scripts/agent/orchestrator.py` L174-175 sets `ctx.turn.persistence_boundary` at turn start) — the guards exist for wiring bugs, so typed-error replacement cannot change normal-flow behavior (validated: healthy fixtures never fire either assert).
- A new plain-`Exception` subclass propagates exactly like today's `AssertionError`: `execute_turn` has no generic `except` (it catches only `WorkflowTimeoutError`, `WorkflowHaltError`, `WorkflowStageFailure`, `asyncio.CancelledError`), so both old asserts and the new typed errors pass through its try/finally unchanged, `_record_exit_status` runs in `finally` regardless (writes nothing for these exit reasons: `_status_for_exit` returns a status only for `cancelled`), and the orchestrator's `except BaseException` branch (`scripts/agent/orchestrator.py` L190) records `error_kind = exc.__class__.__name__` and re-raises (`AssertionError` → the new error class names is the only observable difference).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | Resolved 2026-11-08: repo-wide measurement — ruff 0.15.16 has no `B101` rule; `--select B scripts/ tests/` = 171 findings; bandit `B101` = 29 findings across `scripts/` at HEAD (27 after this plan) | none (measured during the procedure pass) | Follow-up issue with the recorded counts; `pyproject.toml` unchanged in this plan | `False` |
| `UNK-02` | Resolved 2026-11-08: error-type inventory done (`agent/workflow/workflow_engine.py` L84-92 plus `grep "class .*Error"` over `scripts/agent/`): no existing typed constructor-wiring or turn-protocol error to reuse; decision = two new module-local errors `WorkflowEngineWiringError` (new) and `TurnBoundaryMissingError` (new) in `workflow_engine_adapter.py` | none (inventory complete) | See Design section | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | turn execution path | 11 | N/A | not applicable (rsynced) |
| `pyproject.toml` | No change (conditional row demoted to Reference Files by the 2026-11-08 measurement) | lint gates for the whole repo (unchanged) | N/A | N/A | not applicable |
| `tests/agent/workflow/test_adapter_guards.py` | New | tests only | N/A | N/A | not applicable |

## Design
**Typed guards, same positions.** Two new module-local error classes — `WorkflowEngineWiringError` (new) and `TurnBoundaryMissingError` (new), plain `Exception` subclasses — are defined in `workflow_engine_adapter.py` between the `TYPE_CHECKING` block (L42-44) and the "Private helpers" section header (L46). L172: `if self._workflow_engine is None: raise WorkflowEngineWiringError("WorkflowEngine must be injected via constructor")` — identical guard point, message preserved from the current assert text. L407: `if boundary is None: raise TurnBoundaryMissingError(...)` before `await boundary.save(...)`; the current noqa rationale ("None means writes bypass the atomic boundary") becomes part of the raise message.

**Plain `Exception` subclasses, not `WorkflowHaltError` descendants.** Reusing `WorkflowHaltError` for the boundary guard would short-circuit the engine's retry logic (`_run_stage_with_retry` treats halts from stage callbacks as terminal) and route the error into `execute_turn`'s `except WorkflowHaltError` handler — a behavior change at the guard point that contradicts the plan's invariant-preserving intent. Plain subclasses keep today's propagation path (uncaught in `execute_turn`, recorded by the orchestrator's `except BaseException` branch) byte-for-byte while giving the guards real types. `RuntimeError` reuse is rejected per `REQ-002` (no generic where a typed error is created).

**Noqa deletion follows the assert.** The directive is removed because the finding it annotates no longer exists; it never functioned (ruff has no `B`-family selection for a `B101` rule that no longer exists), so removal is not a behavior change.

**B-enablement measured, decision taken.** Measured 2026-11-08: ruff 0.15.16 has no `B101` rule; `--select B` measures 171 findings. Adding `"B"` to the permanent select list is out; the enablement question (ruff `B` family cleanup, or bandit low-severity `B101` gating: 29 findings at HEAD) goes to the follow-up issue. A partial enablement (`--select B101` only in CI) is invalid — the rule does not exist in ruff.

## Implementation steps
1. **Phase 1: Measurement (`UNK-01`).** Completed 2026-11-08 during the procedure pass: `uv run ruff check --select B scripts/ tests/` = 171 findings and ruff 0.15.16 reports no `B101` rule at all; `uv run bandit -r scripts/ | grep -c ">> Issue: \[B101"` = 29 at HEAD. No source changes.
2. **Phase 2: Guard replacement + tests (`REQ-001`-`REQ-004`).** Replace both asserts, delete the noqa, add the two guard tests. Procedures `20261108-<PASS-TS>_01` (adapter) and `20261108-<PASS-TS>_02` (guard tests); lands after `155554_01` and `162804_01` (same file, disjoint regions).
3. **Phase 3: Lint gate decision (`REQ-005`).** Decision taken from the Phase 1 measurement: `pyproject.toml` unchanged (row demoted to Reference Files); file the follow-up issue recording the measured counts (ruff `B`: 171 findings, no `B101` rule; bandit `B101`: 29 findings at HEAD, 27 after Phase 2).

### Release units
**Unit**: wfaudit013-full | **Phases**: 1, 2, 3 | **Reason**: guard replacement and its tests are one contract change; the lint-enablement half is independently revertible via its own row if Phase 1 measures dirty.

## Validation plan
- After Phase 2: `uv run pytest tests/agent/ -q`; `uv run bandit -q scripts/agent/workflow_engine_adapter.py | grep -c ">> Issue: \[B101"` returns 0 (down from 2); `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` clean (1 error before the change); `grep -n "assert \|noqa: B101" scripts/agent/workflow_engine_adapter.py` returns nothing.
- Full lint sequence per `rules/toolchain.md` (`uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`). Note: passing `workflow_engine=None` in the new test file targets `scripts/`, which mypy checks (tests/agent is outside the primary mypy invocation; the adapter call site stays typed).
- Full `uv run pytest tests/ -q` before completion.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New typed error type not handled by a caller that special-cased `AssertionError` | Low | Low | `grep -rn "AssertionError" scripts/` at implementation confirms no turn-path caller special-cases it (verified 2026-11-08: the only `AssertionError` handling in the turn flow is the orchestrator's generic `except BaseException` recording `error_kind = exc.__class__.__name__`); both current asserts are uncaught today (they crash), so typed raising preserves crash-observability with better typing |
| Adding `"B"` surfaces unrelated bugbear findings across the repo | Measured 2026-11-08: confirmed (171 findings) — enablement dropped, row demoted | None (no config change ships) | Follow-up issue with the measured counts |
| Line drift from `wfaudit006`/`wfaudit008` edits to the same file | Confirmed: both procedures (`155554_01`, `162804_01`) land before this plan and delete 46 lines above the guard sites | Low | Guard sites located by quoted text; post-shift anchors recorded in Scope Dependencies (L172 → L130, L407 → L361) |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: B101 measurement (`REQ-005` measurement) | Completed | 20261108-201045 | 20261108-201045 | ruff 0.15.16 has no `B101` rule; follow-up issue branch recorded, issue not yet filed |
| 2 | Phase 2: guard replacement + tests (`REQ-001`-`REQ-004`) | In Progress | 20261108-201045 | — | procedures `20261108-201045_01`/`_02` generated; implementation pending |
| 3 | Phase 3: lint gate decision | Completed | 20261108-201045 | 20261108-201045 | resolved by demotion: no `pyproject.toml` change in this plan |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-201045_01_scripts_agent_workflow_engine_adapter.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261108-201045_02_tests_agent_workflow_test_adapter_guards.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203226_wfaudit013_adapter-production-asserts.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084014
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Required Changes | adapter | no asserts/noqa remain | grep |
| `REQ-002` | Issue Problem (asserts stripped by -O) | adapter | typed exceptions at guard points | guard tests |
| `REQ-003` | Plan Design (behavior preserving) | adapter | healthy paths unchanged | existing suites |
| `REQ-004` | Issue Evidence (bandit findings) | adapter | B101 count 0 | bandit run |
| `REQ-005` | Issue Evidence (inert noqa / select list) | `pyproject.toml` | measured enablement or follow-up issue | ruff run + issue file |

## Notes
- Source verified against HEAD `926dbc109`; the issue's "each followed by a suppression comment" claim was corrected during validation (only L407 carries the noqa — see the issue's `## Adversarial Validation`).
- Coordination: `wfaudit006` and `wfaudit008` edit the same file in different regions; locate guards by text, not line number.
- 2026-11-08 (procedure pass, re-verified at HEAD `ad48bfa28`), corrections applied:
  - `pyproject.toml` row demoted to Reference Files (no procedure doc generated): ruff 0.15.16 does not implement `B101` (`--select B101` and `ruff rule B101` exit "invalid value"); `--select B scripts/ tests/` measures 171 findings; bandit `B101` measures 29 findings across `scripts/` (2 in this file). `REQ-005` falls to its follow-up-issue branch; the follow-up issue is not yet filed and is out of this pass's scope.
  - Constructor evidence corrected: `workflow_engine: WorkflowEngine` (adapter L86) is non-Optional — the earlier "Constructor accepts `WorkflowEngine | None` (validated)" evidence was wrong; the L172 guard exists despite the annotation, and the wiring test passes `workflow_engine=None` against it.
  - Wiring citation corrected: engine injection is guaranteed by `Orchestrator.__init__` (`scripts/agent/orchestrator.py` L81, L137-148), not `startup_component_init.py:121` (which constructs the `Orchestrator` only).
  - L407 site clarified: it is in `_run_execute_stage` (def L367), reached from `execute_turn` via the `execute_fn` stage callback; "handled by existing handling" means unchanged propagation through `execute_turn`'s finally plus the orchestrator's `except BaseException` branch (L190).
  - Sequencing recorded: `155554_01` (wfaudit006) and `162804_01` (wfaudit008) land first; their 46-line deletion shifts HEAD anchors L172 → L130 and L407 → L361 (new-class insertion point is above both sites, after the `TYPE_CHECKING` block at L42-44, before the "Private helpers" header at L46). Sibling docs in `implementations/` are design references, not implemented code.
  - Bandit claim refined: "exactly two `B101` findings" is correct; a raw `grep -c B101` returns 3 because the L407 code-context echo line also matches — count with `grep -c ">> Issue: \[B101"`.
  - `AssertionError` caller check: `grep -rn "AssertionError" scripts/` finds handling only in startup paths (`startup_validation.py` L50, `startup_prompt_setup.py` L25), not in the turn path.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-201045 -->
