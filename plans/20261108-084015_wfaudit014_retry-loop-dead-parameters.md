## Goal
Remove the two dead parameters in the workflow retry path — the unread `error_kind` argument of `_status_for_exit`, and the unreachable `else 60` timeout fallback in `_run_stage` — and rename the misleadingly named `backoff_sec` policy field to a name that matches its constant-wait behavior.

## Priority
Low

## Scope
- **In-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` — `_status_for_exit(exit_reason, error_kind)` (L49-62) and `_record_exit_status(exit_reason, error_kind, task)` (L262-275) drop the `error_kind` parameter and its docstring mention; the `execute_turn` call site (L255) updated; the local `error_kind` computation deleted if no other consumer remains.
  - `scripts/agent/workflow/workflow_engine.py` — `timeout = stage_def.timeout_sec if stage_def else 60` fallback replaced with an explicit failure (typed error) when `stage_def` is missing.
  - Rename `backoff_sec` -> `retry_wait_sec` across `RetryPolicy` and the loader (`workflow_loader.py`, `models.py`, `retry_policy` JSON key), including `config/workflows/*.json`.
  - Tests: pin the removed fallback (missing stage now errors), the renamed key, and updated call sites.
  - Docs: workflow-definition retry-policy key description (`docs/23_agent/` workflow section).
- **Out-of-Scope**:
  - Introducing exponential backoff — the field is renamed, not given new semantics.
  - Changing retry-kind (`retry_on`) semantics — untouched, wfretry001 tests stay green.
  - Any change to which stages the loader allows — loader validation only gains the key rename.
- **Dependencies**: None blocking. The `error_kind` edits share `workflow_engine_adapter.py` with `wfaudit006`/`wfaudit008`/`wfaudit013` (`_status_for_exit` region overlaps 013's context; the retry-loop edits do not overlap the alias block).

## Background
Live verification at HEAD (issue `## Adversarial Validation`): `_status_for_exit(exit_reason, error_kind)` (`scripts/agent/workflow_engine_adapter.py:49-62`) branches only on `exit_reason` (`if exit_reason == "cancelled": return "halted"; return None`) — `error_kind` appears only in the docstring, never in the body; it reaches the function through `_record_exit_status(exit_reason, error_kind, task)` called from the `execute_turn` finally (L255). `_run_stage` (L291-297) has no timeout parameter: the fallback is a body-level literal `timeout = stage_def.timeout_sec if stage_def else 60` (~L310) feeding `asyncio.timeout(timeout)` (L328) and the lease duration, dead because every loaded stage carries a loader-enforced `timeout_sec`. `wait = policy.backoff_sec` then `await asyncio.sleep(wait)` per failed attempt (L271, L268) — a constant wait, not a backoff. Loader tests pin numeric policy values (`tests/agent/workflow/test_workflow_loader.py:56,175-189,254`) and none pin growing-backoff semantics.

## Problem
Three names advertise behavior that does not exist: an argument nothing reads (its presence implies status depends on error kind), a timeout fallback no input can reach (its presence implies stages may lack timeouts), and a field named for a backoff that never grows. Each one invites a reader or future editor to build on a promise the code does not keep.

## Reason for Change
Dead parameters and misleading names are how the audit findings in this issue cluster were produced; removing them shrinks the surface the other plans must re-read. The rename is name-only and test-compatible (validated: no test pins backoff growth).

## Implementation Intent
Delete what is dead, rename what is misleading, convert what is unreachable into what is stated: `error_kind` disappears from both helpers and the call site; a missing `stage_def` raises a typed engine error naming the stage instead of silently borrowing 60 seconds; `backoff_sec` becomes `retry_wait_sec` in `RetryPolicy`, the loader, the models, and the shipped workflow JSON files, with the loader accepting only the new key.

## Requirements
- `REQ-001`: `_status_for_exit` and `_record_exit_status` take no `error_kind`; `grep -n "error_kind" scripts/agent/workflow_engine_adapter.py` shows only the surviving classification uses inside `workflow_engine.py` (engine-side kind handling is unchanged).
- `REQ-002`: `_run_stage` contains no timeout literal fallback; a `stage_id` with no `stage_def` in the loaded definition raises a typed error naming the stage, and no attempt row or lease is created for it.
- `REQ-003`: The retry-policy key is `retry_wait_sec` in `RetryPolicy`, the loader (`_REQUIRED_POLICY_KEYS`, `_require_int` label), `models.py`, and every `config/workflows/*.json`; `backoff_sec` appears nowhere in `scripts/`, `config/`, `tests/`, or `docs/` after the change.
- `REQ-004`: Retry timing behavior is numerically identical: a policy with `retry_wait_sec: 1` produces the same constant 1-second waits as `backoff_sec: 1` did.
- `REQ-005`: Tests pin `REQ-001`-`REQ-004`; existing loader validation tests (L236, L254 parametrization) pass with the renamed field.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | Drop `error_kind` from both helpers (L49-62, L262-275) and the L255 call site | `REQ-001` | Body never reads the parameter (Step 2) | `tests/agent/test_orchestrator.py` | `Verified` |
| `scripts/agent/workflow/workflow_engine.py` | Modify | Replace `else 60` fallback (~L310) with a typed missing-stage error | `REQ-002` | Fallback literal + `asyncio.timeout` site verified | `tests/agent/workflow/` engine tests | `Verified` |
| `scripts/agent/workflow/models.py` | Modify | `RetryPolicy.backoff_sec` -> `retry_wait_sec` (L68, L80 default) | `REQ-003` | Field + default verified | loader/engine tests | `Verified` |
| `scripts/agent/workflow/workflow_loader.py` | Modify | `_REQUIRED_POLICY_KEYS` (L53), `_require_int` call (L132), `RetryPolicy(...)` construction (L172) use the new key | `REQ-003` | Key handling verified | `tests/agent/workflow/test_workflow_loader.py` L175-189, L254 | `Verified` |
| `config/workflows/default.json` | Modify | `retry_policy.backoff_sec` -> `retry_wait_sec` in the shipped definition | `REQ-003` | Loader-enforced required key (L53); sole file in `config/workflows/` | loader load tests | `Verified` |
| `tests/agent/workflow/` | Modify | Update fixtures asserting the key name and value; add missing-stage-error test | `REQ-004`/`REQ-005` | Fixture sites verified (L29, L56, L175-189) | self | `Verified` |
| `docs/23_agent/` (workflow definition section) | Modify | Retry-policy key name in the workflow-definition contract text | `REQ-003` | Loader contract documented (to be located by grep) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` (`_run_stage_with_retry` L226-275) | The retry loop's use of `policy.backoff_sec` and `retry_on` — the rename target and the unchanged semantics | `REQ-003`/`REQ-004` |
| `scripts/agent/workflow/workflow_loader.py` (`_require_int` L84-95, `_REQUIRED_POLICY_KEYS` L53) | The strict-validation pattern the rename must keep intact | `REQ-003` |
| `scripts/agent/workflow/models.py` (`RetryPolicy`, `StageDef.timeout_sec`) | Field definitions to rename; confirms `timeout_sec` is always present on a loaded stage | `REQ-002`/`REQ-003` |
| `config/workflows/default.json` | The shipped definition that must keep loading after the key rename | `REQ-003` |

## Acceptance Criteria
- `REQ-001`: `_status_for_exit("cancelled", "timeout")` and `_status_for_exit("cancelled")` return `"halted"`; the function signature has one parameter.
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
| `UNK-01` | whether any local deployed workflow JSON outside the repo tree carries `backoff_sec` (would refuse to load after the rename) | production config census not taken | grep `/opt/llm/config/workflows/*.json` during validation before rollout | `False` |
| `UNK-02` | whether the loader should accept `backoff_sec` with a clear "renamed key" error message rather than the generic missing-key message | message-quality decision | implement the clearer message only if the generic message is ambiguous — check the existing `_require_int` message style first | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Modify | turn exit-status recording | 11 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | retry loop + stage timeout path | 5 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/models.py` | Modify | `RetryPolicy` consumers | 3 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_loader.py` | Modify | workflow definition loading | 5 | N/A | not applicable (rsynced) |
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
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: dead-parameter removal | Planned | engineer | | | |
| Phase 2: fallback removal | Planned | engineer | | | |
| Phase 3: key rename | Planned | engineer | | | |
| Phase 4: documentation | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

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

## Notes
- Source verified against HEAD `926dbc109`; the issue's "`_run_stage` has a timeout parameter" mechanism was corrected during validation to a body-level fallback literal (see the issue's `## Adversarial Validation`).
- This plan renames a config key: `config/workflows/*.json` is a deploy-synced artifact, so code and config must deploy together.
