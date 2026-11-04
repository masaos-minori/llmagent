## Goal
- Give the partial-completion counter one owner and one implementation: the live runner increments `ctx.stats.stat_partial_completions`, which every reader already reads, so `/stats`, the REPL warning, and the exit session summary report partial completions; the dead duplicate handler module and the unused client counter are removed.

## Priority
Medium

## Scope
- **In-Scope**:
  - `LLMTurnRunner._handle_llm_error` increments `ctx.stats.stat_partial_completions` instead of the LLM client's attribute.
  - Delete the unused `scripts/agent/llm_transport_errors.py` and remove the client's unused `stat_partial_completions` attribute.
  - Move the tests of the deleted module onto the runner path, switch the orchestrator tests that pin the client counter, and add the REPL warning tests.
  - Regenerate the generated agent reference document and correct the one prose document that names the deleted handler.
- **Out-of-Scope**:
  - How partial text is stored, shown, or retried; the diagnostic records written for a partial completion (`llm_transport_error`, `partial_completion`); other statistics counters.
  - The streaming logic in the LLM client, the `LLMTransportError` type and fields, and the used `scripts/shared/llm_transport_errors.py`.
  - The `control_message` parameter carried by the runner and executor (not touched; only `_handle_llm_error`'s body changes).
  - The `ctx.stats` structure (the field already exists and is unchanged).
- **Dependencies**: N/A: none. The synchronous-diagnostics-writes issue touches `llm_turn_runner.py` for a different reason (the diagnostics save calls) and is independent.

## Background
`_handle_llm_error` saves the diagnostic rows for a stream that ended with partial text and then increments `ctx.services_required.llm.stat_partial_completions`, an attribute the client only initializes. Every reader (`ReplInputLoop._dispatch_line`, `/stats` through `cmd_config_stats.py`, `services/context_view.py`, and `SessionPersister.persist_session_diagnostics`) reads `ctx.stats.stat_partial_completions`, which is a field of `RuntimeStats` that nothing increments. `scripts/agent/llm_transport_errors.py` holds a second copy of the handling with a single importer, `tests/agent/test_llm_partial_completion.py` (checked in Step 2).

## Problem
The REPL warning "Partial LLM completion stored" never appears, `/stats` shows zero partial completions, and the exit summary records zero, so the failure mode the counter exists to expose is invisible. The Issue's reproduction (client counter 1, `ctx.stats` counter 0) was re-read against the code in Step 2: the writer line and the four reader lines are as described.

Verification corrections and findings:
1. Canonical counter decided: `ctx.stats.stat_partial_completions`. Four readers and the `/stats` tests already target it, and token statistics are likewise kept in `ctx.stats`; the writer is the only outlier. The client's attribute has no reader, so it is removed to leave one owner (the client's other counters stay).
2. The client never increments the attribute: `LLMClient.stream` adds reconnect, heartbeat-timeout, and parse-error counts but ignores the fifth value returned by the reconnect handler, which is a reconnect-derived count with different semantics. That value is left alone.
3. The duplicate module has no production importer under `scripts/`; its only importers are the tests in `tests/agent/test_llm_partial_completion.py`, so those tests exercise dead code. A search of `plans/`, `implementations/`, `issues/`, `docs/`, and `tools/` finds only archived plans, the generated reference document, and one prose document that names `handle_partial_completion` as the source of the `partial_completion` diagnostic kind; nothing plans a production caller, so the Issue's stop condition does not trigger.
4. The runner path already has tests that pin the old counter (`tests/agent/test_orchestrator.py` asserts `ctx.services_required.llm.stat_partial_completions` in five places and stubs it once), so those assertions must move to `ctx.stats`; their context may use a mock `stats`, and a counter assertion needs a real `RuntimeStats`.
5. The prose document `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` names the deleted `handle_partial_completion` as the source of the `partial_completion` kind, which becomes stale; its monitoring table (`/stats` shows partials) is correct after the fix and stays.

