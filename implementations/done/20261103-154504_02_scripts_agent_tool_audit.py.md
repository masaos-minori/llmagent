## Goal

Make the audit `resource_scope` follow the arguments a tool actually declares
(`resource_scope_keys` in the tool registry) in addition to the configured
`approval_resource_keys.path_keys`, and record every string element of a list-valued
path argument, so the audit `resource_scope` for `read_multiple_files.paths` and
`git.repo_path` is no longer blind to those paths.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **A1**: Both callers of `_extract_resource_scope` (`audit_approval` at
  `scripts/agent/tool_audit.py:84`, `audit_tool_exec` at `:202`) have `tool_name` and
  `ctx.services_required.runtime_tools` available (the same registry passed to
  `classify_operation_type` at `:91`).
- **A2**: The audit is best-effort: if the registry lookup fails or the tool is
  unregistered, fall back to the configured `path_keys`/`branch_keys` only — the audit
  must never raise and block logging (unlike the preflight, which fails closed).
- **A3**: The declared keys are unioned with the configured keys, mirroring
  `scripts/agent/tool_policy.py` (pathkeys001 seq 01), so the two layers agree on which
  argument names are path-like.
- **A4**: `git-fame`/`pydeps`/`grimp` are unavailable; `Churn (30d)` and `Bus Factor`
  are judged from `git log` churn and marked where the tool is missing.
- **A5**: This Plan overlaps `assertaudit001`/`toolaudit001` on
  `scripts/agent/tool_audit.py` (per `check_plan_target_overlaps.py`). Compatible and
  orthogonal: this Plan changes `_extract_resource_scope` key resolution; the others
  change unrelated audit events.

## Design decisions
1. **DD-1 — Resolve the union in the audit.** Thread `tool_name` into
   `_extract_resource_scope` and union the configured `path_keys`/`branch_keys` with the
   registered tool's `resource_scope_keys` (A3). On registry failure or an unregistered
   tool, fall back to the configured keys only (A2) — the audit stays non-fatal.
2. **DD-2 — Expand list values.** For a matching key whose value is a `list`, record
   every string element rather than the `str()` repr of the whole list, so each touched
   path appears in `resource_scope`. Represent the elements in the `dict[str, str]`
   return by joining them with `\n` (preserves the field shape while capturing all
   elements).

## Alternatives considered
- **Change `_extract_resource_scope`'s return type to hold multiple values per key**
  (rejected: ripples through `ToolApprovalEvent`/`ToolExecEvent` and every audit
  consumer; a joined string preserves the existing `dict[str, str]` shape).
- **Fail closed on an unregistered tool** (rejected: the audit must not block logging;
  A2).

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Add a `tool_name: str` parameter to `_extract_resource_scope` and resolve the checked
   key set: the union of the configured `ctx.cfg.approval.approval_resource_keys`
   `path_keys`/`branch_keys` and the registered tool's `resource_scope_keys`. Guard the
   registry lookup so a failure or unknown tool falls back to the configured keys (A2).
2. For each key present in `masked`: if the value is a `str`, emit `k: str(value)`; if
   it is a `list`, emit `k` joined with `\n` of its string elements (skip non-string
   elements). Keys outside the resolved union are excluded as before.
3. Update both callers to pass `tool_name`: `audit_approval` (`:84`) and
   `audit_tool_exec` (`:202`).

### Method
- `_extract_resource_scope` reads `ctx.services_required.runtime_tools` (already present
  at both call sites) to resolve declared keys; the lookup is wrapped so the audit never
  raises.
- List expansion keeps the `dict[str, str]` contract; joining with `\n` preserves every
  element in the single audit field.

### Details
```python
def _extract_resource_scope(
    ctx: AgentContext,
    tool_name: str,
    masked: dict,
) -> dict[str, str]:
    """Pull path/branch keys from masked args for audit events.

    Resolves the union of the configured path/branch keys and the tool's declared
    resource_scope_keys; expands list values so every touched path is recorded.
    Falls back to the configured keys when the registry is unavailable.
    """
    declared: set[str] = set()
    registry = getattr(ctx.services_required, "runtime_tools", None)
    if registry is not None:
        try:
            tool = registry.get(tool_name)
            declared = set(getattr(tool, "resource_scope_keys", ()) or ())
        except KeyError:
            declared = set()  # unregistered tool -> configured keys only (A2)
        except Exception:
            declared = set()  # best-effort: never block logging
    configured = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    configured |= set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    keys = declared | configured
    scope: dict[str, str] = {}
    for k, v in masked.items():
        if k not in keys:
            continue
        if isinstance(v, str):
            scope[k] = str(v)
        elif isinstance(v, list):
            scope[k] = "\n".join(str(item) for item in v if isinstance(item, str))
        else:
            scope[k] = str(v)
    return scope
```
- `audit_approval`: `resource_scope = _extract_resource_scope(ctx, tool_name, masked)`.
- `audit_tool_exec`: `resource_scope = _extract_resource_scope(ctx, tool_name, masked)`.

## Compatibility considerations
- `_extract_resource_scope` gains one required parameter (`tool_name`); both callers are
  updated. It is a private module-level function (no external importers beyond these two).
- The `dict[str, str]` return shape is unchanged; list values are represented as a
  newline-joined string (A backward-incompatible shape change is avoided).
- Fallback-to-configured-keys keeps today's output for tools that declare no scope keys.

## Security considerations
- The audit `resource_scope` now records list-valued (`paths`) and differently-named
  (`repo_path`) paths, so post-hoc review sees every touched path. The lookup is
  best-effort and never raises, so audit logging stays available.

## Rollback considerations
- Single-module change; revert the commit.

## Validation plan
- Unit: `uv run pytest tests/agent/` audit tests — all pass; the new behavior is covered
  by pathkeys001's companion tests in `tests/agent/test_tool_policy.py` (preflight) and a
  small audit assertion if added.
- Static: `uv run ruff`, `uv run mypy --no-namespace-packages`, `uv run bandit` on
  `scripts/agent/tool_audit.py` — clean; no new findings beyond the pre-existing ones.
- Scope guard: `git diff --stat` shows no change outside `scripts/agent/tool_audit.py`.

## Completion criteria
- The audit `resource_scope` for a call includes the declared `resource_scope_keys`
  (`paths`/`repo_path`) in addition to the configured keys; a list-valued argument
  records every string element; an unregistered or registry-less call falls back to the
  configured keys without raising; existing audit tests still pass.

## Out of Scope
- Changing the `ToolApprovalEvent`/`ToolExecEvent` `resource_scope` field shape.
- Fail-closed behavior (the audit stays non-fatal; see A2).
- Any change to the audit event schema or other audit writers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261103 | 20261103 | `except Exception` narrowed to `(KeyError, TypeError)` (BLE001) |
| 2 | Add or update tests per Validation plan | Completed | 20261103 | 20261103 | Covered by tool_policy preflight tests + audit suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103 | 20261103 | ruff/ruff-format/mypy/bandit clean; 691 related tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103 | 20261103 | — |

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
- **Requirement ID**: `REQ-004` (audit `_extract_resource_scope` resolves the union of declared and configured keys and checks every string element of a list-valued argument)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-155552_pathkeys001_path-checks-skip-lists.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-154504
- **Related target files**: `scripts/agent/tool_audit.py`
