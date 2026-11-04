## Goal
Close the path-policy gap in `scripts/agent/tool_policy.py`: the preflight and risk escalation resolve the checked path argument names from the registered tool's declared `resource_scope_keys` unioned with the configured `path_keys` (`REQ-001`: key union), check every string element of a list-valued path argument and fail closed on a value that is neither `str` nor `list[str]` (`REQ-002`: list handling and fail-closed), and thread `RuntimeToolRegistry` as an optional registry into `check_preflight`, `check_allowed_root`, and `_escalate_for_path` so an unknown tool never fails open (`REQ-003`: registry threading).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Plan A1: configured `path_keys` values are strings in practice, so applying the uniform fail-closed rule (str → check; `list[str]` → check each element; anything else → deny) does not regress any currently-valid configured-key call; the untouched existing suite confirms it (`AC-4`).
- Plan UNK-02 resolved uniformly here (non-blocking `Needs confirmation` caveat): a non-string value fails closed under both configured and declared keys, because `REQ-002` does not scope the rule to declared keys only. If the owner later wants the rule scoped to declared-only keys, relax it in the same helper and test.
- Plan A3/DD-2: the shared `_iter_string_arg_values` is NOT modified — the same helper feeds the `branch_keys` loop in `_escalate_for_github_branch`, and list handling stays scoped to path extraction.
- The new `registry` parameters default to `None`, so callers that omit them (the existing test suite, and any call site not yet updated by siblings `20261104-065555_04/_05/_06`) keep today's configured-key behavior exactly.
- `tools/check_plan_target_overlaps.py` re-run at Step 2 of this cycle after the 2026-11-04 amendment: no finding names this Plan.
- Verification note (2026-11-04): the union is applied to ALL of a registered tool's `resource_scope_keys` with no `resource_scope_kind` filter. Confirmed against source: `github_*` tools declare `["owner", "repo"]` and cicd tools declare `["repo", "workflow", "ref"]`/`["repo", "run_id"]`, so those values become path-checked when `allowed_root` is set — they are relative non-path strings and pass `is_relative_to` when the agent cwd is inside `allowed_root`; the Plan's reproduction explicitly includes the `mdq` tool's `paths=["/etc"]` (kind `mdq_store`), which rules out a filesystem-only filter.
- Amendment recorded in this cycle (owner-approved, class `scope`): rows `scripts/agent/tool_approval.py`, `scripts/agent/repository_gateway.py`, `scripts/agent/tool_runner.py` were appended to the Plan's frozen table because the Scope bullet "the declared keys are reachable at every preflight call site" requires them; they are covered by sibling procedures, not this document.

## Design decisions
- Key resolution lives in one new module-private helper `_resolve_path_keys` (new) in `tool_policy.py`: configured `approval_resource_keys.path_keys` unioned with `registry.get(tool_name).resource_scope_keys`; `registry=None` or a `KeyError` (unregistered tool) falls back to the configured keys only — an unknown tool never bypasses the configured checks and never raises out of the policy (`REQ-003`).
- A second new helper `_iter_path_arg_values` (new) is the path-scoped iterator: a non-empty `str` value yields as today; a `list` value yields each non-empty `str` element; a value that is neither, or a `list` containing a non-string element, is reported as not-inspectable and the callers fail closed (`check_allowed_root` → deny → `denied_root_jail`; `_escalate_for_path` → `RiskLevel.HIGH`). Denial codes are unchanged (`REQ-002`).
- Plan DD-1 Option A: `check_preflight`, `check_allowed_root`, and `_escalate_for_path` each gain a trailing optional `registry: RuntimeToolRegistry | None = None`; `classify_risk` already takes the registry and passes it (with `tool_name`) down to `_escalate_for_path`.
- Plan DD-3: union, not replace — a tool that declares no scope keys still falls back to the configured list.
- Plan D1: this document cites only this Plan's `REQ-001`..`REQ-005`; the inline `REQ-` annotations already in `tool_policy.py` for the pre-existing matching mechanism are a separate labeling and stay untouched.

## Alternatives considered
- Plan DD-1 Option B (resolve the union once in `check_approval` and pass the key list down) — rejected: splits the signature change across more functions and duplicates the availability check per site.
- Modifying the shared `_iter_string_arg_values` to handle lists — rejected (Plan A3): it would change `_escalate_for_github_branch` behavior.
- Making the `registry` parameter required — rejected: breaks the existing suite and every not-yet-updated caller, and the Plan's DD-1 explicitly chose the optional parameter.