## Reason for Change
Partial completions mean the user may have seen an incomplete answer; the counter and warning exist to make that visible, and both are silently non-functional.

## Implementation Intent
Route the single writer through the counter all readers use, in the same style as the token statistics, and delete the unused implementation and the unused client counter so no second copy can drift again. Keep the live runner's diagnostics persistence exactly as it is.

## Requirements
- `REQ-001`: `LLMTurnRunner._handle_llm_error` MUST increment `ctx.stats.stat_partial_completions` for a stream that ended with partial text, and MUST NOT increment any client attribute; the diagnostic records and the log line stay unchanged.
- `REQ-002`: Exactly one implementation of the partial-completion handling MUST remain under `scripts/agent/`: `scripts/agent/llm_transport_errors.py` MUST be deleted, with no remaining import of it, and the client's unused `stat_partial_completions` attribute MUST be removed.
- `REQ-003`: After a turn that ends with partial text, `/stats`, the REPL warning (printed once, not for a normal turn), and the session summary written at exit MUST report the same count.
- `REQ-004`: The tests of the deleted module MUST be moved onto the runner path, so the partial-completion tests cover the code that production runs; the orchestrator tests that pin the client counter MUST assert `ctx.stats` instead; the new tests MUST fail on the pre-change code and pass after it.
- `REQ-005`: The generated agent reference document MUST be regenerated, and the prose document that names the deleted handler MUST be corrected.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Counter writer | Replace `ctx.services_required.llm.stat_partial_completions += 1` in `_handle_llm_error` with an increment of `ctx.stats.stat_partial_completions` (checked in Step 2) | REQ-001; AC-1 | `_handle_llm_error` increments the client attribute after saving the two diagnostic rows; the module is 15509 bytes (checked in Step 2) | `tests/agent/test_llm_partial_completion.py`, `tests/agent/test_orchestrator.py` | Verified |
| `scripts/agent/llm_transport_errors.py` | Remove duplicate | Delete the module (Delete): `handle_llm_transport_error`, `handle_partial_completion`, and `handle_non_partial_error` have no production importer (checked in Step 2) | REQ-002; AC-3 | rg over `scripts/` finds no importer of `agent.llm_transport_errors`; `scripts/shared/llm_transport_errors.py` is a different module (checked in Step 2) | `tests/agent/test_llm_partial_completion.py` | Verified |
| `scripts/shared/llm_client.py` | Remove unused counter | Remove `self.stat_partial_completions: int = 0` from the client constructor (checked in Step 2) | REQ-002; AC-3 | The attribute is initialized once and incremented only by the two writers; `LLMClient.stream` never touches it (rg and read, checked in Step 2) | `tests/agent/test_llm_partial_completion.py` | Verified |
| `tests/agent/test_llm_partial_completion.py` | Move tests onto the runner | Rewrite the tests to drive `LLMTurnRunner._handle_llm_error` with a real `RuntimeStats`: history invariant, diagnostics saved, counter incremented once, non-partial error leaves the counter at zero (checked in Step 2) | REQ-004; AC-4, AC-5 | The file imports `agent.llm_transport_errors` in nine tests and builds a `SimpleNamespace` context with a client counter (checked in Step 2) | `tests/agent/test_llm_partial_completion.py` | Verified |
| `tests/agent/test_orchestrator.py` | Switch assertions | Assert `ctx.stats.stat_partial_completions` instead of the client counter in the five partial-completion tests, using a real `RuntimeStats` for the context, and drop the stale stub line (checked in Step 2) | REQ-004; AC-4 | Assertions at the lines that compare `ctx.services_required.llm.stat_partial_completions` to 0 or 1 (rg, checked in Step 2) | `tests/agent/test_orchestrator.py` | Verified |
| `tests/agent/test_repl.py` | Warning tests | Add tests for `_dispatch_line` with a real `RuntimeStats`: the warning appears once for a turn that incremented the counter and not for a normal turn (checked in Step 2) | REQ-003, REQ-004; AC-2, AC-4 | `tests/agent/test_repl.py` is the only file that references `_dispatch_line` (rg, checked in Step 2) | `tests/agent/test_repl.py` | Verified |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Stale handler name | Correct the Source column of the `partial_completion` kind, which names the deleted `handle_partial_completion`, to the live runner path (checked in Step 2) | REQ-005; AC-6 | The diagnostic-kinds table names `handle_partial_completion` as the source (checked in Step 2) | N/A: documentation | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated reference | Regenerate with `tools/generate_reference_table.py --type agent` so the deleted module's rows are removed (checked in Step 2) | REQ-005; AC-6 | The document lists the module's three functions, and `--check` reports no drift before the change (checked in Step 2) | N/A: generated documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/context.py` | `RuntimeStats.stat_partial_completions` is the existing field every reader uses | REQ-001, REQ-003 |
| `scripts/agent/repl_input_loop.py` | `_dispatch_line` compares the counter before and after `handle_turn` to print the warning | REQ-003 |
| `scripts/agent/commands/cmd_config_stats.py` | `/stats` reads `ctx.stats.stat_partial_completions` | REQ-003 |
| `scripts/agent/services/context_view.py` | Context view reads the same counter | REQ-003 |
| `scripts/agent/session_persister.py` | The exit session summary records the same counter | REQ-003 |
| `scripts/agent/llm_turn_executor.py` | Carries the `control_message` parameter with the runner; not edited | REQ-001 |
| `scripts/shared/llm_transport_errors.py` | The used `LlmTransportErrorHandler`; a different module that must not be confused with the deleted one | REQ-002 |
| `tests/agent/commands/test_agent_cmd_config.py` | `/stats` tests already set `ctx.stats.stat_partial_completions`; stub lines on the client stay harmless | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): `_handle_llm_error` with partial text increments `ctx.stats.stat_partial_completions` by one, saves the same diagnostic rows as before, and touches no client attribute; without partial text the counter stays zero.
- AC-2 (REQ-003, REQ-004): `_dispatch_line` prints the warning once for a turn whose handling incremented the counter and prints nothing for a normal turn.
- AC-3 (REQ-002): no file under `scripts/agent/` implements the partial-completion handling besides the runner; `scripts/agent/llm_transport_errors.py` is gone; a repository search finds no import of it; the client has no `stat_partial_completions`.
- AC-4 (REQ-004): the rewritten and new tests fail on the pre-change code and pass after the change, and the partial-completion tests exercise `_handle_llm_error`.
- AC-5 (REQ-003): `/stats` and the exit session summary read the same incremented counter (existing reader tests pass unchanged).
- AC-6 (REQ-005): `uv run python tools/generate_reference_table.py --check` exits 0, the prose document no longer names the deleted handler, and the docs checkers report no findings.

## Tests
- `REQ-004`: `tests/agent/test_llm_partial_completion.py` rebuilt on the runner with a real `RuntimeStats` and a stub diagnostics store: partial text increments the counter once and saves both diagnostic rows, history is not appended, a non-partial error leaves the counter at zero.
- `REQ-004`: `tests/agent/test_orchestrator.py` partial-completion tests assert `ctx.stats` with a real `RuntimeStats`.
- `REQ-003`, `REQ-004`: `tests/agent/test_repl.py` warning-once and no-warning tests.
- Regression: `tests/agent/test_llm_turn_runner.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_session_persister.py`, `tests/agent/commands/test_agent_cmd_config.py`, `tests/shared/test_llm_transport_errors.py`, `tests/integration/test_orchestrator_integration.py`.
- `rg -n "agent.llm_transport_errors|agent/llm_transport_errors" scripts tests tools` returns nothing after the change.

## Documentation Impact
Yes: one prose correction and the regenerated reference (REQ-005). The monitoring document's `/stats` and warning rows stay correct after the fix.

## Assumptions
- `ctx.stats` is a real `RuntimeStats` in production and in the readers' tests (`ctx.stats.stat_partial_completions` exists and defaults to zero); test contexts that mock `stats` need a real one for counter assertions (checked in Step 3).
- Removing the client attribute breaks no reader: a repository search finds no read of `llm.stat_partial_completions` outside the tests that stub it (checked in Step 3).
- Step 8b overlap judgement (`tools/check_plan_target_overlaps.py`): `docs/23_agent/agent_13_reference-api-generated.md` is also regenerated by the memory-persistence logging Plan and the session-restore Plan; the file is generated from live code, so the regenerations are compatible in either order. `tests/agent/test_repl.py` is also edited by the interrupted-startup exit Plan, which adds entry-function tests, while this Plan adds `_dispatch_line` warning tests in a separate class; judged compatible, no ordering needed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the Issue's open question (which counter was meant to be canonical) had an owner preference other than `ctx.stats`. | No record of the original intent was found. | The Plan fixes `ctx.stats` on the evidence that every reader uses it; the owner may revert to the client counter in review. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Modify | Medium: the live LLM turn path | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/llm_transport_errors.py` | Delete | Low: no production importer | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/llm_client.py` | Modify | Low: removes one unread attribute | 1 | N/A | not applicable (rsynced) |
| `tests/agent/test_llm_partial_completion.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Low: five assertions | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_repl.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_13_reference-api-generated.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, the canonical counter: `ctx.stats.stat_partial_completions` (rationale under Problem, finding 1). Alternative: make the client counter canonical and move all four readers; rejected because it touches four readers, removes a `RuntimeStats` field (the Issue says to keep the `ctx.stats` structure), and moves the writer's neighbors for no gain. Compatibility: the diagnostics rows and the log line are unchanged.

