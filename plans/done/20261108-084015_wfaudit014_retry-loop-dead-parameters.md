## Goal
Remove the two dead parameters in the workflow retry path — the unread `error_kind` argument of `_status_for_exit`, and the unreachable `else 60` timeout fallback in `_run_stage` — and rename the misleadingly named `backoff_sec` policy field to a name that matches its constant-wait behavior.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — `_status_for_exit(exit_reason, error_kind)` (L49-61) and `_record_exit_status(exit_reason, error_kind, task)` (L262-280) drop the `error_kind` parameter and its docstring mention; the `execute_turn` call site (L255) updated. The local `error_kind` computation is KEPT (correction 2026-11-08: `execute_turn` returns `(answer, error_kind, is_partial)` (L260) and `scripts/agent/orchestrator.py` L176 consumes it — a consumer remains, so only the two helper parameters and their docstring mentions are removed).
  - `scripts/agent/workflow/workflow_engine.py` — `timeout = stage_def.timeout_sec if stage_def else 60` (L310) replaced with an explicit failure (typed engine error) when `stage_def` is missing.
  - Rename `backoff_sec` -> `retry_wait_sec` across `RetryPolicy` and the loader (`workflow_loader.py`, `models.py`, `retry_policy` JSON key), the `RetryEvent` TypedDict field in `scripts/shared/events.py` (L47), and every `config/workflows/*.json`.
  - Tests: pin the removed fallback (missing stage now errors), the renamed key, and updated call sites.
  - Docs: workflow-definition retry-policy key description (`docs/23_agent/` workflow section).
- **Out-of-Scope**:
  - Introducing exponential backoff — the field is renamed, not given new semantics.
  - Changing retry-kind (`retry_on`) semantics — untouched, wfretry001 tests stay green.
  - Any change to which stages the loader allows — loader validation only gains the key rename.
- **Dependencies**: None blocking. The `error_kind` edits share `workflow_engine_adapter.py` with `wfaudit006` (procedure `155554_01`: regions L104, L254-258, L290-294), `wfaudit008` (procedure `162804_01`: alias block L106-146, deactivate twin L336-341, module docstring L7-8) and `wfaudit013` (procedure `201045_01`: guards L172-174, L406-407 plus two new error classes); all regions are disjoint from this plan's L49-61/L255/L262-280 targets, and all edits are anchored by quoted text. `workflow_loader.py`/`test_workflow_loader.py` are shared with `wfaudit004` (procedures `151141_01`/`151141_02`, disjoint regions); `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` is shared with `151141_03` (Loader Validation Rules section L148-158, this plan renames the numeric bullet at L153 inside that section) and `175155_09` (Startup Recovery sentence L165, disjoint). See Notes for the landing-order decisions.

## Background
Live verification at HEAD `ad48bfa28` (issue `## Adversarial Validation`, citations re-verified 2026-11-08): `_status_for_exit(exit_reason, error_kind)` (`scripts/agent/workflow_engine_adapter.py:49-61`) branches only on `exit_reason` (`if exit_reason == "cancelled": return "halted"; return None`) — `error_kind` appears only in the docstring, never in the body; it reaches the function through `_record_exit_status(exit_reason, error_kind, task)` (def L262-280) called from the `execute_turn` finally (L255). `_run_stage` (def L291-297) has no timeout parameter: the fallback is a body-level literal `timeout = stage_def.timeout_sec if stage_def else 60` (L310) feeding `asyncio.timeout(timeout)` (L328) and the lease duration (L319), dead because every loaded stage carries a loader-enforced `timeout_sec`. `wait = policy.backoff_sec` (L271) then `await asyncio.sleep(wait)` (L289) per failed attempt — a constant wait, not a backoff. Loader tests pin numeric policy values (`tests/agent/workflow/test_workflow_loader.py:56,175-189,254`) and none pin growing-backoff semantics.

