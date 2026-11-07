## Goal
Replace the two `assert` statements in the production turn path of `workflow_engine_adapter.py` with explicit typed guards, and remove the `# noqa: B101` directive that suppresses nothing in this repository's configured linters.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — L172 engine-injection guard and L407 persistence-boundary guard become explicit `if ... is None: raise <typed>` forms; the L407 `# noqa: B101` comment is deleted with the assert it annotates.
  - `pyproject.toml` — add a ruff `flake8-bugbear` (`"B"`) select entry so `B101` is enforced by the repository's configured linter, provided the rest of `scripts/` passes (measured in Phase 1, `UNK-01`).
  - Tests: guard-behavior tests asserting the typed exception (not `AssertionError`) is raised when the dependency is missing.
- **Out-of-Scope**:
  - Removing asserts elsewhere in `scripts/` unless Phase 1's `-m B101` measurement shows a count small enough to fix in this plan; otherwise they become a follow-up issue (`UNK-01`).
  - Bandit configuration changes: `# nosec` markers are not introduced — replacing the asserts removes the finding at its source instead.
  - Changing when the guards fire (both stay at the same points in the turn flow).
- **Dependencies**: None blocking. Shares `workflow_engine_adapter.py` with `wfaudit006` (flag removal) and `wfaudit008` (alias deletion); the two assert sites (L172, L407) are outside those regions, so overlap is line-number drift only.

## Background
Live verification at HEAD (issue `## Adversarial Validation`): `assert self._workflow_engine is not None` (`scripts/agent/workflow_engine_adapter.py:172`, engine-start path of `execute_turn`) and `assert boundary is not None` (L407, persist-as-assistant path before `boundary.save("assistant", answer)`). Bandit reports exactly two `B101: assert_used` findings for the file. Only L407 carries `# noqa: B101`; L172 carries none. The ruff select list is `["E", "W", "F", "I", "UP", "BLE001"]` (`pyproject.toml:106`) — no `B` family — so `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports the L407 directive as unused (1 error, auto-fixable), confirming it suppresses nothing. Asserts vanish under `python -O`, silently removing both guards.

## Problem
Two production invariants in the turn path are enforced only by `assert`, which a production interpreter run with `-O` strips; one of them is annotated with a suppression comment that the project's linters do not even honor.

## Reason for Change
Guards that must hold in production cannot depend on a construct whose defining property is that it can be disabled. The replacement is mechanical, and the repository gains enforceable `B101` coverage as a side effect.

## Implementation Intent
Guard with typed errors the surrounding `execute_turn` handling already plans for: a missing injected engine is a wiring bug, so raise a typed wiring error rather than let `engine = self._workflow_engine` proceed; a missing turn boundary is a turn-protocol violation raised at the same point today's assert fires. Delete the inert noqa with the assert. Measure whether adding `"B"` to ruff select is green across `scripts/` before adding it.

## Requirements
- `REQ-001`: `grep -n "assert " scripts/agent/workflow_engine_adapter.py` returns nothing; no `# noqa: B101` remains in the file.
- `REQ-002`: Both guards raise typed exceptions: L172 path raises a typed constructor-wiring error (chosen from existing project error types — not bare `AssertionError` or generic `RuntimeError` where a typed error exists); L407 path raises a typed turn-protocol error at the same point the assert fired. Both are covered by `execute_turn`'s existing handling so the turn fails observably (logged) rather than crashing differently than today.
- `REQ-003`: Behavior for the healthy path is unchanged: identical outputs for every existing test fixture (both guards only fire on states no healthy fixture reaches).
- `REQ-004`: `uv run bandit -q scripts/agent/workflow_engine_adapter.py` reports zero `B101` findings for the file.
- `REQ-005`: If Phase 1 measurement shows `scripts/` green under `ruff check --select B101`, `pyproject.toml` select gains `"B"`; otherwise the assert-removal ships and the repository-wide `B101` enablement is filed as a follow-up issue with the measured count.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Replace L172 and L407 asserts with typed guards; delete the inert L407 noqa | `REQ-001`/`REQ-002`/`REQ-004` | Bandit count + live ruff RUF100 run (Step 2) | `tests/agent/test_orchestrator.py`, adapter tests | `Verified` |
| `pyproject.toml` | Modify (conditional) | Add `"B"` to ruff select if Phase 1 measurement is green | `REQ-005` | select list verified at L106 | ruff run | `Verified` |
| `tests/agent/` (adapter/orchestrator tests) | Modify | Guard tests: adapter constructed with `None` engine raises the typed error; persist path with no boundary raises the typed error | `REQ-002`/`REQ-003` | Constructor accepts `WorkflowEngine \| None` (validated) | self | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` (`execute_turn` except branches; `_status_for_exit`/`_record_exit_status`) | Determines which exception types the turn flow already plans for — constrains the typed-error choice | `REQ-002` |
| `scripts/agent/workflow/errors.py` (or the module defining `WorkflowHaltError`/`WorkflowTimeoutError`) | Inventory of existing typed errors to reuse before inventing a new one | `REQ-002` |
| `scripts/agent/context.py` (`turn.persistence_boundary`) | Type of the boundary object and where a turn legitimately has none | `REQ-002`/`REQ-003` |
| `rules/toolchain.md` | Validation sequence that the ruff select change must satisfy | `REQ-005` |

## Acceptance Criteria
- `REQ-001`: grep-clean asserts and B101 noqas in the adapter file.
- `REQ-002`: `WorkflowEngineAdapter(engine=None, ...).execute_turn(...)` raises the typed wiring error (test asserts the exception type name); a persist-as-assistant turn with `persistence_boundary=None` raises the typed protocol error and the answer is not saved.
- `REQ-003`: Full `tests/agent/` suite green with unchanged assertions on healthy paths.
- `REQ-004`: Bandit `B101` count for the file is 0 (down from 2).
- `REQ-005`: Either `pyproject.toml` select includes `"B"` and `uv run ruff check scripts/ tests/` is green, or a follow-up issue file records the measured `B101` count.

## Tests
- Two guard tests (missing engine, missing boundary) asserting typed exception types and no side effects (no engine call, no save).
- RUF100 cleanliness: after the change, `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports no errors (the unused directive is gone).
- Regression: existing orchestrator/adapter suites unchanged.

