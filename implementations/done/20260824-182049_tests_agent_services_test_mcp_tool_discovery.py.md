## Goal

Fix `tests/agent/services/test_mcp_tool_discovery.py::_make_ctx()` so it explicitly
sets `ctx.cfg.tool.tool_definitions_strict` (default `False`), eliminating a
`MagicMock`-truthiness bug that silently runs every test built via the helper in
strict mode, fixing the 2 currently-failing tests in
`TestDiscoverAllUnreachableServers`. No production code change.

## Scope

- In scope: `tests/agent/services/test_mcp_tool_discovery.py::_make_ctx()` — add
  explicit `tool_definitions_strict` handling.
- Out of scope: `scripts/agent/services/mcp_tool_discovery.py` (no production defect;
  `_is_strict()`/`_is_fatal_severity()` behave correctly given a properly-configured
  context); all other items from the parent QA-review requirement (already resolved by
  sibling requirements/plans, or explicitly out of scope — GitHub MCP coverage,
  unconfirmed `schema_version` claim).

## Assumptions

- Root cause confirmed this cycle: `_is_strict()`
  (`scripts/agent/services/mcp_tool_discovery.py:369-371`) is
  `return bool(getattr(self._ctx.cfg.tool, "tool_definitions_strict", False))`. Since
  `_make_ctx()` builds `ctx = MagicMock()` without setting
  `ctx.cfg.tool.tool_definitions_strict`, `getattr` never hits its `False` default —
  `MagicMock` auto-vivifies `ctx.cfg.tool.tool_definitions_strict` as a truthy
  `MagicMock` attribute instead of raising `AttributeError`.
- Confirmed by running `uv run pytest tests/agent/services/test_mcp_tool_discovery.py
  -v` this cycle: exactly 2 failures
  (`test_invalid_json_body_marks_server_unreachable`,
  `test_non_200_status_marks_server_unreachable`), both failing on
  `assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)` with
  captured log line `"Strict mode: all MCP servers unreachable — cannot validate tool
  definitions."` — confirming strict mode is incorrectly active, matching the plan's
  root-cause claim exactly. 70 tests pass.
- No test in the file currently depends on the accidental `True` default in a way that
  would break once the default becomes explicit `False` — to be reconfirmed by running
  the full file again after the fix (Validation plan below); if one does, that call
  site gets an explicit `tool_definitions_strict=True` argument rather than reverting
  the helper's new default.

## Design decisions

- Add a `tool_definitions_strict: bool = False` parameter to `_make_ctx()` and set
  `ctx.cfg.tool.tool_definitions_strict = tool_definitions_strict` explicitly, matching
  the plan's Design section exactly:
  ```python
  def _make_ctx(
      servers: dict[str, object],
      http: AsyncMock,
      security_profile: SecurityProfile = SecurityProfile.LOCAL,
      tool_definitions_strict: bool = False,
  ) -> MagicMock:
      """Build a minimal mocked AgentContext (mirrors tests/test_repl_health.py's style)."""
      ctx = MagicMock()
      ctx.cfg.mcp.mcp_servers = servers
      ctx.cfg.mcp.security_profile = security_profile
      ctx.cfg.tool.tool_definitions_strict = tool_definitions_strict
      ctx.services_required.http = http
      return ctx
  ```

## Alternatives considered

- Passing `strict=True` explicitly at every existing call site instead of changing the
  helper's default — rejected: the helper's docstring already states it builds a
  "minimal mocked AgentContext," and an explicit, sane default (`False`, matching
  production's default `tool_definitions_strict` behavior) is the correct general fix;
  per-call-site overrides remain available for the (currently unidentified) tests that
  need strict mode.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. Add the `tool_definitions_strict: bool = False` parameter to `_make_ctx()`'s
   signature.
2. Add `ctx.cfg.tool.tool_definitions_strict = tool_definitions_strict` inside the
   function body.
3. Scan the file's other test classes for any that assert `FATAL`-severity behavior
   without passing `security_profile=SecurityProfile.PRODUCTION` — if found, that call
   site may have been silently relying on the old accidental strict=True default; add
   `tool_definitions_strict=True` explicitly there instead of reverting the new
   default.
4. Re-run the full file to confirm both previously-failing tests now pass and no
   other test regresses.

### Method

Direct text edit to the existing helper function; no new imports required
(`MagicMock`, `AsyncMock`, `SecurityProfile` are already imported in this file).

### Details

Current `_make_ctx()` (verified this cycle, lines 65-75):
```python
def _make_ctx(
    servers: dict[str, object],
    http: AsyncMock,
    security_profile: SecurityProfile = SecurityProfile.LOCAL,
) -> MagicMock:
    """Build a minimal mocked AgentContext (mirrors tests/test_repl_health.py's style)."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.cfg.mcp.security_profile = security_profile
    ctx.services_required.http = http
    return ctx
```
The two failing tests (`test_non_200_status_marks_server_unreachable` at line 570,
`test_invalid_json_body_marks_server_unreachable` at line 587) call `_make_ctx()`
without a `tool_definitions_strict` argument, so they automatically pick up the new
`False` default once added.

## Compatibility considerations

Test-only change. `_make_ctx()`'s call signature gains one new optional keyword
parameter with a default — existing call sites without the new argument are
unaffected in count (their behavior only changes because the accidental `True`
truthiness is replaced with an explicit `False`, which is the intended fix).

## Security considerations

N/A: test-only fixture change, no production code, no external input.

## Rollback considerations

Revert `_make_ctx()` to its previous body; no other rollback steps required (no
production code touched).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_mcp_tool_discovery.py` | Unit | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | 0 failures (72 pass, incl. the 2 previously-failing tests) |
| Full suite | Regression | `uv run pytest tests/ -q` | No new failures vs. current baseline |
| Modified file | Static | `uv run ruff check tests/agent/services/test_mcp_tool_discovery.py` + `uv run mypy tests/agent/services/test_mcp_tool_discovery.py` | Clean |

## Out of scope

`scripts/agent/services/mcp_tool_discovery.py`; GitHub MCP coverage; the unconfirmed
`schema_version` claim from the parent QA-review requirement.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture fix, no new test cases added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/done/20260726-122527_require.md`
- **Source plan**: `plans/20260823-194536_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-182049
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`

## Adversarial verification notes (this cycle)

- **Plan correction applied**: the plan's own Traceability section recorded
  `Source requirement: requires/20260726-122527_require.md`, but that file only exists
  at `requires/done/20260726-122527_require.md` (confirmed via file-existence check;
  the plan's own Out-of-Scope bullet correctly used the `requires/done/` path, so the
  Traceability section was simply inconsistent with the rest of the same document).
  Corrected `plans/20260823-194536_plan.md`'s Traceability section in place to
  `requires/done/20260726-122527_require.md`, and carried the corrected path forward
  into this document's own Traceability section.
- Re-ran `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` against
  current source: confirmed exactly 2 failures with the exact names and failure mode
  the plan describes (70 passed, 2 failed), and confirmed `_is_strict()`'s
  implementation matches the plan's root-cause description exactly.
- Confirmed via `grep -rl "20260823-194536_plan" implementations/
  implementations/done/` that no existing implementation procedure document already
  covers this plan/target pair. No other blocking unknowns or contradictions found.
