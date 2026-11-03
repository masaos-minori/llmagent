# Implementation Procedure: scripts/agent/tool_audit.py (pathkeys001 seq 02)

## Goal
Change `scripts/agent/tool_audit.py` `_extract_resource_scope` so a list-valued path argument is
recorded as its elements joined into one scope value (`REQ-004`: audit records list elements in
joined string form — today the whole list lands as a Python repr like `['/etc/shadow', ...]`) and the
extracted path keys are the configured `approval_resource_keys.path_keys` unioned with the
registered tool's declared `resource_scope_keys` (`REQ-005`), so `tool_approval` / `tool_exec`
audit events for `read_multiple_files` and git tools name the checked paths in readable form.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current behavior (verified against source, lines 45-49): `_extract_resource_scope` keeps every
  masked argument whose key is in configured `path_keys | branch_keys` and records `str(v)`, so a
  list value is already present in the event but as a repr string — `REQ-004` asks for the joined
  element form, not for adding previously-missing keys on the scalar side.
- `_extract_resource_scope` does not receive the tool name today; the procedure adds an optional
  trailing `tool_name: str | None = None` parameter so direct calls (and any test calling the
  private function) keep working, while the two audit writers pass the name they already hold.
- The runtime registry is reachable at both call sites: `audit_approval` (writer for line 84) and
  `audit_tool_exec` (writer for line 202) each already use `ctx.services_required.runtime_tools`
  for `classify_operation_type` (lines 90 and 207), so no availability guard beyond the `KeyError`
  fallback is added.
- `tests/agent/test_tool_audit.py` exercises the audit writers through a `MagicMock` audit logger
  and contains no list-valued path fixtures; it is a validation target only — it is not a target
  row of this Plan and must not be edited in this cycle.
- `tools/check_plan_target_overlaps.py` re-run at Step 2 of this cycle: no finding names this Plan.
  This row's target was already in the frozen table before the 2026-11-04 amendment.

## Design decisions
- Plan `REQ-004` joined form: list elements become one value `a;b` (each element stringified,
  empty-string elements dropped). Rejected alternatives: keeping the Python repr (unreadable for
  downstream parsing, the exact gap the Plan Problem reports) and JSON serialization (format churn
  for no fidelity gain).
- Empty list values are no longer recorded (today they render as `[]`): an empty scope entry adds
  no evidence. Scalar values keep today's `str(v)` semantics exactly, including empty strings.
- Unknown tool names and `KeyError` from `runtime_tools.get` fall back to configured keys only,
  mirroring sibling `20261104-065555_01` so audit keys and checked keys agree (`REQ-005`).
- Optional trailing `tool_name` parameter instead of a required one: the two writers always pass
  it, but the parameter shape stays backward compatible for any other caller.

## Alternatives considered
- Resolving declared keys from `ctx` alone without the tool name: rejected — `AgentContext` does
  not carry the tool name of the call being audited; both writers hold it and can pass it.
- Adding a new module-level key-resolution helper: rejected for this file — the union is one small
  expression inside `_extract_resource_scope`, and the policy-side sibling owns the shared
  resolution semantics.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
1. Replace the `_extract_resource_scope` body (lines 45-49) with the union-key, list-aware version
   below, adding the optional trailing `tool_name` parameter.
2. Pass the tool name at the two call sites: line 84 in `audit_approval` and line 202 in
   `audit_tool_exec` (both already hold `tool_name` as a parameter).
3. Single-block edit:

```python
# Before (lines 45-49):
def _extract_resource_scope(ctx: AgentContext, masked: dict) -> dict[str, str]:
    """Pull path/branch keys from masked args for audit events."""
    path_keys = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    branch_keys = set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    return {k: str(v) for k, v in masked.items() if k in path_keys | branch_keys}

# After:
def _extract_resource_scope(
    ctx: AgentContext,
    masked: dict,
    tool_name: str | None = None,
) -> dict[str, str]:
    """Pull path/branch keys from masked args for audit events.

    Path keys are the configured path_keys unioned with the registered tool's
    declared resource_scope_keys; a list value is recorded as its non-empty
    elements joined with ';'.
    """
    path_keys = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    if tool_name is not None:
        try:
            declared = ctx.services_required.runtime_tools.get(tool_name)
            path_keys |= set(declared.resource_scope_keys)
        except KeyError:
            pass
    branch_keys = set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    scope: dict[str, str] = {}
    for key, value in masked.items():
        if key not in path_keys | branch_keys:
            continue
        if key in path_keys and isinstance(value, list):
            entries = [str(item) for item in value if str(item)]
            if entries:
                scope[key] = ";".join(entries)
        else:
            scope[key] = str(value)
    return scope
```

