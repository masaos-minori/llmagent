## Goal

Make `ApprovalConfig.gitops_push_blocked` reloadable via `/reload` by adding its
diff-apply line to `_reload_approval_config()` in
`scripts/agent/services/config_reload.py` (REQ-001: add the missing diff-apply for
`gitops_push_blocked`, matching the existing pattern used for the function's other
fields).

## Scope

- In scope: `scripts/agent/services/config_reload.py` —
  `_reload_approval_config()` gains one `if (vb := _get_bool(new_cfg,
  "gitops_push_blocked")) is not None: approval.gitops_push_blocked = vb` block,
  following the exact style of the function's 9 existing field blocks.
- In scope: `tests/agent/services/test_config_reload.py` — add a characterization
  test confirming `gitops_push_blocked = true` in the reload payload updates
  `ctx.cfg.approval.gitops_push_blocked`.
- Out of scope (per Plan): the meaning/default of `gitops_push_blocked` itself; any
  change to the other 9 fields `_reload_approval_config()` already handles; the
  validator-reexecution mechanism (tracked separately in
  `issues/20260825_cfgreload_missing_validator_reexecution_issue.md` — no
  `validate_*` function exists for `gitops_push_blocked` today, so it is not a
  prerequisite here).

## Assumptions

- **CORRECTED**: The `gitops_push_blocked` diff-apply already exists in code. Verified at `scripts/agent/services/config_reload.py:552-553`: `if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None: approval.gitops_push_blocked = vb`. No further action needed on this implementation procedure.

## Design decisions

- Follow the established `if (vb := _get_bool(new_cfg, "<field>")) is not None:
  approval.<field> = vb` walrus-assignment pattern used by every other field in this
  function (`config_reload.py:412-428`) and by boolean fields elsewhere in the same
  class (e.g. `_reload_approval_settings()`'s `memory_local_only` /
  `security_lockdown_enabled` blocks at lines 458, 468) — no new abstraction, no
  helper function, single line addition.
- Insert the new block as the last statement in `_reload_approval_config()`, after
  the existing `approval_github_allowed_repos` block (currently ending at line 428),
  preserving the function's existing field order (new field appended at the end
  rather than interleaved, since it has no ordering dependency on the others).

## Alternatives considered

- Add the diff-apply to `_reload_approval_settings()` instead (the function that
  wraps `_reload_approval_config()` plus the tool/memory/security fields): rejected
  — `gitops_push_blocked` is an `ApprovalConfig` field like the other 9, so it
  belongs in `_reload_approval_config()`, matching Plan Requirements/REQ-001 exactly.
- Add explicit `.applied` reporting for this one field so it would surface in the
  reload report even though the other 9 approval fields do not: rejected as out of
  scope — the Plan's In-Scope is limited to the diff-apply line, and singling out
  `gitops_push_blocked` for `.applied` reporting while its 9 siblings remain
  unreported would be an inconsistent, undocumented behavior change not requested by
  any Requirement; if reload-report visibility is wanted for the approval domain as a
  whole, that is a separate Plan-level decision.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Open `_reload_approval_config()` (`scripts/agent/services/config_reload.py:405-429`).
2. After the existing `approval_github_allowed_repos` block (lines 428-429), add:
   ```python
   if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None:
       approval.gitops_push_blocked = vb
   ```
3. No other line in this function or its call site (`apply_config_dict()`,
   `config_reload.py:122`, which calls `_reload_approval_settings()` ->
   `_reload_approval_config()`) needs to change — the new block is picked up
   automatically because `_reload_approval_config()` is already invoked on every
   `apply_config_dict()` call.

### Method

Single-line diff-apply addition, no refactor, no new imports, no signature change.

### Details

Current end of `_reload_approval_config()` (verified at
`scripts/agent/services/config_reload.py:426-430`):

```python
        if (v := _get_str(new_cfg, "allowed_root")) is not None:
            approval.allowed_root = v
        if (lst := _get_list(new_cfg, "approval_github_allowed_repos")) is not None:
            approval.approval_github_allowed_repos = list(lst)

    def _detect_startup_only(
```

Target state:

```python
        if (v := _get_str(new_cfg, "allowed_root")) is not None:
            approval.allowed_root = v
        if (lst := _get_list(new_cfg, "approval_github_allowed_repos")) is not None:
            approval.approval_github_allowed_repos = list(lst)
        if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None:
            approval.gitops_push_blocked = vb

    def _detect_startup_only(
```

Test addition in `tests/agent/services/test_config_reload.py`: add a new test class
following the existing `_make_svc()` -> `(ConfigReloadService, ctx)` tuple pattern
already used by `TestRuntimeToolPolicyReapplication` (lines 293-306):

```python
class TestReloadApprovalConfigGitopsPushBlocked:
    """gitops_push_blocked must be reloadable via _reload_approval_config()."""

    def _make_svc(self, gitops_push_blocked: bool = False) -> tuple[object, object]:
        from agent.services.config_reload import ConfigReloadService

        ctx = MagicMock()
        ctx.cfg.approval.gitops_push_blocked = gitops_push_blocked
        return ConfigReloadService(ctx), ctx

    def test_gitops_push_blocked_true_updates_config(self) -> None:
        svc, ctx = self._make_svc(gitops_push_blocked=False)
        svc._reload_approval_config(ctx, {"gitops_push_blocked": True})
        assert ctx.cfg.approval.gitops_push_blocked is True

    def test_missing_key_leaves_config_unchanged(self) -> None:
        svc, ctx = self._make_svc(gitops_push_blocked=True)
        svc._reload_approval_config(ctx, {})
        assert ctx.cfg.approval.gitops_push_blocked is True
```

