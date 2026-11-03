## Goal
- Make the agent-side path policy (`check_allowed_root`, `_escalate_for_path`) and the audit `resource_scope` follow the arguments a tool actually declares (`resource_scope_keys` in the tool registry) in addition to the configured `approval_resource_keys.path_keys`, and check every string element of a list-valued path argument, so that list-valued paths (`read_multiple_files.paths`) and differently-named path arguments (`git.repo_path`) are no longer skipped by the preflight and the audit.

## Priority
Medium

## Scope
- **In-Scope**:
  - Resolve the checked argument names for a call from the registered tool's declared `resource_scope_keys` unioned with the configured `path_keys`; keep the configured keys as an additional source, not the only one.
  - Check every string element of a list-valued path argument; fail closed on a value that is neither a string nor a list of strings.
  - Thread the `RuntimeToolRegistry` into `check_preflight` → `check_allowed_root` → `_escalate_for_path` so the declared keys are reachable at every preflight call site.
  - Apply the same key resolution and list handling to the audit `_extract_resource_scope`.
  - Add regression tests using a stub registry that declares the scope keys.
- **Out-of-Scope**:
  - Shell command path handling (`issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`, `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`).
  - Changing which risk tiers skip protected-path escalation (`classify_risk` early return for `READ_ONLY`/`WRITE_SAFE` is unchanged).
  - Resolving relative paths against the server working directory instead of the agent's.
  - Adding a registry lookup that fails open for an unknown tool.
  - Any change to server-side enforcement (`FileAuthorizationError`, `allowed_repo_paths`, `read_single_file` jail).
- **Dependencies**:
  - `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` (open, no Plan moved to done separately): both edit `scripts/agent/tool_policy.py` and `tests/agent/test_tool_policy.py`. Independent in behavior; either order works. shellprefix001 changes the `shell_run` prefix path and interpreter removal; this issue changes path-argument extraction. Reconcile the shared test file when shellprefix001 is implemented. Non-blocking.

## Background
The agent's path policy reads only the string values stored under five configured argument names (`approval_resource_keys.path_keys`). A tool that takes its paths as a list, or under a differently named key, is not inspected: such a call passes the preflight and, for read-only tools, is auto-approved. The servers enforce their own limits, so this is a missing defense-in-depth layer, not an open door, but the agent-side policy does not do what its configuration implies.

Verified against current source:
- `_iter_string_arg_values` yields a value only when it is a non-empty `str`; a list value (e.g. `paths=[...]`) yields nothing, so no element is checked. It is shared by the `path_keys` loops in `check_allowed_root`/`_escalate_for_path` AND the `branch_keys` loop in `_escalate_for_github_branch`, so a blanket change to it would also alter branch escalation.
- `check_allowed_root` and `_escalate_for_path` take the key list from `cfg.approval.approval_resource_keys.get("path_keys", [])` and iterate it with `_iter_string_arg_values`. No registry access.
- `classify_risk` returns `RiskLevel.NONE` immediately for `READ_ONLY`/`WRITE_SAFE` tools before `_escalate_for_path` runs, so the protected-path escalation never applies to those tiers even for the listed keys; only the `check_allowed_root` denial does.
- Tool metadata carries the missing keys: `read_multiple_files` declares `resource_scope_keys` of `["paths"]`; the git tools declare `["repo_path"]`. `resolve_resource_scopes` already consumes these keys for scheduling, and `RuntimeTool.resource_scope_keys` is a required schema-2.0 field populated at discovery.
- The audit `_extract_resource_scope` pulls only the configured `path_keys`/`branch_keys` from masked args, so it is blind to `paths`/`repo_path` too.
- Every `check_preflight` call site (`tool_approval.check_approval`, `repository_gateway._gate_write`, the `tool_runner` gateway bypass) has `ctx.services_required.runtime_tools` available; `classify_risk` already receives the same registry at its call site.
- `RuntimeToolRegistry.get()` raises `KeyError` for an unregistered tool (distinct from a registered-but-under-annotated tool that has safe construction-time defaults), so a registry lookup can fail closed.