## Problem
Three names advertise behavior that does not exist: an argument nothing reads (its presence implies status depends on error kind), a timeout fallback no input can reach (its presence implies stages may lack timeouts), and a field named for a backoff that never grows. Each one invites a reader or future editor to build on a promise the code does not keep.

## Reason for Change
Dead parameters and misleading names are how the audit findings in this issue cluster were produced; removing them shrinks the surface the other plans must re-read. The rename is name-only and test-compatible (validated: no test pins backoff growth).

## Implementation Intent
Delete what is dead, rename what is misleading, convert what is unreachable into what is stated: `error_kind` disappears from both helpers and the call site; a missing `stage_def` raises a typed engine error naming the stage instead of silently borrowing 60 seconds; `backoff_sec` becomes `retry_wait_sec` in `RetryPolicy`, the loader, the models, and the shipped workflow JSON files, with the loader accepting only the new key.

## Requirements
- `REQ-001`: `_status_for_exit` and `_record_exit_status` take no `error_kind` parameter and their docstrings no longer mention it; the surviving `error_kind` occurrences in `scripts/agent/workflow_engine_adapter.py` are only the local classification/return uses inside `execute_turn` and `_run_execute_stage` (the orchestrator consumes the returned kind). Engine-side kind handling in `workflow_engine.py` is unchanged.
- `REQ-002`: `_run_stage` contains no timeout literal fallback; a `stage_id` with no `stage_def` in the loaded definition raises a typed error naming the stage, and no attempt row or lease is created for it.
- `REQ-003`: The retry-policy key is `retry_wait_sec` in `RetryPolicy`, the loader (`_REQUIRED_POLICY_KEYS`, `_require_int` label), `models.py`, the `RetryEvent` TypedDict field in `scripts/shared/events.py` (row added 2026-11-08: the REQ-003 grep gate covers all of `scripts/`, and `scripts/shared/events.py:47` carries `backoff_sec: float`), and every `config/workflows/*.json`; `backoff_sec` appears nowhere in `scripts/`, `config/`, `tests/`, or `docs/` after the change (text files; `__pycache__` artifacts excluded).
- `REQ-004`: Retry timing behavior is numerically identical: a policy with `retry_wait_sec: 1` produces the same constant 1-second waits as `backoff_sec: 1` did.
- `REQ-005`: Tests pin `REQ-001`-`REQ-004`; existing loader validation tests (L236, L254 parametrization) pass with the renamed field.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Drop `error_kind` from both helpers (L49-61, L262-280) and the L255 call site; docstring mention removed | `REQ-001` | Body never reads the parameter (Step 2, re-verified at HEAD `ad48bfa28`) | `tests/agent/test_orchestrator.py` | `Verified` |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Replace `else 60` fallback (L310) with a typed missing-stage error; `wait = policy.backoff_sec` (L271) reads the renamed field | `REQ-002`/`REQ-003`/`REQ-004` | Fallback literal L310 + `asyncio.timeout` site L328 verified | `tests/agent/workflow/test_workflow_engine.py` | `Verified` |
| `scripts/agent/workflow/models.py` | Modify | `RetryPolicy.backoff_sec` -> `retry_wait_sec` (field L79, `WorkflowDef` default_factory L91) | `REQ-003` | Field + default verified at HEAD (original L68/L80 citations drifted) | loader/engine tests | `Verified` |
| `scripts/agent/workflow/workflow_loader.py` | Modify | `_RetryPolicyJson` field + docstring (L22, L27), `_REQUIRED_POLICY_KEYS` (L53), `_require_int` call (L132), `RetryPolicy(...)` construction (L170-173) use the new key | `REQ-003` | Key handling verified at HEAD | `tests/agent/workflow/test_workflow_loader.py` L175-189, L254 | `Verified` |
| `scripts/shared/events.py` | Modify | `RetryEvent.backoff_sec` (L47) -> `retry_wait_sec` — same misleading name in the retry-event DTO (row added 2026-11-08) | `REQ-003` | `grep -rn backoff_sec scripts/` hit at `scripts/shared/events.py:47`; `RetryEvent` has no emitter/consumer in `scripts/` or `tests/` (census 2026-11-08) | grep gate | `Verified` |
| `config/workflows/default.json` | Modify | `retry_policy.backoff_sec` (L23) -> `retry_wait_sec` in the shipped definition | `REQ-003` | Loader-enforced required key (L53); sole file in `config/workflows/` | loader load tests | `Verified` |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | Fixtures asserting the key name and value renamed (L29, L56, L175-189 including the test method name and the `backoff_sec must be >= 0` match string, the L254 parametrized field list, and the L274/L304/L316/L328 payload fixtures) | `REQ-003`/`REQ-005` | Fixture sites verified at HEAD `ad48bfa28` (row split from the `tests/agent/workflow/` directory row 2026-11-08) | self | `Verified` |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | `_make_wdef` parameter and `RetryPolicy` fixture key (L42, L48) and the 16 `backoff_sec=` call sites renamed; add the missing-stage typed-error test and the constant-wait test | `REQ-002`/`REQ-003`/`REQ-004`/`REQ-005` | Call sites counted by grep at HEAD (row split from the `tests/agent/workflow/` directory row 2026-11-08) | self | `Verified` |
| `tests/agent/workflow/test_workflow_models.py` | Modify | `RetryPolicy` fixture (L77) and the default-policy assertion (L96) renamed to the new key | `REQ-003`/`REQ-005` | Sites verified at HEAD (row split from the `tests/agent/workflow/` directory row 2026-11-08) | self | `Verified` |
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Modify | `RetryPolicy` fixture key (L38) renamed | `REQ-003` | Site verified at HEAD (row split from the `tests/agent/workflow/` directory row 2026-11-08) | self | `Verified` |
| `tests/agent/test_orchestrator.py` | Modify | 12 `backoff_sec` fixture sites (L204, L414, L512, L613, L853, L961, L1055, L3171, L3819, L3934, L3982 + L3929 comment) renamed; adapter exit-status test with the reduced signature (row added 2026-11-08) | `REQ-003`/`REQ-005` | `grep -c backoff_sec` = 12 at HEAD | self | `Verified` |
| `tests/agent/test_repl_health.py` | Modify | 3 workflow-JSON fixture strings (L473, L500, L514) carry `"backoff_sec": 1` and must carry the new key or the loader refuses them (row added 2026-11-08) | `REQ-003` | `grep -n backoff_sec` sites verified at HEAD | self | `Verified` |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Retry Mechanism bullets (L131-132, L135) and the numeric loader-validation bullet (L153) name the key and the fixed-wait semantics | `REQ-003` | Key text located by grep (original `docs/23_agent/` group row split per file 2026-11-08) | docs checkers | `Verified` |
| `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` | Modify | Invalid Retry Policy symptom text (L79) quotes the validator message with the old key | `REQ-003` | `grep -n backoff_sec docs/` hit at L79 (row added 2026-11-08) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` (`_run_stage_with_retry` L226-289) | The retry loop's use of `policy.backoff_sec` (L271) and `retry_on` — the rename target and the unchanged semantics | `REQ-003`/`REQ-004` |
| `scripts/agent/workflow/workflow_loader.py` (`_require_int` L84-97, `_REQUIRED_POLICY_KEYS` L53) | The strict-validation pattern the rename must keep intact | `REQ-003` |
| `scripts/agent/workflow/models.py` (`RetryPolicy`, `StageDefinition.timeout_sec`) | Field definitions to rename; confirms `timeout_sec` is always present on a loaded stage | `REQ-002`/`REQ-003` |
| `config/workflows/default.json` | The shipped definition that must keep loading after the key rename | `REQ-003` |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` (L72-78) | Confirmed no-change (verification 2026-11-08): describes `RetryEvent` without naming its fields, so the events.py field rename requires no doc edit | `REQ-003` |
| `docs/41_db/` (stage timeout rows) | Confirmed no-change (verification 2026-11-08): grep for stage/attempt timeout rows implying a missing timeout found no such row, so the Documentation Impact bullet is satisfied without an edit | `REQ-002` |