## Documentation Impact
- None expected (behavior contract is internal error typing). If `docs/23_agent` describes adapter construction requirements, confirm the wording already says the engine must be injected; no speculative doc edits.
- Run `routing.md` checkers only if a doc file is touched.

## Assumptions
- Both guarded states are unreachable in production today (constructor injection is always wired — `startup_component_init.py:121`; boundaries are always set inside a turn) — the guards exist for wiring bugs, so typed-error replacement cannot change normal-flow behavior (validated: healthy fixtures never fire either assert).
- `execute_turn`'s generic except/logging handles a new typed error the same way it handles today's `AssertionError` for status-recording purposes (`_record_exit_status` runs in `finally` regardless).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | repository-wide `B101` count under `ruff check --select B101 scripts/` (decides whether `"B"` enters the permanent select list in this plan) | measurement not run | Phase 1 measurement; follow-up issue if > 0 outside this file | `False` |
| `UNK-02` | exact typed exception to use for the engine-injection guard (reuse vs new small typed error) | error-type inventory | read the workflow errors module at implementation; prefer reuse | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | turn execution path | 11 | N/A | not applicable (rsynced) |
| `pyproject.toml` | Modify (conditional) | lint gates for the whole repo | N/A | N/A | not applicable |
| `tests/agent/` | Modify | tests only | N/A | N/A | not applicable |

## Design
**Typed guards, same positions.** L172: `if self._workflow_engine is None: raise <wiring error>` immediately before `engine = self._workflow_engine` — identical guard point, message preserved from the current assert text ("WorkflowEngine must be injected via constructor"). L407: `if boundary is None: raise <protocol error>` before `await boundary.save(...)`; the current noqa rationale ("None means writes bypass the atomic boundary") becomes the raise message.

**Noqa deletion follows the assert.** The directive is removed because the finding it annotates no longer exists; it never functioned (ruff B-family not selected), so removal is not a behavior change.

**B-enablement is measured, not assumed.** Adding `"B"` to the permanent select list is conditional on a clean repo-wide run (UNK-01); a partial enablement (`--select B101` only in CI) is rejected as it forks linting configuration.

## Implementation steps
1. **Phase 1: Measurement (`UNK-01`).** `uv run ruff check --select B101 scripts/ tests/ --statistics`; record the count. No source changes.
2. **Phase 2: Guard replacement + tests (`REQ-001`-`REQ-004`).** Replace both asserts, delete the noqa, add the two guard tests.
3. **Phase 3: Lint gate decision (`REQ-005`).** If Phase 1 count is 0: add `"B"` to select and re-run the full lint gate; otherwise file the follow-up issue with the recorded count.

### Release units
**Unit**: wfaudit013-full | **Phases**: 1, 2, 3 | **Reason**: guard replacement and its tests are one contract change; the lint-enablement half is independently revertible via its own row if Phase 1 measures dirty.

## Validation plan
- After Phase 2: `uv run pytest tests/agent/ -q`; `uv run bandit -q scripts/agent/workflow_engine_adapter.py | grep -c B101` returns 0; `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` clean.
- After Phase 3 (if enabled): full lint sequence per `rules/toolchain.md` including ruff over the repository.
- Full `uv run pytest tests/ -q` before completion.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New typed error type not handled by a caller that special-cased `AssertionError` | Low | Low | grep for `AssertionError` handling in the turn path at implementation; both current asserts are uncaught today (they crash), so typed raising preserves crash-observability with better typing |
| Adding `"B"` surfaces unrelated bugbear findings across the repo | Medium | Low (blocked by Phase 1 gate) | Conditional row: enablement ships only on a measured-clean run |
| Line drift from concurrent `wfaudit006`/`wfaudit008` edits to the same file | Medium | Low | Line numbers in this plan are HEAD anchors; implementation locates guards by text |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: B101 measurement | Planned | engineer | | | |
| Phase 2: guard replacement + tests | Planned | engineer | | | |
| Phase 3: lint gate decision | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

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