## Problem
The real `approval_resource_keys`, `allowed_tools`, `tool_safety_tiers` and protected paths from `config/agent.toml`, a temporary directory as `allowed_root`, and `check_preflight` plus `classify_risk` called directly reproduce the gap with no tool executed: `read_text_file` with `path=/etc/shadow` is denied (`denied_root_jail`), while `read_multiple_files` with `paths=["/etc/shadow", ...]` and a git tool with `repo_path=/etc` pass the preflight and classify as no risk, so no prompt is shown. A third confirmed example in the same reproduction is the `mdq` tool with `paths=["/etc"]`.

Effects:
- The configured jail and protected paths do not apply to list-valued paths or to the git tools' repository path; a reviewer reading the configuration would assume they do.
- The agent-side layer, the approval prompt, and the audit `resource_scope` (built from the same five keys) are blind to the paths these calls touch.
- Safety rests entirely on each server's own enforcement.

## Reason for Change
A policy that silently covers only some argument shapes gives false assurance, and the omission is invisible in the configuration. Any new tool with a differently named or list-shaped path argument is unprotected until someone remembers to extend a global list. The fix is small and cheaper before anything downstream depends on the audit `resource_scope` being complete.

## Implementation Intent
Follow the tool's declared resource arguments: resolve the checked argument names from the registered tool's `resource_scope_keys` unioned with the configured `path_keys`, and treat list values by checking each string element. A path-like argument whose value is neither a string nor a list of strings fails closed. Keep the configured key list as an additional source. Thread the registry down through `check_preflight` so the declared keys are available at every call site. Apply the same extraction to the audit `resource_scope`.

## Requirements
- `REQ-001`: For a call, the checked path argument names are the configured `approval_resource_keys.path_keys` unioned with the registered tool's `resource_scope_keys`; the configured keys remain an additional source. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-002`: Every string element of a list-valued path argument is checked; a path-like argument whose value is neither a `str` nor a `list[str]` fails closed (denies). Denial codes are unchanged. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-003`: `RuntimeToolRegistry` is threaded into `check_preflight`, `check_allowed_root`, and `_escalate_for_path` as an optional registry; an unknown tool (no registry entry) fails closed and never fails open. (`scripts/agent/tool_policy.py`; checked in Step 3)
- `REQ-004`: The audit `_extract_resource_scope` resolves the same union of keys and checks every string element of a list-valued argument. (`scripts/agent/tool_audit.py`; checked in Step 3)
- `REQ-005`: `read_multiple_files` with one `paths` element outside `allowed_root` is denied; a git tool with `repo_path` outside `allowed_root` is denied; a list with all elements inside is allowed; the five configured keys behave as before. New tests fail on current code and pass after the change. (`tests/agent/test_tool_policy.py`; checked in Step 3)