Decision 2, the duplicate: delete rather than wire. The module has no production caller and the runner already implements the handling with workflow and task identifiers, which the module lacks, so wiring it would regress the live path. Its tests move onto the runner.

Decision 3, the client attribute: remove it, so a second owner cannot reappear. The client's other counters are untouched.

Consumer scan (`uv run python tools/scan_change_consumers.py --seed handle_partial_completion`, run in Step 3; candidates only): `scripts/agent/llm_transport_errors.py` (target, deleted); `docs/23_agent/agent_13_reference-api-generated.md` and `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` (targets); the tests listed in the Tests section (targets or `not affected`). `scripts/shared/llm_transport_errors.py` is a different module and `not affected`.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Rebuild the partial-completion tests on the runner path and add the REPL warning tests; record that they fail on the current code (REQ-004; `tests/agent/test_llm_partial_completion.py`, `tests/agent/test_repl.py`).
2. **Phase 2: Writer**
   - [ ] Increment `ctx.stats.stat_partial_completions` in `_handle_llm_error` (REQ-001; `scripts/agent/llm_turn_runner.py`).
   - [ ] Switch the orchestrator assertions to `ctx.stats` (REQ-004; `tests/agent/test_orchestrator.py`).
3. **Phase 3: Remove duplicates**
   - [ ] Delete the unused module and remove the unused client attribute (REQ-002; `scripts/agent/llm_transport_errors.py`, `scripts/shared/llm_client.py`).
