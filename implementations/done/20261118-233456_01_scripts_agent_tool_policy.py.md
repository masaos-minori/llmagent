## Goal

State the verified approval-risk evaluation order and the `RiskLevel.NONE` short-circuit in the
docstrings of `classify_risk()` and `is_plan_mode_blocked()` (REQ-002), and record the posture that
DT-01/DT-06 Option A settled for this module (REQ-004) — clarification only, no behavior change.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- All six decision tasks were approved as Option A on 2026-11-18 (Plan Decision records); for this
  file Option A means no logic change, docstring/contract clarification only.
- Evaluation-order and measured-posture claims are the Plan `Problem` section's, re-verified in
  this procedure-writing cycle.

## Design decisions
- Docstrings state the implemented order: `approval_risk_rules` → `tool_safety_tiers` →
  `scripts/shared/tool_constants.py` default → `MEDIUM` fallback, then the
  `if base == RiskLevel.NONE: return` short-circuit ahead of `_special_case_risk()` and
  `_escalate_for_path()`.
- `is_plan_mode_blocked()` states the tier check as the authority and `plan_blocked_tools` as an
  explicit extension (DT-03 Option A).

## Alternatives considered
- Adding provenance logging to `classify_risk()` — rejected; provenance is pinned in the
  characterization tests (rows 11/12/15), not added to the module.

## Implementation
### Target file
`scripts/agent/tool_policy.py`
### Procedure
1. Extend the `classify_risk()` docstring (`:426-468`) with the four-step order and the
   `NONE` short-circuit, in that order.
2. Extend the `is_plan_mode_blocked()` docstring (`:413-423`): tier rule is the authority;
   `plan_blocked_tools` is an explicit extension; a tool with no tier entry is rejected
   (fail-closed).
3. Cross-reference the canonical approval document
   `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` from both docstrings.
### Method
Docstring and comment edits only in the two functions; no change to logic, branches, or returns.
### Details
- State the short-circuit consequence: rule-less tier tools (`index_paths`, `refresh_index`,
  `git_add`, `git_commit`, every `READ_ONLY` tool) return `NONE` before `_special_case_risk()`
  (`:368-410`) and `_escalate_for_path()` (`:323-349`), so `approval_protected_paths` can never
  raise their risk (measured: `git_add`/`git_commit` → `none`).
- State the escalation consequence for ruled path-bearing tools: `write_file`, `edit_file`,
  `move_file` → `high` under the shipped protected paths (DT-06 Option A semantics).
- Keep the wording consistent with `check_allowed_root()` (`:471-512`) and `check_allowed_repo()`
  (`:515-530`): jail rejection happens before escalation, and an empty
  `approval_github_allowed_repos` denies all GitHub writes.

## Compatibility considerations
- No behavior change. The regenerated API reference (`docs/23_agent/agent_13_reference-api-generated.md`,
  Plan row 33) re-renders these docstrings in Phase 6; never hand-edit that file.

## Security considerations
Documentation must state fail-closed behavior accurately (unknown tool → `HIGH`; empty allowlist →
deny-all) and must not imply the protected-paths list discriminates inside the jail.

## Rollback considerations
N/A: revert the commit; no behavior to roll back.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_risk.py -q`
  — the row 11/12/15 characterization tests must pass before and after this edit.
- Lint/type check sequence per `rules/toolchain.md`.

## Completion criteria
- Both docstrings state the order, the `NONE` short-circuit, and the plan-mode rule; the module
  diff is docstring/comment-only; the three test files pass unchanged.

## Out of Scope
Tier/rule removal, any new validator guard (DT-01 Option A: none added), `scripts/shared/tool_constants.py`
(row 1-adjacent reference file, never modified by this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261119-071552 | 20261119-071552 | DT-01/DT-06 approved Option A on 2026-11-18; docstring-only edit verified against source (line refs confirmed) |
| 2 | Add or update tests per Validation plan | N/A | — | 20261119-071552 | Tests live in Plan rows 11/12/15, not here; existing 3 test files pass unchanged (365 passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-071552 | 20261119-071552 | ruff format/check + mypy pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | 20261119-071552 | Canonical docs are Plan rows 21/25; API regeneration is Plan row 33 |

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
- **Requirement ID**: `REQ-001` (reachability record), `REQ-002` (record the evaluation order), `REQ-004` (DT-01/DT-03/DT-06 decisions)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/tool_policy.py`