## Acceptance Criteria
- `REQ-001`: `_status_for_exit("cancelled")` returns `"halted"` and the function signature has one parameter (correction 2026-11-08: the old two-argument call form is removed by the change, so the acceptance is stated against the new signature only); `_record_exit_status` takes `(exit_reason, task)`.
- `REQ-002`: A test driving `begin_stage_if_new`/`_run_stage` with a stage_id absent from the definition raises the typed error naming that stage; no attempt row is written.
- `REQ-003`: `grep -rn "backoff_sec" scripts/ config/ tests/ docs/` returns nothing; `config/workflows/default.json` loads with `retry_wait_sec` and `wdef.retry_policy.retry_wait_sec == 1`.
- `REQ-004`: A retry test with two failing attempts observes exactly two waits of the configured value (no growth), identical to HEAD behavior.
- `REQ-005`: Updated tests fail on HEAD (old key rejected by the loader / fallback still present) and pass after; full `tests/agent/` green.

## Tests
- Loader tests updated for the renamed key (validation parametrization at L254 field list becomes `["max_attempts", "retry_wait_sec"]`).
- New missing-stage error test at the engine level (`REQ-002`).
- Adapter test that `_record_exit_status` writes `halted` for a cancelled exit with the reduced signature.
- Regression: the wfretry001 `retry_on` tests and lease semantics tests stay green.