## Implementation
### Target file
`scripts/agent/tool_policy.py`
### Procedure
1. Add `_resolve_path_keys` (new): given `cfg`, `tool_name`, and the optional registry, return the configured `path_keys` plus the registered tool's `resource_scope_keys`; on `KeyError` from `RuntimeToolRegistry.get` return the configured keys only.
2. Add `_iter_path_arg_values` (new): yield each non-empty string value under the resolved keys, yielding each non-empty string element of a `list` value; expose a way for the caller to detect a not-inspectable value (neither `str` nor `list[str]`, or a list containing a non-string element).
3. `check_allowed_root` gains the optional trailing `registry` parameter; iterate with `_iter_path_arg_values` (new) over `_resolve_path_keys` (new) output; a not-inspectable value returns `False` (denies); the existing `Path.resolve` / `is_relative_to` jail logic and the `denied_root_jail` code are unchanged.
4. `check_preflight` gains the optional trailing `registry` parameter and passes it to `check_allowed_root`; `denied_allowed_tools` and `denied_repo_allowlist` handling is unchanged.
5. `_escalate_for_path` gains `tool_name` and the optional `registry` parameters and uses the same resolved keys and list handling; a not-inspectable value returns `RiskLevel.HIGH`. `classify_risk` passes its existing `registry` and `tool_name` into it.
6. Leave `_iter_string_arg_values`, `_escalate_for_github_branch`, `check_allowed_repo`, and `classify_risk`'s public signature unchanged. Signature edits in one line each:

```python
# Before:
def _escalate_for_path(
    cfg: AgentConfig,
    base: RiskLevel,
    args: dict[str, Any],
) -> RiskLevel | None:

def check_allowed_root(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> bool:

def check_preflight(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> None:
# After:
def _escalate_for_path(
    cfg: AgentConfig,
    tool_name: str,
    base: RiskLevel,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> RiskLevel | None:

def check_allowed_root(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> bool:

def check_preflight(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> None:
```

