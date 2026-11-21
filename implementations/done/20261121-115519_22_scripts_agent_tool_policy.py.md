## Goal

Read declared metadata for tier, risk and key kinds, and invert the priority in `classify_operation_type()` so declared metadata is read first (REQ-004, REQ-006, REQ-007, REQ-008; AC-04, AC-06, AC-07).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- Declared metadata is the decision input; the static sets are used only for drift comparison, which is the priority inversion the issue asks for.
- The tier-to-risk mapping stays, but its input becomes the declared tier instead of a configuration map.
- Plan-mode blocking is derived from the declared tier; `plan_blocked_tools` remains only as the documented exception denylist, and its current entries stay redundant by design (DT-03 Option A).

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/tool_policy.py`
### Procedure
- Replace the configuration-map reads with declared-field reads, and reorder the classification lookup so the declared value is consulted before the reference sets.
### Method
- `classify_operation_type()` reads the declared `side_effect_class` first; the reference sets become a comparison that reports disagreement.
- `classify_risk()` loses the `approval_risk_rules` lookup and resolves from the declared tier's mapped risk, then the existing special-case and escalation rules.
- `is_plan_mode_blocked()` checks the documented denylist first, then the declared tier.
- `_escalate_for_path()` and `_escalate_for_github_branch()` resolve keys by the declared kind rather than by tool name, and `_configured_path_keys()` / `_iter_path_arg_values()` read the declared mapping filtered by kind.
### Details
- Verified 2026-11-21: the current lookup order is `approval_risk_rules`, then `tool_safety_tiers`, then the constants default, then `medium`; the plan-mode rule reads `tool_safety_tiers` and the audit and policy key reads use `approval_resource_keys`.
- `repository_gateway.py` calls these functions through their existing signatures, so the public entry points are unchanged.
### Companion test files
- `tests/agent/test_tool_policy.py`
  - Procedure: Point the 71 references to the removed maps at declared metadata, and add the plan-mode derivation and key-kind cases (T-04, T-06).
  - Validation: `uv run pytest tests/agent/test_tool_policy.py -v`

## Compatibility considerations
- This is the largest consumer surface in the plan; the caller signatures stay, so no caller change is needed beyond the removed configuration fields.

## Security considerations
- Fail-closed behaviour for a tool absent from the registry is preserved (risk stays `high`).

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py -v`

## Completion criteria
- No decision path in this module reads a configuration map or a static tool-name set; only the drift comparison reads the reference data.
- A tool whose declared kind is `path` or `branch` escalates through the declared kind, and a `non_escalating` key does not.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Phase 4; release unit: contract-and-producers. Companion ripple: tool_approval.py:286 call-site now passes runtime_tools to is_plan_mode_blocked; source/destination (move_file) key kind corrected to path in tools/apply_producer_policy_fields.py and docs 01/11. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue tests/agent/test_tool_policy.py adapted: 263 passed 2026-11-21. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203303 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue ruff/format/mypy/lint-imports green on target+companion 2026-11-21. Allowed reds resolvable by later batch rows: test_tool_policy_comprehensive (row 49), test_tool_approval_preflight (row 23), test_tool_audit (row 24), test_tool_runner (row 25), test_tool_approval_risk (row 51), test_agent_repl_tool_exec (row 52). unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`