4. **Phase 4: Documentation**
   - [ ] Correct the stale handler name, regenerate the reference with `uv run python tools/generate_reference_table.py --type agent`, and run the docs checkers (REQ-005; `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`, `docs/23_agent/agent_13_reference-api-generated.md`).
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` and the repository search from the Tests section (REQ-002; `scripts/agent/llm_transport_errors.py`).

### Release units
**Unit**: partial-counter-owner | **Phases**: 2, 3 | **Reason**: removing the client attribute before the writer moves would break the live runner, and moving the writer without the test switch leaves the orchestrator tests asserting a counter nothing increments; they are validated and released together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Unit with a real `RuntimeStats` and stubs | `uv run pytest tests/agent/test_llm_partial_completion.py tests/agent/test_llm_turn_runner.py tests/agent/test_orchestrator.py -v` | New tests fail before Phase 2, pass after |
| REPL warning, `/stats`, summary | Unit | `uv run pytest tests/agent/test_repl.py tests/agent/commands/test_agent_cmd_config.py tests/agent/test_session_persister.py -v` | All pass |
| Shared client | Unit and integration | `uv run pytest tests/shared/test_llm_transport_errors.py tests/integration/test_orchestrator_integration.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/`, `scripts/shared/` | Security / architecture / dead code | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run vulture scripts/ --min-confidence 80` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Generated reference | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Docs | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `LLMTurnRunner.run` at C (15), `_handle_llm_error` at B (8), and `_span_ctx` at B (9); the change adds no branch to `_handle_llm_error`. `vulture` reports two existing unused variables at `llm_turn_runner.py:32` (not caused by this change) and none in the other targets; `bandit` shows no medium or high finding for the touched Python files; diff-cover is recorded at implementation time.