Call sites:

```python
# Before (line 84 in audit_approval, line 202 in audit_tool_exec):
    resource_scope = _extract_resource_scope(ctx, masked)
# After (both sites):
    resource_scope = _extract_resource_scope(ctx, masked, tool_name)
```

### Method
Edit `_extract_resource_scope` in place and the two call lines; no new module-level symbols, no
import change. `mask_args`, `_workflow_id_or_skip`, the event dataclasses, and both writers' other
logic are untouched.

### Details
- `resource_scope` flows into `ToolApprovalEvent.resource_scope` and `ToolExecEvent.resource_scope`
  as a `dict[str, str]`; the joined single-string form keeps that type unchanged (no nested
  structures for downstream event consumers).
- Denied executions reach `audit_tool_exec` through the `_ERROR_TYPE_DENIED` branch (line 196), so
  the `denied_root_jail` audit line produced after a sibling `20261104-065555_01` policy denial
  will carry the joined list — land this after `_01` to see the end-to-end effect.
- `branch_keys` values keep today's `str(v)` handling exactly (Plan A3: list handling stays scoped
  to path keys).
- Test ownership: the failing-baseline audit assertions for this procedure (denied multi-path call
  records `resource_scope["paths"]` in the joined element form; declared-key `repo_path` recorded;
  unregistered-name fallback) land in `tests/agent/test_tool_policy.py`, which is this Plan's row 3
  and is owned by sibling `20261104-065555_01`'s companion procedure — this document adds no test
  file of its own. `tests/agent/test_tool_audit.py`, named loosely by this row's Related Tests
  cell, is not a Plan row and stays untouched (run as a regression check only).

## Compatibility considerations
- Scalar and branch-key audit values are byte-identical to today; only list-valued path keys
  change format (repr string → joined elements), and empty lists change from `[]` to absent.
- Existing callers of `_extract_resource_scope` that omit `tool_name` keep the configured-keys
  behavior; no other file imports this private function (verified by grep across `scripts/`).

## Security considerations
- Audit evidence for a path jail denial names each offending path readably; masked fields from
  `mask_args` are unchanged, and the change never adds values beyond what the caller passed.

## Rollback considerations
- N/A: revert the single commit; no schema, config, or deploy change.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_audit.py` — new assertions
  fail before the change; both files green after it.
- `uv run ruff check scripts/agent/tool_audit.py tests/agent/test_tool_policy.py` and
  `uv run ruff format --check` on both.
- `uv run mypy --no-namespace-packages scripts/ tests/agent/test_tool_policy.py` — clean on the
  changed signature.
- `uv run bandit -r scripts/agent/tool_audit.py -c pyproject.toml` — no NEW findings (the 3
  pre-existing High findings in this file are out of scope per the Plan Risks).
- Diff-scoped coverage per `rules/toolchain.md` section 7 (`diff-cover --fail-under=90`).

## Completion criteria
- A denied `read_multiple_files` audit event's `resource_scope["paths"]` lists every non-empty
  element joined with `;` (AC-1 audit half).
- A git tool audit event records `repo_path` under the declared key even when the configured
  `path_keys` does not name it (AC-2 audit half).
- Unregistered tool names fall back to configured keys and raise nothing (AC-3 audit half).
- All existing `tests/agent/test_tool_audit.py` and `tests/agent/test_tool_policy.py` tests pass
  (AC-4), with scalar scope values unchanged.

## Out of Scope
- Changing `mask_args`, the event dataclasses, denial codes, or where/when audit events are written.
- Editing `tests/agent/test_tool_audit.py` (not a target row of this Plan).
- The policy-side checking change (sibling `20261104-065555_01`) and the three preflight call-site
  updates (siblings `20261104-065555_04/_05/_06`).
- Redaction or retention policy for audit events.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the failing-baseline audit assertions land in sibling _01's companion test file (Plan Phase 1, row 3 ownership); confirm they fail on current code | Pending | — | — | See Details > test ownership |
| 2 | Implement the `_extract_resource_scope` rewrite and the two call-site edits per Implementation > Procedure/Method/Details | Pending | — | — | Land after sibling _01 |
| 3 | Re-run companion and audit suites (all green) and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (audit records list elements, joined form), REQ-005 (audit key union)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-155552_pathkeys001_path-checks-skip-lists.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-065555
- **Related target files**: `scripts/agent/tool_audit.py`, `tests/agent/test_tool_policy.py`
