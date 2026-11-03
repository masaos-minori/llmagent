## Goal

Make the agent-side path policy (`check_allowed_root`, `_escalate_for_path`) and the
audit `resource_scope` follow the arguments a tool actually declares
(`resource_scope_keys` in the tool registry) in addition to the configured
`approval_resource_keys.path_keys`, and check every string element of a list-valued
path argument, so that list-valued paths (`read_multiple_files.paths`) and
differently-named path arguments (`git.repo_path`) are inspected by the preflight and
the audit instead of being skipped.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **A1**: The configured `path_keys` values are always strings in practice, so applying
  the fail-closed rule (str → check; `list[str]` → check each; else deny) does not
  regress any currently-valid configured-key call. Derived from the config usage, not an
  owner decision.
- **A2**: The declared keys are unioned with the configured keys rather than replacing
  them, so a tool that declares no scope keys still falls back to the configured list.
  Derived from the Issue's "additional source, not the only one" intent.
- **A3**: List handling is scoped to path extraction and does NOT modify the shared
  `_iter_string_arg_values`, because the same helper feeds `_escalate_for_github_branch`
  (branch escalation); changing it would alter branch behavior. Verified:
  `_iter_string_arg_values` (line 140) is read by both the `path_keys` loop in
  `check_allowed_root`/`_escalate_for_path` and the `branch_keys` loop in
  `_escalate_for_github_branch`.
- **A4**: `git-fame`/`pydeps`/`grimp` are unavailable; `Churn (30d)` and `Bus Factor`
  are judged from `git log` churn and marked where the tool is missing.
- **A5**: This Plan overlaps `shellprefix001` and `shellrisk001` on
  `scripts/agent/tool_policy.py` and `wfrecovery001`/`assertaudit001`/`toolaudit001` on
  `scripts/agent/tool_audit.py` (per `check_plan_target_overlaps.py`). These are
  compatible/orthogonal: this Plan changes path-argument extraction
  (`check_allowed_root`/`_escalate_for_path`/key resolution) and the audit
  `_extract_resource_scope`, while the others change the `shell_run` prefix path, shell
  flag paths, or unrelated audit events. Reconcile the shared
  `tests/agent/test_tool_policy.py` during implementation (non-blocking; either order
  works).
- **A6** (UNK-02 resolution): the fail-closed rule applies uniformly to a value that is
  neither `str` nor `list[str]` for both declared and configured keys. Safe per A1
  (configured keys are strings) and closes the unknown-shape gap the Issue describes.

## Design decisions
1. **DD-1 — How the declared keys reach the policy.** Thread an optional
   `RuntimeToolRegistry` into `check_preflight`, `check_allowed_root`, and
   `_escalate_for_path` (Option A, selected). All three call sites already hold the
   registry (`ctx.services_required.runtime_tools` at `tool_approval.py:168`,
   `repository_gateway.py:102`, `tool_runner.py:223`); `classify_risk` already receives
   it and uses the optional-registry convention (`registry=None` → fail closed to
   UNKNOWN). Optional parameter defaults to `None`, so callers/tests that omit it keep
   configured-key behavior. Option B (resolve the union once in `check_approval` and
   pass the key list down) was rejected: it duplicates the registry availability check
   at each site and splits the signature change across more functions.
2. **DD-2 — Scope of list handling.** Do not modify the shared `_iter_string_arg_values`
   (used by both the `path_keys` and `branch_keys` loops). Add path-scoped list handling
   so `_escalate_for_github_branch` is unaffected and the five-key behavior is preserved.
   Fail closed on a value that is neither `str` nor `list[str]`.
3. **DD-3 — Union vs. replace.** Union the declared keys with the configured keys rather
   than replacing them, so a tool that declares no scope keys still falls back to the
   configured list (A2).

## Alternatives considered
- **Resolve the union once in `check_approval` and pass the key list down** (rejected:
  duplicates the registry availability check at each of the three call sites and splits
  the signature change across more functions for the same result).