(Adding `tool_name` to `_escalate_for_path`'s positional list is safe: it is private and only called from `classify_risk`, which already holds both values.)

### Method
Edit the three functions in place and add the two private helpers near `_iter_string_arg_values` in the same file. No new public symbols, no import change (re-verified 2026-11-04: `tool_policy.py` has `from __future__ import annotations` at line 9 and `RuntimeToolRegistry` is already imported under the module's TYPE_CHECKING import block at line 35, exactly as the annotations in `classify_operation_type` and `classify_risk` already rely on).

### Details
- Current behavior (verified against source): `_iter_string_arg_values` yields a value only when it is a non-empty `str`, so `paths=["/etc/shadow", ...]` yields nothing; `check_allowed_root` and `_escalate_for_path` read only `cfg.approval.approval_resource_keys.get("path_keys", [])`; `classify_risk` returns `RiskLevel.NONE` for `READ_ONLY`/`WRITE_SAFE` tiers before escalation runs, so the denial that matters for those tools is the `check_allowed_root` one.
- The declared keys to union already exist in the registry metadata: `read_multiple_files` declares `resource_scope_keys` `["paths"]` (`scripts/mcp_servers/file/read_tools.py`), the git tools declare `["repo_path"]` (`scripts/mcp_servers/git/git_tools.py`); `RuntimeToolRegistry.get` raises `KeyError` for an unregistered tool (`scripts/shared/runtime_tool_registry.py`), which is what makes the fallback branch testable.
- `scripts/shared/resource_scope.py` `resolve_resource_scopes` is the metadata-driven model this mirrors; it is a reference file and must not change.
- Empty-string elements keep today's skip semantics (non-empty check), so an empty path value cannot smuggle a deny or a pass.

### Companion test files
- `tests/agent/test_tool_policy.py`
  - Procedure: extend the `TestClassifyRisk._registry_with` pattern (or a new module-level helper) so stub `RuntimeTool` entries can declare `resource_scope_keys`; add failing-baseline tests (Plan Phase 1): `read_multiple_files` with `paths=[inside, outside]` is denied (`denied_root_jail`) while `paths=[inside, inside]` passes; a git tool with `repo_path` outside `allowed_root` is denied; a list element check; a not-inspectable value (e.g. `path=123`) denies; an unregistered tool name with a list under a configured key still denies (configured keys apply, no raise); the five configured keys behave as before. Run once first to confirm the new tests FAIL on current code (baseline), then re-run after the source change.
  - Verification note (2026-11-04): the audit-line assertions owned by sibling `20261104-065555_02` (a denied multi-path call records `resource_scope` `paths` as the joined element form, and a declared-key `repo_path` is recorded) also live in this test file, but they are added during the `_02` cycle, not this one — they fail until `tool_audit.py` implements the union, and this procedure's Step 3 gates on the companion suite being all green.
  - Validation: `uv run pytest tests/agent/test_tool_policy.py` — new tests fail before the change and all tests (existing included) pass after it.

## Compatibility considerations
- Trailing optional parameters keep every existing call (suite and production) valid and behavior-identical until siblings `20261104-065555_04/_05/_06` pass the registry at the three preflight call sites.
- A list value under a configured key is denied today where it was skipped before — an intentional behavior change covered by Plan Assumption A1 and the whole-suite `AC-4` check.
- shellprefix001 (already implemented and archived) shares this file and test file; this change does not touch the `shell_run` prefix path or its tests, so no reconciliation is pending.
- `config/agent.toml` is a reference file and does not change.
- Verification note (2026-11-04): "only called from `classify_risk`" holds for production code, but three existing direct test calls in `tests/agent/test_tool_policy.py`
  (`_escalate_for_path(cfg, base, args)` in `TestCheckPreflight`, lines 338-359) use the 3-arg positional form. They are updated mechanically to pass a `tool_name` in
  Step 2 of this cycle, alongside the signature change; their assertions are unchanged.

## Security considerations
- Fail-closed is the requirement: an unknown tool keeps the configured checks (`KeyError` fallback), a not-inspectable path-like value denies rather than passes, and the union only adds checks — it never removes the configured ones (Plan DD-3).
- A stable defense-in-depth layer for `paths`/`repo_path` arguments closes the false-assurance gap the Plan Problem describes; server-side enforcement remains unchanged and out of scope.

## Rollback considerations
- N/A: revert the single commit; no schema, config, or deploy change.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py` — failing baseline first, then all green including the existing path/repo/prefix cases.
- `uv run ruff check scripts/agent/tool_policy.py tests/agent/test_tool_policy.py` and `uv run ruff format --check` on both.
- `uv run mypy --no-namespace-packages scripts/ tests/agent/test_tool_policy.py` — clean on the touched signatures.
- `uv run bandit -r scripts/agent/tool_policy.py -c pyproject.toml` — no NEW findings. Verification note (2026-11-04): the Plan Risks' "3 pre-existing High findings" claim is stale; a run against HEAD today reports "No issues identified", so the gate is zero findings on this file.
- Diff-scoped coverage per `rules/toolchain.md` section 7 (`diff-cover --fail-under=90`) on the changed lines.

## Completion criteria
- A list-valued path argument with one element outside `allowed_root` is denied by the preflight; a list with all elements inside passes (AC-1).
- A git tool's `repo_path` outside `allowed_root` is denied (AC-2, policy half).
- An unregistered tool name never fails open: the configured keys still apply and no `KeyError` escapes the policy (AC-3).
- The five configured keys behave as before and the whole existing suite passes (AC-4).
- `_iter_string_arg_values` and `_escalate_for_github_branch` are unchanged in this file.

## Out of Scope
- Shell command path handling (`shell_run` prefixes, shell flag paths) — separate plans (shellprefix001 already done, shellrisk001 separate).
- Changing which risk tiers skip protected-path escalation (`classify_risk` early return for `READ_ONLY`/`WRITE_SAFE`).
- Resolving relative paths against the server working directory instead of the agent's.
- Any registry lookup that fails open for an unknown tool.
- Server-side enforcement (`FileAuthorizationError`, `allowed_repo_paths`, `read_single_file` jail).
- The audit `_extract_resource_scope` change (sibling procedure `20261104-065555_02`) and the three preflight call-site updates (siblings `20261104-065555_04/_05/_06`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the failing-baseline tests to the companion test file first (Plan Phase 1); confirm they fail on current code | Completed | 20261104-144113 | 20261104-144408 | Baseline: 9 failing tests confirmed (DID NOT RAISE / medium!=high / TypeError on 4-arg call), 2 pin tests green |
| 2 | Implement the helper additions and signature changes per Implementation > Procedure/Method/Details | Completed | 20261104-144408 | 20261104-150434 | Land before siblings _04/_05/_06 pass the registry |
| 3 | Re-run the companion suite (all green) and the validation sequence (`rules/toolchain.md`) | Completed | — | 20261104-150434 | 313 companion tests green; full suite 11456 passed; gates pass; diff-cover 100% |

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
- **Requirement ID**: REQ-001 (configured ∪ declared key union), REQ-002 (list elements checked, fail closed), REQ-003 (registry threaded, unknown tool never fails open)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261101-155552_pathkeys001_path-checks-skip-lists.md` (archived by
  commit `60d796777`; path corrected during Step 3a verification)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-065555
- **Related target files**: `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`