## Documentation Impact
- `docs/23_agent/` workflow-definition/retry-policy text — rename the key and state that the wait is constant (not exponential).
- `docs/41_db` stage timeout description — remove any implication that stages may lack a timeout if such a row exists.
- Run docs checkers for domain agent per `routing.md`.

## Assumptions
- No deployed `config/workflows/*.json` outside the repository uses `backoff_sec` (deployed configs are rsynced from the repo tree); a deploy-time check confirms before rollout.
- `stage_def` absence is only reachable through a direct engine call with an unknown stage_id, not through the loaded-definition run path — turning it into a typed error therefore cannot affect normal operation (validated by the loader's required-stage contract).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether any local deployed workflow JSON outside the repo tree carries `backoff_sec` (would refuse to load after the rename) — evidence 2026-11-08: `/opt/llm/config/workflows/default.json` matches the grep, so yes; resolution is the deploy-time migration below | closed by census; deploy step remains | grep `/opt/llm/config/workflows/*.json` during validation before rollout; migrate the hit in the same deploy step | `False` |
| `UNK-02` | whether the loader should accept `backoff_sec` with a clear "renamed key" error message rather than the generic missing-key message | message-quality decision | implement the clearer message only if the generic message is ambiguous — check the existing `_require_int` message style first | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | turn exit-status recording | 11 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | retry loop + stage timeout path | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/models.py` | Modify | `RetryPolicy` consumers | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_loader.py` | Modify | workflow definition loading | 5 | N/A | not applicable (rsynced) |
| `scripts/shared/events.py` | Modify | `RetryEvent` DTO shape | 1 | N/A | not applicable (rsynced) |
| `config/workflows/*.json` | Modify | shipped definitions | N/A | N/A | direct deploy artifact — sync required |
| docs (1-2 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Delete, don't deprecate.** The key rename has no compatibility window: the workflow definitions live in the repository and are rsynced by deploy, so code and config move together in one deploy (repo no-compatibility policy, and `check_compat_shims.py` would flag any accepted-legacy key handling). `UNK-01` guards the only external-config risk.

**Missing stage is an error, not a default.** `stage_def` absence means the caller asked for something the loaded definition does not contain — that is a programming/wiring error, and a silent 60-second guess hides it. The typed error names the stage so the failure is self-describing.

**Rename is name-only.** `retry_wait_sec` keeps the loader's `_require_int(..., 0)` strictness, the same default value (1), and the same `asyncio.sleep(wait)` semantics — `REQ-004` proves numeric identity rather than asserting it.

## Implementation steps
1. **Phase 1: Dead-parameter removal (`REQ-001`).** Drop `error_kind` from both adapter helpers and the call site; adapter test update.
2. **Phase 2: Fallback removal (`REQ-002`).** Replace `else 60` with the typed missing-stage error; add the engine test.
3. **Phase 3: Rename (`REQ-003`, `REQ-004`).** `models.py` -> `workflow_loader.py` -> engine -> config JSON -> tests, in that order, then the numeric-identity retry test.
4. **Phase 4: Docs (`REQ-003` propagation).** Key rename in docs; docs checkers.

### Release units
**Unit**: wfaudit014-full | **Phases**: 1, 2, 3, 4 | **Reason**: three independent narrow cleanups in one audit finding; shipping them together keeps one config-sync event for the key rename rather than two.

## Validation plan
- After each phase: `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -q`; full `uv run pytest tests/ -q` before completion.
- `grep -rn "backoff_sec\|else 60" scripts/ config/ tests/ docs/` returns nothing.
- Deploy pre-check (`UNK-01`): grep `/opt/llm/config/workflows/` for `backoff_sec`; any hit is migrated in the same deploy step.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 4.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A deployed workflow JSON keeps the old key and refuses to load after rollout | Low | High (startup refused with a clear loader error) | `UNK-01` grep before deploy; migrate in the same step |
| Missing-stage error surfaces a latent bad stage reference in a definition | Low | Medium (previously silent wrong-timeout behavior) | The typed error is the point — surfacing it is the fix; validation runs the shipped definitions through the loader |
| Concurrent edits to `workflow_engine_adapter.py` from `wfaudit006`/`wfaudit008`/`wfaudit013` | Medium | Low | The `_status_for_exit`/`_record_exit_status` region is located by text, not line number |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: dead-parameter removal (REQ-001) | In Progress | — | — |  |
| 2 | Phase 2: fallback removal (REQ-002) | In Progress | — | — |  |
| 3 | Phase 3: key rename (REQ-003, REQ-004) | In Progress | — | — |  |
| 4 | Phase 4: documentation (REQ-003 propagation) | In Progress | — | — |  |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-211937_01_scripts_agent_workflow_engine_adapter.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261108-211937_02_scripts_agent_workflow_workflow_engine.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261108-211937_03_scripts_agent_workflow_models.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_04_scripts_agent_workflow_workflow_loader.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_05_scripts_shared_events.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_06_config_workflows_default.json.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_07_tests_agent_workflow_test_workflow_loader.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_08_tests_agent_workflow_test_workflow_engine.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_09_tests_agent_workflow_test_workflow_models.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_10_tests_agent_workflow_test_session_diagnostics_wiring.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_11_tests_agent_test_orchestrator.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_12_tests_agent_test_repl_health.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261108-211937_13_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261108-211937_14_docs_23_agent_agent_10_04_operations-and-observability-validation-and-troubleshooting.md.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084015
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (unread parameter) | `scripts/agent/workflow_engine_adapter.py` | one-parameter helpers | grep + adapter test |
| `REQ-002` | Issue Problem (unreachable fallback) | `scripts/agent/workflow/workflow_engine.py` | typed missing-stage error | engine test |
| `REQ-003` | Issue Problem (misleading name) | models + loader + config | key renamed everywhere | grep + loader tests |
| `REQ-004` | Plan Design (name-only rename) | engine retry loop | identical wait values | retry timing test |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |

## Related Documents
| Path | Relation | Coordination decision |
|---|---|---|
| `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit008) | Same file `scripts/agent/workflow_engine_adapter.py`: deletes the L106-146 alias block (−41 lines before this plan's L255/L262-280 anchors) and renames the deactivate twin | Landing order: wfaudit008 first (batch chronology), then this plan. This plan's adapter procedure locates all sites by quoted text (def signatures, call-site line), never raw line numbers. Regions are disjoint: wfaudit008 owns L106-146/L336-341/L7-8; this plan owns L49-61/L255/L262-280. |
| `implementations/20261108-155554_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit006) | Same file: deletes the `_owns_state_store` flag and the finally close branch (L256-258, L294), adjacent to this plan's finally call-site edit (L255) | Landing order: wfaudit006 first. Its Method step 2 quotes "the finally keeps only `self._record_exit_status(exit_reason, error_kind, task)`" — after this plan lands, that retained line reads `self._record_exit_status(exit_reason, task)`; its deletion targets stay byte-identical either order, so the two edits commute. This plan's procedure anchors the call with the text `self._record_exit_status(exit_reason, error_kind, task)` exactly as it appears at HEAD `ad48bfa28`. |
| `implementations/20261108-201045_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit013) | Same file: inserts two typed error classes (net +9 lines) and rewrites guards at L172-174/L406-407 | Landing order: wfaudit013 before or after both work; its own Assumptions already defer this plan's `_status_for_exit` region to text anchors. Disjoint from L49-61/L255/L262-280. |
| `implementations/20261108-151141_01_scripts_agent_workflow_workflow_loader.py.md` and `implementations/20261108-151141_02_tests_agent_workflow_test_workflow_loader.py.md` (wfaudit004) | Same files `workflow_loader.py` and `test_workflow_loader.py` | wfaudit004 adds `_require_dict` and shape checks (loader L97-138 region) and appends new test classes at file end (including retry_policy payload fixtures naming `backoff_sec`). Landing order: wfaudit004 first, then this plan; this plan's rename is defined as "rename every remaining `backoff_sec` occurrence in the file at execution time", so it also renames the key literals wfaudit004's new tests introduced. Reversed order also works (wfaudit004's quoted fixtures then match the new key only after a re-anchor); the batch order is frozen here to keep one rule. |
| `implementations/20261108-151141_03_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` (wfaudit004) | Same file `agent_03_03_turn-processing-flow-workflow-engine.md`, adjacent bullets in the Loader Validation Rules section (L148-158); its new bullet is inserted after the numeric `retry_policy` bullet this plan renames (L153) | Landing order: wfaudit004's docs document first (its verbatim quote of the numeric bullet matches HEAD), then this plan rewrites only the key names inside that bullet. Disjoint sentences; no conflict. |
| `implementations/20261108-175155_02_scripts_agent_workflow_workflow_engine.py.md` (wfaudit015) | Same file `workflow_engine.py`: replaces the `begin_stage_if_new(...)` call (L313-320) and the artifact call (L373-379) with facade calls and deletes the two ops imports (L20-21) | Disjoint from this plan's L271 and L309-310 edits; `175155_02` is symbol-anchored, so either landing order works. If `175155_02` lands first, this plan's missing-stage error must be inserted above the facade call unchanged; if this plan lands first, `175155_02`'s quoted block stays intact. Recorded here; no sequencing constraint imposed. |
| `implementations/20261108-170505_06_tests_agent_workflow_test_workflow_engine.py.md` and `implementations/20261108-175155_07_tests_agent_workflow_test_workflow_engine.py.md` | Same file `test_workflow_engine.py` | Their edits retarget `count_attempts` asserts and imports; this plan renames `_make_wdef` parameter/fixture key literals and appends two new tests at file end. Text-anchored and disjoint. |
| `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md` and `implementations/20261108-175155_08_tests_agent_test_orchestrator.py.md` | Same file `tests/agent/test_orchestrator.py` | Their edits retarget patch names and rewire fixtures; this plan renames `RetryPolicy(... backoff_sec=...)` literals and adds one new test at a named insertion point. Text-anchored rename (`backoff_sec=` kwarg literal) commutes with their patch-name edits. |

## Notes
- Source verified against HEAD `926dbc109`; the issue's "`_run_stage` has a timeout parameter" mechanism was corrected during validation to a body-level fallback literal (see the issue's `## Adversarial Validation`).
- This plan renames a config key: `config/workflows/*.json` is a deploy-synced artifact, so code and config must deploy together.
- Corrections applied during the 2026-11-08 procedure pass (re-verified at HEAD `ad48bfa28`):
  - Line citations refreshed: adapter `_status_for_exit` L49-62 -> L49-61 and `_record_exit_status` L262-275 -> L262-280; models `RetryPolicy.backoff_sec` L68 -> L79 and default L80 -> L91 (`WorkflowDef` default_factory); engine `_run_stage_with_retry` L226-275 -> L226-289, `asyncio.sleep` L268 -> L289; loader `_require_int` L84-95 -> L84-97, `RetryPolicy(...)` construction L172 -> L170-173.
  - The Scope's "delete the local `error_kind` computation if no other consumer remains" is resolved NO: a consumer remains — `execute_turn` returns `(answer, error_kind, is_partial)` (L260) and `scripts/agent/orchestrator.py` L176 consumes it — so the local computation stays.
  - `backoff_sec` census found three targets the original table missed: `scripts/shared/events.py:47` (`RetryEvent.backoff_sec`), `tests/agent/test_repl_health.py` (3 JSON fixture strings), `tests/agent/test_session_diagnostics_wiring.py:38`; plus `docs/23_agent/agent_10_04_...md:79`. Rows added. The original `docs/23_agent/` group row was split into the two concrete doc files found by grep.
  - REQ-001 acceptance reworded: the two-argument call form is removed by the change, so it cannot be the acceptance probe.
  - `docs/41_db` check (Documentation Impact "if such a row exists"): grep for stage/attempt timeout rows implying a missing timeout found no such row — no docs/41_db change. `docs/40_shared` `RetryEvent` description (L72-78) names no fields — no change.
  - `UNK-01` evidence gathered (not yet closed): `/opt/llm/config/workflows/default.json` exists at deploy location and contains `backoff_sec` — the deploy step MUST migrate it in the same sync.
  - `UNK-02` decided: implement the clearer "renamed key" error only if needed after observing the generic message; decision criteria in procedure 04.
  - Landing-order and commutation decisions for all same-file siblings recorded in the new Related Documents table above; this plan's procedures anchor every edit site by quoted text, not raw line numbers.
- Repair pass 2026-11-08 (re-verified at HEAD `ad48bfa28`):
  - Every factual claim in this plan was adversarially re-checked line-by-line against HEAD: adapter L49/L56/L255/L262-280, engine L271/L289/L291-297/L310/L319/L328, models L79/L90-91, loader L22/L27/L53/L132/L170-173, `scripts/shared/events.py:47`, `config/workflows/default.json` L21-25, docs `agent_03_03` L131-135/L153 and `agent_10_04` L79, and all test fixture line citations (12 sites in `test_orchestrator.py`, 3 in `test_repl_health.py`, loader/engine/models/wiring sites). No claim was stale; no plan text correction was needed.
  - The `tests/agent/workflow/` directory row was split into four rows, one per named test file (`test_workflow_loader.py`, `test_workflow_engine.py`, `test_workflow_models.py`, `test_session_diagnostics_wiring.py`), so every row names exactly one file and receives its own procedure document; the table now has 14 rows. The `170505_06`/`175155_07` Related Documents row covers `test_workflow_engine.py` alongside the new engine-test row.
  - The broken untracked skeletons of the failed first pass (`implementations/20261108-205038_7_tests_agent_workflow_.md`, `_8_tests_agent_test_orchestrator.py.md`, `_9_tests_agent_test_repl_health.py.md`, 1857 B each) were deleted and the stale pass-timestamp marker was removed from this plan before regenerating the full procedure set.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-211937 -->