- **Fail open on an unknown tool** (rejected: the Issue requires fail-closed;
  `RuntimeToolRegistry.get()` raises `KeyError` for an unregistered tool, which the
  procedure treats as deny).
- **Modify the shared `_iter_string_arg_values` to handle lists** (rejected: it also
  feeds `_escalate_for_github_branch`, altering branch escalation; DD-2).

## Implementation
### Target file
`scripts/agent/tool_policy.py`

### Procedure
1. Add a module-level helper `_resolve_checked_path_keys` (new) (new) that returns the sorted
   unique set of path-key names to check: the union of the configured
   `cfg.approval.approval_resource_keys.get("path_keys", ())` and the registered tool's
   `resource_scope_keys`. When `registry is not None` and `registry.get(tool_name)`
   raises `KeyError` (unregistered tool), return a sentinel (`None`) so the caller fails
   closed. When `registry is None`, return only the configured keys (preserves today's
   behavior).
2. Add a module-level helper `_iter_path_arg_values(args, keys)` that yields each string
   element of the given argument names: a `str` value yields itself (if non-empty); a
   `list` value yields each `str` element; a value that is neither a non-empty `str` nor
   a list of `str` raises `_UnexpectedPathValueType(key, value)` so the caller fails
   closed. This is a NEW helper — do NOT edit the shared `_iter_string_arg_values`.
3. Thread an optional `registry: RuntimeToolRegistry | None = None` parameter into
   `check_preflight` (line 418), pass it to `check_allowed_root`; into
   `check_allowed_root` (line 380); and into `_escalate_for_path` (line 246). Keep the
   default `None` on every signature so all existing callers and tests stay valid.
4. In `check_allowed_root`: resolve the union keys via `_resolve_checked_path_keys` (new); on
   the `None` sentinel return `False` (fail closed); iterate `_iter_path_arg_values` (new) and
   resolve each value against `allowed_root`, returning `False` on the first out-of-root
   value (denial codes unchanged).
5. In `_escalate_for_path`: resolve the union keys and iterate `_iter_path_arg_values` (new)
   the same way, failing closed on the sentinel and on `_UnexpectedPathValueType` (new).
6. Leave `classify_risk`'s existing `registry` threading to `_escalate_for_path`
   (line 373) intact — it already passes the registry, so the escalation chain now checks
   declared keys too.

### Method
- Every new parameter is optional with default `None`, matching `classify_risk`'s
  convention; the `RuntimeToolRegistry` annotation resolves via the existing
  `TYPE_CHECKING` import (line 34-35) plus `from __future__ import annotations` (line 9),
  so no runtime import is added.
- Union resolution reads `RuntimeTool.resource_scope_keys` (a required schema-2.0 field,
  populated at discovery via `build_runtime_tool`); `registry.get()` raising `KeyError`
  is the fail-closed signal for an unregistered tool.
- List handling lives entirely in the new `_iter_path_arg_values` (new); the shared
  `_iter_string_arg_values` is untouched, so `_escalate_for_github_branch` is unchanged.

### Details
```python
class _UnexpectedPathValueType (new)(Exception):
    """Raised when a path argument value is neither str nor list[str]."""


def _resolve_checked_path_keys (new)(
    tool_name: str,
    cfg: AgentConfig,
    registry: RuntimeToolRegistry | None = None,
) -> list[str] | None:
    """Sorted unique path-key names to check, or None when the tool is unregistered."""
    declared: tuple[str, ...] = ()
    if registry is not None:
        tool = registry.get(tool_name)  # KeyError -> unregistered -> caller fails closed
        declared = tuple(getattr(tool, "resource_scope_keys", ()) or ())
    configured = cfg.approval.approval_resource_keys.get("path_keys", ())
    return sorted(set(declared) | set(configured))


def _iter_path_arg_values (new)(args: dict[str, Any], keys: list[str]):
    for key in keys:
        value = args.get(key)
        if isinstance(value, str):
            if value:
                yield value
        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, str) or not item:
                    raise _UnexpectedPathValueType (new)(key, value)
                yield item
        else:
            raise _UnexpectedPathValueType (new)(key, value)
```
- `check_preflight` gains `registry: RuntimeToolRegistry | None = None` and calls
  `check_allowed_root(cfg, tool_name, args, registry)`.
