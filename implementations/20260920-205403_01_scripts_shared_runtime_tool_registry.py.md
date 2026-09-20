## Goal
Add a diagnostic warning log inside `RuntimeToolRegistry.apply_policy()` when a
`llm_visibility_base=False` tool's `allowed_tools` membership would otherwise have
enabled it, so REQ-002's Acceptance Criteria ("logs a warning and rejects the invalid
visibility change") is met — no change to the existing, already-correct enforcement
logic itself.

## Scope
In scope: add a module-level `logger = logging.getLogger(__name__)` and one
`logger.warning(...)` call inside `apply_policy()`'s existing loop body.
Out of scope: any change to `apply_policy()`'s tier/allowlist computation,
`RuntimeTool`'s field shape, or `build_runtime_tool()`'s defaulting rules (REQ-002 of
`plans/20260920-203022_plan.md`; see Plan's own Scope > Out-of-Scope).

## Assumptions
- CPython's GIL makes the existing `self._tools = new_tools` swap atomic; unrelated to
  this file's own change here (documented for `runtime_tool_registry.py` in the
  sibling Plan `plans/20260920-203342_plan.md`, not re-litigated in this document).
- `rules/coding.md`'s Logging convention (module-level `logger =
  logging.getLogger(__name__)`, English-only log messages) applies verbatim — no
  project-specific logging wrapper exists in `scripts/shared/` that this file should
  use instead (confirmed: no other `scripts/shared/*.py` file imports a custom logging
  wrapper; `logging.getLogger(__name__)` is the standard pattern used elsewhere in
  `scripts/shared/`).

## Design decisions
- Place the warning check inside `apply_policy()`'s existing loop, immediately after
  `new_enabled` is computed, rather than at the `_sync_services()` call site
  (`scripts/agent/services/config_reload.py`) — this is the single place where both
  `resolved_llm_visibility_base` and the `allowed_tools`-alone result are already
  available without recomputing anything.
- Gate the log on `not resolved_llm_visibility_base and (not allowed_tools or name in
  allowed_tools)` — i.e., log only when the tool is hidden AND would otherwise have
  been allowed by `allowed_tools`. This keeps the log rare (only fires for a tool an
  operator's config specifically, if mistakenly, tries to re-enable), per the Plan's
  Risks section rationale.

## Alternatives considered
- Raising an exception instead of logging: rejected — the Plan's Assumptions section
  treats the Issue's own Acceptance Criteria text ("logs a warning and rejects") as
  authoritative over its separately-listed, unresolved "raise an exception or log a
  warning?" question (Unknowns UNK-01 in `plans/20260920-203022_plan.md`); logging is
  the additive, lower-risk choice that does not change `apply_policy()`'s existing
  no-exception contract for any caller.
- Logging at the `_sync_services()` call site instead of inside `apply_policy()`:
  rejected — would require exposing the internal `resolved_llm_visibility_base`
  computation outside the method, duplicating logic that already exists in one place.

## Implementation
### Target file
`scripts/shared/runtime_tool_registry.py`

### Procedure
1. Add `import logging` to the module's import block (after `from __future__ import
   annotations`, before the `dataclasses` import, per `rules/coding.md` Import order —
   stdlib imports before third-party/local).
2. Add a module-level `logger = logging.getLogger(__name__)` declaration after the
   existing imports, before the `class RuntimeToolRegistry:` definition.
3. Inside `apply_policy()`'s `for name, tool in list(self._tools.items()):` loop, after
   the existing `new_enabled = resolved_llm_visibility_base and (...)` computation,
   add a conditional `logger.warning(...)` call that fires when
   `not resolved_llm_visibility_base and (not allowed_tools or name in
   allowed_tools)` — i.e., the tool would have been enabled by `allowed_tools` alone
   but `llm_visibility_base` forces it to stay hidden. Include the tool `name` in the
   message.

### Method
Direct file edit (`Edit` tool) — two small additions to an existing, already-correct
method body; no new function, class, or public API surface.

### Details
Current `apply_policy()` body (confirmed via Read, lines 150-175):
```python
def apply_policy(
    self,
    tier_map: Mapping[str, AgentSafetyTier],
    allowed_tools: Sequence[str] = (),
) -> None:
    """Apply a tier/allowlist policy to all registered tools, in place.
    ...
    """
    new_tools: dict[str, RuntimeTool] = {}
    for name, tool in list(self._tools.items()):
        tier = tier_map.get(name, tool.agent_safety_tier)
        resolved_llm_visibility_base = _or_default(tool.llm_visibility_base, True)
        new_enabled = resolved_llm_visibility_base and (
            not allowed_tools or name in allowed_tools
        )
        new_tools[name] = dataclasses.replace(
            tool,
            agent_safety_tier=tier,
            enabled_for_llm=new_enabled,
        )
    self._tools = new_tools
```

Target shape after this change (illustrative signature/structure only, not final
prose — write the actual code during implementation):
```python
import logging
...
logger = logging.getLogger(__name__)


class RuntimeToolRegistry:
    ...
    def apply_policy(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """..."""
        new_tools: dict[str, RuntimeTool] = {}
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            resolved_llm_visibility_base = _or_default(tool.llm_visibility_base, True)
            allowed_alone = not allowed_tools or name in allowed_tools
            if not resolved_llm_visibility_base and allowed_alone:
                logger.warning(
                    "tool %r hidden at discovery (llm_visibility_base=False);"
                    " reload's allowed_tools would otherwise have re-enabled it",
                    name,
                )
            new_enabled = resolved_llm_visibility_base and allowed_alone
            new_tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                enabled_for_llm=new_enabled,
            )
        self._tools = new_tools
```
No signature change; `new_enabled`'s computed value is unchanged (only refactored to
reuse `allowed_alone` to avoid duplicating the `not allowed_tools or name in
allowed_tools` expression for the log condition).

## Compatibility considerations
No public API change — `apply_policy()`'s signature, return type (`None`), and
existing enabled/disabled outcomes for every tool are unchanged. The only new
observable effect is a log line at `WARNING` level in the process's configured
logging output, which no existing caller inspects programmatically (confirmed:
`rg -l "apply_policy"` shows no caller captures log output for assertions except via
`caplog` in tests, which is exactly what this Plan's companion test,
`tests/shared/test_runtime_tool_registry.py`, Row 2, is written to check).

## Security considerations
This change is itself a security-observability improvement (making a rejected,
potentially-malicious or misconfigured visibility override visible in logs) with no
new attack surface: no new input is parsed, no new external call is made, and the log
message includes only the tool `name` (already-known, non-secret data already present
in `RuntimeTool.name`).

## Rollback considerations
Trivially revertable: removing the `import logging` line, the module-level `logger`
declaration, and the new conditional block restores the exact prior behavior with no
data migration or state cleanup needed, since `apply_policy()` remains a pure
in-memory transformation with no persisted side effect from the log call itself.

## Validation plan
- `uv run ruff check scripts/shared/runtime_tool_registry.py` — confirm the new
  `import logging` is used (no unused-import finding) and import ordering is correct.
- `uv run mypy scripts/shared/runtime_tool_registry.py` — confirm no new type error.
- `uv run pytest tests/shared/test_runtime_tool_registry.py -v` — the companion test
  document (`implementations/20260920-205403_02_tests_shared_test_runtime_tool_registry.py.md`,
  generated from the same Plan's Row 2) adds the `caplog`-based assertions this row's
  change is written to satisfy; this row's own validation confirms the source change
  compiles/lints/type-checks cleanly and does not regress any currently-passing test
  in this file (`uv run pytest tests/shared/test_runtime_tool_registry.py -v` run once
  after both this row and Row 2 are implemented, per the Plan's own Tests section).
- `uv run pytest tests/agent/services/test_config_reload.py -v` — regression check per
  the Plan's Tests section (confirms the new logger call does not break
  `TestRuntimeToolPolicyReapplication`'s mocked-registry tests).

## Completion criteria
- `apply_policy()` contains the new `logger.warning(...)` call, gated exactly on "tool
  hidden by `llm_visibility_base=False` AND would otherwise be allowed by
  `allowed_tools`".
- `enabled_for_llm`'s computed value for every tool is byte-for-byte unchanged from
  before this edit (verified by the full existing test suite in
  `tests/shared/test_runtime_tool_registry.py` still passing with no modification to
  any pre-existing test).
- `uv run ruff check` / `uv run mypy` pass clean on this file.

## Out of scope
- Writing the new tests themselves — covered by this Plan's Row 2
  (`tests/shared/test_runtime_tool_registry.py`, a separate implementation procedure
  document).
- Updating `docs/00_governance_03_issue-and-uncertainty-management.md` — covered by
  this Plan's Row 3, a separate implementation procedure document.
- Any change to `scripts/agent/services/config_reload.py` or any other caller of
  `apply_policy()` — none is required; this change is fully internal to
  `RuntimeToolRegistry.apply_policy()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `import logging`, module-level `logger`, and the warning-log call inside `apply_policy()` | Completed | 20260920-210758 | 20260920-210758 |  |
| 2 | Run `ruff check` / `mypy` on this file | Completed | 20260920-210758 | 20260920-210758 |  |
| 3 | Run `tests/shared/test_runtime_tool_registry.py` and `tests/agent/services/test_config_reload.py` (full validation, after Row 2's tests also land) | Completed | 20260920-210854 | 20260920-210854 | Existing 28 tests in tests/shared/test_runtime_tool_registry.py all pass; new caplog-based tests land in Row 2's cycle |

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
- **Requirement ID**: REQ-002 (add warning log for rejected visibility override)
- **Source issue**: issues/20260920-190713_req001_enforce-immutability-of-llm_visibility_base-during-config-reload.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203022_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-205403
- **Related target files**: scripts/shared/runtime_tool_registry.py