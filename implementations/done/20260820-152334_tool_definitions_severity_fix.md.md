# Implementation Procedure: Resolve tool_definitions FATAL/WARNING severity contradiction between docs and implementation

## Goal
Make the documented severity behavior of `tool_definitions` startup findings in `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` consistent with the actual behavior implemented in `scripts/agent/services/mcp_tool_discovery.py`, and lock that behavior down with tests across the full `(strict, security_profile)` matrix.

## Goal
Make the documented severity behavior of `tool_definitions` startup findings in `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` consistent with the actual behavior implemented in `scripts/agent/services/mcp_tool_discovery.py`, and lock that behavior down with tests across the full `(strict, security_profile)` matrix.

## Scope
- Target files:
  - `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` - Update the `tool_definitions` bullet
  - `tests/agent/services/test_mcp_tool_discovery.py` - Add parametrized tests
  - `scripts/agent/services/mcp_tool_discovery.py` - Verify docstring consistency (no code change needed)

## Assumptions
- The module docstring in `mcp_tool_discovery.py` (lines 33-35) correctly describes the intended behavior: unified severity scheme including `tool_definitions`
- The doc at line 63 is stale documentation that predates the unified scheme refactor
- No change to `scripts/agent/startup.py` needed — it already treats all `mcp_tool_discovery` findings uniformly

## Design decisions
- **Option B chosen**: Implementation is correct; doc must be updated (Option A rejected)
- Rationale: Module docstring explicitly includes `tool_definitions` in unified scheme; `_check_tool_definitions_finding()` docstring describes current behavior as a bug fix for an "old quirk"; reverting to "never FATAL" would re-introduce the bug the code was written to fix
- Update doc bullet at line 63 to match unified scheme wording
- Add parametrized tests covering full `(strict, security_profile)` matrix for both `has_issues` and `except RuntimeError` branches

## Implementation steps

### Phase 1 — Documentation correction
1. In `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, replace line-63 bullet:
   ```markdown
   - `tool_definitions` は strict モードでも FATAL にはならない — 常に WARNING にダウングレードされる。
   ```
   with:
   ```markdown
   - `tool_definitions` は統一された重大度スキームに従う: strict モードまたは security_profile=PRODUCTION のとき FATAL、それ以外は WARNING。
   ```
2. No code change to `scripts/agent/services/mcp_tool_discovery.py` required — verify docstring matches new wording

### Phase 2 — Test coverage
1. Add parametrized test `TestUnifiedSeverity.test_severity_unified_for_tool_definitions_has_issues` mirroring `test_severity_unified_for_duplicates` (line 1368):
   - Parameters: `(False, LOCAL) -> WARNING`, `(False, PRODUCTION) -> FATAL`, `(True, LOCAL) -> FATAL`, `(True, PRODUCTION) -> FATAL`
   - Drive `_check_tool_definitions` via monkeypatch returning `has_issues=True`

2. Extend `test_tool_definitions_check_surfaces_as_outcome_not_exception` (line 1428) into parametrized variant covering same `(strict, profile)` matrix for `except RuntimeError` branch, reusing existing `RuntimeError("boom")` side effect

3. Verify existing tests unchanged: `test_malformed_capabilities_produces_warning_not_fatal`, `TestDriftFindings`, duplicate tests

### Phase 3 — Verification
- Run `pytest tests/agent/services/test_mcp_tool_discovery.py -q` — all tests pass
- Run full lint/type/test gate per `rules/toolchain.md`
- Manual doc review: `rg "tool_definitions" docs/05_agent_10_01*.md scripts/agent/services/mcp_tool_discovery.py` — doc bullet and module docstring describe same condition

## Validation plan
- `pytest tests/agent/services/test_mcp_tool_discovery.py -q` — all 4 `(strict, profile)` combinations assert correct status for `tool_definitions` in both `has_issues` and `RuntimeError` branches
- Manual doc review: `rg "tool_definitions" docs/05_agent_10_01*.md scripts/agent/services/mcp_tool_discovery.py` — doc bullet and module docstring describe same condition
- Full suite `pytest` — no regressions

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-224947_require.md
- Source plan: plans/20260819-184236_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-152334
- Related target files: scripts/agent/services/mcp_tool_discovery.py, docs/05_agent_10_01_operations-and-observability-startup-and-health.md, tests/agent/services/test_mcp_tool_discovery.py, scripts/agent/startup.py