- `check_allowed_root(cfg, tool_name, args, registry: RuntimeToolRegistry | None = None)`:
  ```python
  keys = _resolve_checked_path_keys(tool_name, cfg, registry)
  if keys is None:
      return False  # unregistered tool -> fail closed
  for val in _iter_path_arg_values(args, keys):
      try:
          resolved = Path(val).resolve()
      except (ValueError, OSError):
          return False
      if not resolved.is_relative_to(root):
          return False
  return True
  ```
- `_escalate_for_path(cfg, base, args, registry: RuntimeToolRegistry | None = None)`:
  same union + `_iter_path_arg_values` (new) handling as `check_allowed_root`.

## Compatibility considerations
- Additive optional parameters on `check_preflight`, `check_allowed_root`,
  `_escalate_for_path`: existing callers that omit `registry` keep configured-key
  behavior exactly. No public-contract change for callers that do not pass a registry.
- The `RuntimeToolRegistry` type annotation resolves under `TYPE_CHECKING` +
  `from __future__ import annotations`; no new runtime import.
- New module-level names (`_UnexpectedPathValueType` (new), `_resolve_checked_path_keys` (new),
  `_iter_path_arg_values` (new)) are private and additive.

## Security considerations
- Fail closed on an unregistered tool (`KeyError` from `registry.get()` → deny) and on a
  path argument whose value is neither `str` nor `list[str]` (A6). Never fail open.
- Declared `resource_scope_keys` now reach the preflight and escalation, closing the
  defense-in-depth gap for list-valued (`read_multiple_files.paths`) and differently-named
  (`git.repo_path`) path arguments. Denial codes are unchanged.

## Rollback considerations
- Single-module change; revert the commit.

## Validation plan
- Unit: `uv run pytest tests/agent/test_tool_policy.py` — all green, including the new
  list-valued (`paths=[inside, outside]` → denied; all inside → allowed) and
  `repo_path=outside` → denied cases, and the unknown-tool fails-closed case.
- Static: `uv run ruff`, `uv run mypy --no-namespace-packages`, `uv run bandit` on
  `scripts/agent/tool_policy.py` and `tests/agent/test_tool_policy.py` — clean; no new
  findings beyond the 3 pre-existing High ones (unchanged from HEAD).
- Scope guard: `git diff --stat` shows no change outside `scripts/agent/tool_policy.py`
  and its companion test; the shared `_iter_string_arg_values` body is byte-identical.

## Completion criteria
- A call whose declared (`resource_scope_keys`) or configured (`path_keys`) path argument
  is a list containing a path outside `allowed_root` is denied; a list with all elements
  inside is allowed; a git tool whose `repo_path` is outside `allowed_root` is denied; an
  unknown tool name fails closed; the five configured keys behave as before; the existing
  suite still passes.

## Out of Scope
- Shell command path handling (`shellprefix001`, `shellrisk001`).
- Changing which risk tiers skip protected-path escalation (`classify_risk` early return
  for `READ_ONLY`/`WRITE_SAFE` is unchanged).
- Modifying the shared `_iter_string_arg_values` (feeds branch escalation).
- Resolving relative paths against the server working directory instead of the agent's.
- Adding a registry lookup that fails open for an unknown tool.
- Any change to server-side enforcement (`FileAuthorizationError`, `allowed_repo_paths`,
  `read_single_file` jail).

## Adversarial review findings & deviations from procedure