Exact placement (new class vs. new methods on an existing class) and naming may be
adjusted during implementation as long as the test calls `_reload_approval_config()`
(or `apply_config_dict()`) with `gitops_push_blocked` present/absent in the payload
and asserts the resulting `ctx.cfg.approval.gitops_push_blocked` value, per the
Plan's Tests section.

## Compatibility considerations

- `_reload_approval_config()` is module-private; no public API surface change.
- No config file format, TOML key, or CLI-visible behavior change — `agent.toml`'s
  `gitops_push_blocked` key already exists and is read at startup
  (`scripts/agent/config_builders.py:409,420`); this change only makes the running
  process pick up a changed value without a restart.
- The Plan's other 9 fields in this function and `_reload_approval_settings()`'s
  other fields are untouched (out of scope, per Plan Scope).

## Security considerations

- `gitops_push_blocked` gates all GitHub write operations
  (`scripts/agent/tool_approval.py:138-143`). Making it hot-reloadable is
  security-relevant in that an operator can now flip it live; the change is
  fail-safe in both directions (setting it `True` restricts writes immediately,
  setting it `False` restores the startup-time default behavior) and does not
  introduce any new attack surface — the field was already trusted config-file
  input, only now consumable through the same authenticated `/reload` path as the
  other 9 `ApprovalConfig` fields.
- No new logging of secrets; the diff-apply pattern here matches the existing 9
  fields exactly, none of which log values.

## Rollback considerations

- Single-file, single two-line addition (plus its test), no data migration, no
  config schema change, no new persistent state. Revert via `git revert` of the
  implementing commit; no follow-up cleanup needed.

## Validation plan

- `uv run pytest tests/agent/services/test_config_reload.py -v` — new test(s) green;
  existing tests in this file (including the 9-field-adjacent
  `TestRuntimeToolPolicyReapplication`, `TestStartupOnlyDetection` classes) show no
  regressions.
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` — no regressions
  (this file exercises `ConfigReloadOutcome` rendering and could be affected if
  `.applied` behavior were mistakenly changed; it should not be, per Design
  decisions above).
- `uv run pytest` (full suite) — no new failures.
- `uv run mypy scripts/` — no new errors.
- `rg -n "gitops_push_blocked" scripts/agent/services/config_reload.py` — one match
  after the change (currently zero).

## Completion criteria

- `_reload_approval_config()` in `scripts/agent/services/config_reload.py` contains
  the `gitops_push_blocked` diff-apply block described in Details above.
- A new or extended test in `tests/agent/services/test_config_reload.py` confirms
  that calling `_reload_approval_config()` (directly or via `apply_config_dict()`)
  with `gitops_push_blocked` present in the payload updates
  `ctx.cfg.approval.gitops_push_blocked` to the payload's value, and that omitting
  the key leaves the existing value unchanged.
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/commands/test_agent_cmd_config.py -v` and the full `uv run pytest` suite are green.
- `uv run mypy scripts/` shows no new errors vs. pre-existing baseline.

## Out of scope

- The semantics/default value of `gitops_push_blocked` (per Plan Scope).
- Any change to the other 9 fields `_reload_approval_config()` already handles, or
  to `_reload_approval_settings()`'s tool/memory/security fields (per Plan Scope).
- Adding `.applied`-report visibility for `gitops_push_blocked` or for the approval
  domain generally — none of the existing 9 approval fields report to `.applied`
  either; changing that is a separate Plan-level decision, not part of REQ-001 (see
  Alternatives considered above).
- The validator-reexecution mechanism tracked in
  `issues/20260825_cfgreload_missing_validator_reexecution_issue.md` (per Plan
  Out-of-Scope — no `validate_*` function exists for `gitops_push_blocked` today).
- `deploy/deploy.sh` changes — none needed (no file added, removed, or moved;
  `scripts/` is rsynced wholesale per `rules/toolchain.md`).
- Note for cross-plan awareness (not an action item for this document): the sibling
  plan `plans/20260825-141157_plan.md` also targets this same file — its generated
  document (`implementations/20260826-100937_01_scripts_agent_services_config_reload.py.md`)
  splits `_reload_approval_settings()` into four helpers and rewires
  `apply_config_dict()`'s call site, but explicitly keeps `_reload_approval_config()`
  itself (this document's edit target) unchanged and out of its scope. The two
  changes touch disjoint code regions in the same file with no ordering dependency
  between them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `gitops_push_blocked` diff-apply block to `_reload_approval_config()` (REQ-001) | Obsolete | — | — | Already implemented at config_reload.py:552-553 |
| 2 | Add characterization test(s) to `tests/agent/services/test_config_reload.py` | Obsolete | — | — | Prerequisite step already done |
| 3 | Run the validation sequence | Obsolete | — | — | N/A |
| 4 | Confirm no deploy.sh update needed | Obsolete | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| All | Document describes work already implemented in source code | Yes | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (add `gitops_push_blocked` diff-apply to `_reload_approval_config()`)
- **Source issue**: `issues/20260825_cfgreload_gitops_push_blocked_not_reloadable_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-141653_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-101556
- **Related target files**: `scripts/agent/services/config_reload.py`