## Implementation Target Files
**Freeze status**: Frozen (set after Step 8b: every row is `Verified` and all four freeze criteria plus the additional checks pass).
Amended 2026-11-03 (scope): added scripts/agent/tool_approval.py — check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime
Amended 2026-11-03 (scope): added scripts/agent/repository_gateway.py — check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime
Amended 2026-11-03 (scope): added scripts/agent/tool_runner.py — check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | Thread `RuntimeToolRegistry` into `check_preflight`/`check_allowed_root`/`_escalate_for_path`; union declared `resource_scope_keys` with configured `path_keys`; check list elements and fail closed on unexpected type without changing the shared `_iter_string_arg_values` used by branch escalation | `check_allowed_root`/`_escalate_for_path` read only configured `path_keys` via `_iter_string_arg_values`; `resolve_resource_scopes` already uses the tool's declared keys; every preflight call site has the registry available; `get()` raises `KeyError` for unknown tools so the lookup fails closed | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `_iter_string_arg_values` shared by path and branch loops; `check_preflight` callers at `tool_approval`, `repository_gateway`, `tool_runner`; `RuntimeToolRegistry.get` (checked in Step 3) | `tests/agent/test_tool_policy.py` | Verified |
| `scripts/agent/tool_audit.py` | `_extract_resource_scope` resolves the same union of keys and checks list elements | `_extract_resource_scope` pulls only configured `path_keys`/`branch_keys` from masked args, so the audit `resource_scope` is blind to `paths`/`repo_path` | REQ-004 / AC-2 | `_extract_resource_scope` (checked in Step 3) | `tests/agent/` audit tests | Verified |
| `tests/agent/test_tool_policy.py` | Add regression tests with a stub registry declaring the scope keys; keep existing suite passing | existing `TestPrefixCollision` and path/repo tests build `AgentConfig` via `_cfg(...)` and import `RuntimeToolRegistry`; no test exercises list-valued or differently-named path keys | REQ-005 / AC-1, AC-2, AC-3, AC-4 | existing `_cfg` helper and `RuntimeToolRegistry` import (checked in Step 3) | itself | Verified |
| `scripts/agent/tool_approval.py` | Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks | check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | REQ-003 / N/A: none cites REQ-003 | check_preflight call site holds ctx.services_required.runtime_tools | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Verified |
| `scripts/agent/repository_gateway.py` | Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks | check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | REQ-003 / N/A: none cites REQ-003 | check_preflight call site holds ctx.services_required.runtime_tools | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Verified |
| `scripts/agent/tool_runner.py` | Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks | check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | REQ-003 / N/A: none cites REQ-003 | check_preflight call site holds ctx.services_required.runtime_tools | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Verified |

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

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `config/agent.toml` | `[approval_resource_keys]` defines the configured `path_keys`/`branch_keys` that must remain an additional source | `scripts/agent/tool_policy.py` / `REQ-001` |
| `scripts/shared/resource_scope.py` | `resolve_resource_scopes` consumes `tool.resource_scope_keys` for scheduling — the metadata-driven model the policy should mirror | `scripts/agent/tool_policy.py` / `REQ-001` |
| `scripts/shared/runtime_tool.py` | `RuntimeTool.resource_scope_keys` is a required schema-2.0 field; the single construction point `build_runtime_tool` enforces it | `scripts/agent/tool_policy.py` / `REQ-001` |
| `scripts/shared/runtime_tool_registry.py` | `RuntimeToolRegistry.get()` raises `KeyError` for an unregistered tool (fail-closed); the registry wired into every preflight call site | `scripts/agent/tool_policy.py` / `REQ-003` |
| `scripts/mcp_servers/file/read_tools.py` | `read_multiple_files` declares `resource_scope_keys` of `["paths"]` — the confirmed list-valued example | `scripts/agent/tool_policy.py` / `REQ-002` |
| `scripts/mcp_servers/git/git_tools.py` | the git tools declare `resource_scope_keys` of `["repo_path"]` — the confirmed differently-named example | `scripts/agent/tool_policy.py` / `REQ-002` |
| `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` | Sibling issue sharing `tool_policy.py` and its tests; reconciles the shared test file | `scripts/agent/tool_policy.py` / `REQ-005` |

## Acceptance Criteria
- `AC-1` (`REQ-001`, `REQ-002`): A call whose declared or configured path argument is a list containing a path outside `allowed_root` is denied by the preflight; a list with all elements inside is allowed.
- `AC-2` (`REQ-002`, `REQ-004`): A git tool whose `repo_path` is outside `allowed_root` is denied; the audit `resource_scope` for such a call lists that path.
- `AC-3` (`REQ-003`): An unknown tool name does not fail open; the configured keys still apply.
- `AC-4` (`REQ-005`): The five configured keys behave as before; the new tests fail on current code and pass after the change; the existing suite still passes.

## Tests
- `AC-1` (`REQ-001`, `REQ-002`): `check_preflight`/`check_allowed_root` with a stub registry declaring `paths` deny `read_multiple_files(paths=[inside, outside])` and allow `read_multiple_files(paths=[inside, inside])`.
- `AC-2` (`REQ-002`, `REQ-004`): a git tool with `repo_path=outside` is denied; `_extract_resource_scope` includes the outside path in `resource_scope`.
- `AC-3` (`REQ-003`): an unregistered tool name still applies the configured keys and does not raise open.
- `AC-4` (`REQ-005`): the whole `tests/agent/test_tool_policy.py` suite passes, including every existing path/repo/prefix case.