## Risks
- **Risk**: Another reader of the client attribute exists that the search missed → **Mitigation**: the consumer scan and a repository search before deletion; the Issue's stop condition (stop and report if a production caller of the deleted module turns up) is kept.
- **Risk**: Test contexts with a mock `stats` hide a counter regression → **Mitigation**: the counter tests use a real `RuntimeStats`.
- **Risk**: The live handler and the deleted module differed in behavior (the module lacks workflow and task identifiers) → **Mitigation**: the live runner path is the one kept and its diagnostics persistence is unchanged.
- **Risk**: A second owner reappears in the future → **Mitigation**: the client attribute is removed and the vulture gate stays in the validation plan.
- **Risk**: Overlap on `llm_turn_runner.py` with the synchronous-diagnostics issue → **Mitigation**: that change touches the save calls in the same method; if it lands first, rebase this one-line change onto it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: failing runner-path and REPL warning tests | Pending | — | — | |
| 2 | Phase 2: writer moves to `ctx.stats` and orchestrator assertions switch | Pending | — | — | |
| 3 | Phase 3: delete the duplicate module and the unused client attribute | Pending | — | — | |
| 4 | Phase 4: documentation correction and regenerated reference | Pending | — | — | |
| 5 | Phase 5: deployment hand-off and verification | Pending | — | — | |

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
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-115736
- **Related target files**: scripts/agent/llm_turn_runner.py, scripts/agent/llm_transport_errors.py, scripts/shared/llm_client.py, tests/agent/test_llm_partial_completion.py, tests/agent/test_orchestrator.py, tests/agent/test_repl.py, docs/23_agent/agent_10_05_operations-and-observability-monitoring.md, docs/23_agent/agent_13_reference-api-generated.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Problem | scripts/agent/llm_turn_runner.py | 2 | AC-1 | Runner-path partial-completion tests | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; Acceptance Criteria bullet 3 | scripts/agent/llm_transport_errors.py | 3 | AC-3 | Repository search for the removed module | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; client attribute found in Step 2 | scripts/shared/llm_client.py | 3 | AC-3 | `uv run vulture scripts/ --min-confidence 80` | Derived from confirmed evidence |
| REQ-003 | Acceptance Criteria bullets 1-2 | scripts/agent/llm_turn_runner.py | 2 | AC-2, AC-5 | `/stats`, warning, and summary reader tests | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | tests/agent/test_repl.py | 1 | AC-2 | Warning-once and no-warning tests | Explicit in issue |
| REQ-004 | Required Changes bullet 2 (move the tests) | tests/agent/test_llm_partial_completion.py | 1 | AC-4 | Rebuilt runner-path tests | Explicit in issue |
| REQ-004 | Derived: orchestrator tests pin the client counter | tests/agent/test_orchestrator.py | 2 | AC-4 | Five switched assertions | Confirmed by repository evidence |
| REQ-005 | Documentation Impact | docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | 4 | AC-6 | `tools/check_docs_*` | Derived from confirmed evidence |
| REQ-005 | Derived: deleted module is listed in the generated reference | docs/23_agent/agent_13_reference-api-generated.md | 4 | AC-6 | `tools/generate_reference_table.py --check` | Confirmed by repository evidence |