Adversarial review against current `scripts/agent/tool_policy.py` found the procedure
incomplete and mistaken in five ways. All were corrected during implementation; none
changed the Goal. The frozen plan's Problem + Implementation Intent require call-site
wiring, which the Procedure body omitted — the user approved adding the three call-site
files to the frozen Target Files table.

1. **Step 6 is factually wrong.** It states `classify_risk`'s call to `_escalate_for_path`
   (line 373) "already passes the registry". Current line 373 is
   `_escalate_for_path(cfg, base, args)` — no registry threaded. Because the Goal names
   `_escalate_for_path` and REQ-003 requires the registry there, added a `tool_name` +
   `registry` parameter to `_escalate_for_path` and threaded both from `classify_risk`.
2. **Call-site wiring omitted.** The Procedure never instructs updating the three
   `check_preflight` call sites (`tool_approval.py:168`, `repository_gateway.py:102`,
   `tool_runner.py:223`). Without passing `ctx.services_required.runtime_tools`, the
   registry stays `None` at runtime and declared keys are never checked (a dead feature).
   Added the wiring at all three sites and added the three files as rows in the frozen
   Target Files table.
3. **`_resolve_checked_path_keys` did not catch `KeyError`.** The procedure documents a
   `None` sentinel for an unregistered tool ("caller fails closed"), but the code let
   `KeyError` propagate unhandled out of `check_allowed_root`/`_escalate_for_path`. Caught
   `KeyError` and returned `None` so the caller's fail-closed branch runs.
4. **`_iter_path_arg_values` raised on absent keys.** Iterating configured keys and raising
   on any non-str/non-list value denies every call when a configured key a tool does not
   supply is present in `path_keys` (value `None`). Restored the prior skip-absent-key
   behavior (`if key not in args: continue`); only a *present* wrong-typed value raises.
5. **`tool_audit.py` `except Exception` (BLE001).** The procedure's `_extract_resource_scope`
   used a blind `except Exception`, flagged by ruff. Narrowed to `(KeyError, TypeError)`
   (the realistic registry-failure modes); the audit stays best-effort and never raises.

Test deviation: the companion-test prose says an unregistered tool "still applies the
configured keys"; REQ-003 says an unknown tool "fails closed". Followed REQ-003 (deny),
which the fail-closed unit test asserts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261103 | 20261103 | See deviations above (Steps 1-4 of procedure corrected) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261103 | 20261103 | Added `TestDeclaredScopeKeys` (8 tests) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103 | 20261103 | ruff/ruff-format/mypy/bandit clean; 302 tool_policy tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103 | 20261103 | Frozen Target Files table amended with 3 call-site rows |

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
- **Requirement ID**: `REQ-001` (union of declared `resource_scope_keys` and configured `path_keys`), `REQ-002` (check every string element of a list-valued path arg; fail closed on unexpected type), `REQ-003` (optional `RuntimeToolRegistry` threaded in; unknown tool fails closed)
- **Source issue**: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-155552_pathkeys001_path-checks-skip-lists.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-154504
- **Related target files**: `scripts/agent/tool_policy.py`, `tests/agent/test_tool_policy.py`

### Companion test files
- `tests/agent/test_tool_policy.py`
  - Procedure: add regression tests with a stub `RuntimeToolRegistry` declaring the scope
    keys — `check_preflight`/`check_allowed_root` deny `read_multiple_files(paths=[inside,
    outside])` and allow `read_multiple_files(paths=[inside, inside])`; a git tool with
    `repo_path=outside` is denied; a list whose element is not a string fails closed; an
    unregistered tool name still applies the configured keys and does not fail open; the
    five configured keys behave as before. Build the stub registry the same way existing
    `TestPrefixCollision` and path/repo tests build `AgentConfig` via `_cfg(...)` and
    import `RuntimeToolRegistry`. (`REQ-005`; AC-1, AC-2, AC-3, AC-4)
  - Validation: `uv run pytest tests/agent/test_tool_policy.py` — new tests fail on
    current code and pass after the change; the whole existing suite still passes.