## Documentation Impact
`N/A: no `docs/*.md` requires updating for this Plan.` The audit `resource_scope` shape is an internal field; no documented policy describes the checked argument names beyond `config/agent.toml`, which is not changed.

## Assumptions
- **A1**: The configured `path_keys` values are always strings in practice, so applying the fail-closed rule (str → check; `list[str]` → check each; else deny) does not regress any currently-valid configured-key call. Derived from the config usage, not an owner decision.
- **A2**: The declared keys should be unioned with the configured keys rather than replacing them, so a tool that declares no scope keys still falls back to the configured list. Derived from the Issue's "additional source, not the only one" intent.
- **A3**: List handling must be scoped to path extraction and must not modify the shared `_iter_string_arg_values`, because the same helper feeds branch escalation; changing it would alter `_escalate_for_github_branch` behavior. Derived from the caller inspection.
- **A4**: `git-fame`/`pydeps`/`grimp` are unavailable in this environment; `Churn (30d)` and `Bus Factor` are judged from `git log` churn and marked where the tool is missing.
- **A5**: `check_plan_target_overlaps.py` reports this Plan alongside shellprefix001 and shellrisk001 on `scripts/agent/tool_policy.py` and `tests/agent/test_tool_policy.py`, and alongside wfrecovery001, assertaudit001, and toolaudit001 on `scripts/agent/tool_audit.py`. These are compatible/orthogonal: this Plan changes path-argument extraction (`check_allowed_root`/`_escalate_for_path`/`_iter_string_arg_values`) and the audit `_extract_resource_scope`, while the others change the `shell_run` prefix path, shell flag paths, or unrelated audit events. No design contradiction; reconcile the shared test file during implementation (see A6).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `read_multiple_files`/git `repo_path` were deliberately left unchecked because the server layer alone was deemed sufficient | Code shows the agent side never inspected them; the Issue states this is defense-in-depth only | Issue Acceptance Criteria require agent-side coverage regardless; owner confirmation only needed to *not* fix — non-blocking | False |
| UNK-02 | Exact fail-closed boundary for a non-string value under a *configured* key vs. a *declared-only* key | Not distinguished in current source; both currently skip | Implementation decides uniformly (deny) or scoped to declared keys; recorded at plan-to-implementation-procedure | False |
| UNK-03 | Whether any consumer reads the audit `resource_scope` today outside `scripts/` | Not searched in operational tooling outside the repository | Non-blocking; completeness is still the goal | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_policy.py` | Modify | Medium (shared with shellprefix001; changes preflight signature and path extraction used across approval and gateway) | 2 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `scripts/agent/tool_audit.py` | Modify | Low-Medium (audit scope only; called per approval/exec event) | 3 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `tests/agent/test_tool_policy.py` | Modify | Low (tests only; shared with shellprefix001) | 2 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `scripts/agent/tool_approval.py` | Modify | Not assessed (amendment 2026-11-03) | N/A | N/A | Not assessed (amendment 2026-11-03) |
| `scripts/agent/repository_gateway.py` | Modify | Not assessed (amendment 2026-11-03) | N/A | N/A | Not assessed (amendment 2026-11-03) |
| `scripts/agent/tool_runner.py` | Modify | Not assessed (amendment 2026-11-03) | N/A | N/A | Not assessed (amendment 2026-11-03) |

## Design
This Issue leaves two design choices open, so `skills/python-design/SKILL.md` was applied
narrowly to its Step 4 decision entries and Step 8 risks for these decisions only.

**DD-1 — How the declared keys reach the policy.** The policy functions currently take
only `cfg` and `args`, with no registry. Two options:
- **Option A — thread the `RuntimeToolRegistry` into `check_preflight` and descend to
  `check_allowed_root`/`_escalate_for_path`.** All three call sites already hold the
  registry (`ctx.services_required.runtime_tools`); `classify_risk` already receives it.
  Optional parameter defaults to `None`, so callers/tests that omit it keep configured-key
  behavior. **Selected.**
- **Option B — resolve the union once in `check_approval` and pass the key list down.**
  Duplicates the registry availability check at each site and splits the signature change
  across more functions. Rejected as more invasive for the same result.

Rationale: Option A keeps the registry at the single authority it already has in
`classify_risk`, matches the optional-registry convention there, and lets an omitted
registry fail back to configured keys.

**DD-2 — Scope of list handling.** Do not modify the shared `_iter_string_arg_values`
(used by both the `path_keys` and `branch_keys` loops). Add path-scoped list handling so
`_escalate_for_github_branch` is unaffected and the five-key behavior is preserved. Fail
closed on a value that is neither `str` nor `list[str]`.

**DD-3 — Union vs. replace.** Union the declared keys with the configured keys rather than
replacing them, so a tool that declares no scope keys still falls back to the configured
list. This follows from the Issue ("additional source, not the only one").

**D1 — Requirement-ID offset.** `tool_policy.py` carries inline `REQ-001`..`REQ-005`
annotations for the already-implemented matching-mechanism requirements. This Plan uses
`REQ-001`..`REQ-005` scoped to this Plan's requirement traceability table; the inline
annotations are a separate, pre-existing labeling and are not touched by this Plan.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Failing-test baseline**
   - [ ] Add the `REQ-005` regression tests to `tests/agent/test_tool_policy.py` with a stub `RuntimeToolRegistry` declaring `paths`/`repo_path`; confirm they FAIL on current code and record the failures as the baseline. No source change yet. (`tests/agent/test_tool_policy.py`; `REQ-005`)
   - [ ] Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks (REQ-003; `scripts/agent/tool_approval.py`) — amendment 2026-11-03
   - [ ] Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks (REQ-003; `scripts/agent/repository_gateway.py`) — amendment 2026-11-03
   - [ ] Pass ctx.services_required.runtime_tools into check_preflight so declared resource_scope_keys reach the path checks (REQ-003; `scripts/agent/tool_runner.py`) — amendment 2026-11-03
2. **Phase 2: Core logic implementation**
   - [ ] Thread an optional `RuntimeToolRegistry` into `check_preflight`, `check_allowed_root`, and `_escalate_for_path`; resolve the union of configured `path_keys` and the registered tool's `resource_scope_keys`. (`scripts/agent/tool_policy.py`; `REQ-001`, `REQ-003`)
   - [ ] Check every string element of a list-valued path argument; fail closed on a value that is neither `str` nor `list[str]`; keep denial codes unchanged; do not touch the shared `_iter_string_arg_values`. (`scripts/agent/tool_policy.py`; `REQ-002`)
3. **Phase 3: Audit scope**
   - [ ] Update `_extract_resource_scope` in `scripts/agent/tool_audit.py` to resolve the same union of keys and check list elements. (`scripts/agent/tool_audit.py`; `REQ-004`)
4. **Phase 4: Verification**
   - [ ] Run `tests/agent/test_tool_policy.py` (all green), then `ruff` and `mypy --no-namespace-packages` on touched files, plus `bandit` and confirm no new findings beyond the pre-existing ones. (`scripts/agent/tool_policy.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_tool_policy.py`; `AC-1`, `AC-2`, `AC-3`, `AC-4`)
5. **Phase 5: Deployment hand-off**
   - [ ] Commit and push via `git-commit-and-sync`. Deploying is the user's decision behind an approval gate; no production config changes are introduced by this Plan. (`scripts/agent/tool_policy.py`; `REQ-001`–`REQ-005`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_policy.py` | Unit: `check_preflight`/`check_allowed_root` for list-valued and `repo_path` arguments with a stub registry | `uv run pytest tests/agent/test_tool_policy.py` | outside element → denied; all inside → allowed; unknown tool → fails closed |
| `scripts/agent/tool_audit.py` | Unit: `_extract_resource_scope` includes list/repo paths | `uv run pytest tests/agent/` | outside path present in `resource_scope` |
| `scripts/agent/tool_policy.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_tool_policy.py` | Static checks | `uv run ruff`, `uv run mypy --no-namespace-packages`, `uv run bandit` | clean; no new bandit findings |
| `tests/agent/test_tool_policy.py` | Regression (whole suite) | `uv run pytest tests/agent/test_tool_policy.py` | existing suite passes |

## Risks
- **Risk**: Modifying the shared `_iter_string_arg_values` to handle lists also changes `_escalate_for_github_branch`, altering branch escalation. → **Mitigation**: scope list handling to path extraction only (DD-2); the shared helper is left unchanged.
- **Risk**: Failing closed on a non-string value under a configured key denies a previously allowed call. → **Mitigation**: configured keys are always strings in practice (Assumption A1); the whole existing suite in `AC-4` confirms no regression.
- **Risk**: The `check_preflight` signature change misses a call site, leaving a path unchecked. → **Mitigation**: all three call sites hold the registry; Phase 2 threads it through all three; `AC-3` covers the unknown-tool path.
- **Risk**: `bandit` reports 3 pre-existing High findings in `tool_policy.py`/`tool_audit.py`. → **Mitigation**: these are unchanged from HEAD and out of scope; Phase 4 confirms no *new* findings are introduced.
- **Risk**: Coordination with shellprefix001 on the shared `tests/agent/test_tool_policy.py`. → **Mitigation**: this issue adds list/repo tests and does not touch the `shell_run` prefix path; reconcile when shellprefix001 is implemented.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing-test baseline (`tests/agent/test_tool_policy.py`, stub registry) | In Progress | — | — |  |
| 2 | Core logic in `scripts/agent/tool_policy.py` (registry threading, key union, list handling, fail closed) | In Progress | — | — |  |
| 3 | Audit scope in `scripts/agent/tool_audit.py` (`_extract_resource_scope`) | In Progress | — | — |  |
| 4 | Verification: suite, ruff, mypy, bandit | Pending | — | — |  |
| 5 | Deployment hand-off (commit/push; deploy is user decision) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261103-154504_01_scripts_agent_tool_policy.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261103-154504_02_scripts_agent_tool_audit.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-155552
- **Related target files**: `scripts/agent/tool_policy.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes 1; Background (metadata carries missing keys) | `scripts/agent/tool_policy.py` | Phase 2 | AC-1 | key-union test | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; Required Changes 2; Acceptance Criteria 1-2 | `scripts/agent/tool_policy.py` | Phase 2 | AC-1, AC-2 | list/repo denial test | Confirmed by repository evidence |
| REQ-003 | Required Changes 1; Constraints (no fail-open); Acceptance Criteria 3 | `scripts/agent/tool_policy.py` | Phase 2 | AC-3 | unknown-tool test | Confirmed by repository evidence |
| REQ-004 | Implementation Intent; Required Changes 3; Acceptance Criteria 2 | `scripts/agent/tool_audit.py` | Phase 3 | AC-2 | audit resource_scope test | Confirmed by repository evidence |
| REQ-005 | Testing Expectations; Acceptance Criteria 4; AI Implementation Instruction | `tests/agent/test_tool_policy.py` | Phase 1, Phase 4 | AC-1, AC-2, AC-3, AC-4 | whole suite | Explicit in issue |
| REQ-003 | Amendment 2026-11-03: check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | scripts/agent/tool_approval.py | Phase 1 | N/A: none cites REQ-003 | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-03: check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | scripts/agent/repository_gateway.py | Phase 1 | N/A: none cites REQ-003 | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-03: check_preflight gained an optional registry parameter; this site holds the registry but did not pass it, so declared keys were never inspected at runtime | scripts/agent/tool_runner.py | Phase 1 | N/A: none cites REQ-003 | tests/agent/test_tool_approval_preflight.py, test_repository_gateway.py, test_tool_runner.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-154504 -->