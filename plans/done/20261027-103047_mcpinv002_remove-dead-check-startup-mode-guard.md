# Plan: Remove dead `ToolExecutor._check_startup_mode` guard

## Goal
- Delete the never-called `ToolExecutor._check_startup_mode` method and its leftover
  references, making the live disabled-server guards in `ToolTransportInvoker` the single
  source of truth, and correct the two documentation claims that point at the dead method's
  location.

## Priority
Low

## Scope
- **In-Scope**:
  - Delete `_check_startup_mode` from `ToolExecutor` (`scripts/shared/tool_executor.py`).
  - Remove the leftover references the method alone justified: the `StartupMode` import in
    `tool_executor.py` and the redundant `self._server_configs = server_configs` assignment in
    `ToolExecutor.__init__` (the parent `ToolTransportInvoker.__init__` already assigns the
    same attribute from the same argument).
  - Correct stale guard-location claims in `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
    and `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`.
- **Out-of-Scope**:
  - Any change to the disabled-server policy or the live guard locations in
    `ToolTransportInvoker` / `mcp_config` (Issue constraint: "Must not touch
    `ToolTransportInvoker` or `mcp_config`").
  - Refactoring `ToolTransportInvoker`.
  - Test changes: no test references `_check_startup_mode` (verified), so none require
    modification.
- **Dependencies**: N/A: none. (Overlap notes: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
  is also a target of the mcpinv001 Plan — Compatible: mcpinv001 edits the "Idempotency and
  retry" section, this Plan edits the `ToolExecutor.server_configs` note; disjoint sections.
  `scripts/shared/tool_executor.py` is also a target of the mcpinv004 Plan — Compatible: that
  Plan edits only the `concurrency_limits` parameter docstring in `__init__`, this Plan deletes
  `_check_startup_mode`, the `StartupMode` import, and the redundant `_server_configs`
  assignment; disjoint regions, and whichever Plan implements second rebases on the first.)

## Background
- `ToolExecutor._check_startup_mode` (defined in `scripts/shared/tool_executor.py`) returns an
  error `ToolCallResult` for a `startup_mode == StartupMode.NONE` server. A repository-wide
  search (`scripts/`, `tests/`, `docs/`, `tools/`, `config/`, `deploy/`) finds only its own
  definition — zero call sites.
- Live guards verified: `ToolTransportInvoker._run_precall_gates()` rejects disabled servers at
  the shared invocation boundary (its REQ-004 block: `cfg.startup_mode == StartupMode.NONE` →
  error result), and `ToolTransportInvoker.__init__` skips building a transport when
  `cfg.is_disabled`. `ToolExecutor` inherits both because it subclasses `ToolTransportInvoker`
  and its `execute()` delegates to `_run_precall_gates()`.

## Problem
- A defensive-looking guard that never runs creates a false sense of defense-in-depth. The
  problem is already realized in the docs: `mcp_06_02` states disabled rejection happens "by
  the `ToolExecutor` startup mode check", and `mcp_03_01` documents `self._server_configs.get(...)`
  in `tool_executor.py` as a live "startup-mode check" location. After this Plan, both claims
  name the real guard location.

## Reason for Change
- The Issue (python-code-review generated) flags misleading dead code. Deletion removes the
  maintainer trap and the docs' misattribution at the same time.

## Implementation Intent
- Fresh `rg` re-check immediately before deletion (Issue's unresolved question: confirm no
  external plugin or generated test references the symbol), then a pure deletion in
  `tool_executor.py` plus two small documentation corrections. No behavior change.

## Requirements
- `REQ-001`: Delete the `_check_startup_mode` method definition from `ToolExecutor` in
  `scripts/shared/tool_executor.py`.
- `REQ-002`: Remove the `StartupMode` entry from the `shared.mcp_config` import block in the
  same file — its only use was inside the deleted method, and an unused import would fail
  `ruff` (F401).
- `REQ-003`: Remove the redundant `self._server_configs = server_configs` assignment in
  `ToolExecutor.__init__` — it existed to feed the deleted method; the parent
  `ToolTransportInvoker.__init__` assigns the identical attribute from the identical argument
  (verified: parent stores `self._server_configs` and uses it in `_run_precall_gates` and the
  concurrency-limit block; the attribute remains available to tests that assign
  `executor._server_configs` directly).
- `REQ-004`: Correct the two stale documentation claims so they name the live guard: the
  `startup_mode="none"` behavior note in `mcp_06_02` and the `ToolExecutor.server_configs`
  note in `mcp_03_01` must attribute disabled-server rejection to
  `ToolTransportInvoker._run_precall_gates()` (inherited boundary), not to a `ToolExecutor`
  check.
- `REQ-005`: Runtime behavior is unchanged: `ToolTransportInvoker` and `mcp_config` are not
  touched, and disabled servers remain rejected at the invocation boundary.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/tool_executor.py | Delete the dead method, the unused `StartupMode` import, and the redundant `_server_configs` assignment | The Issue's single source file; leftover references must not survive the deletion | REQ-001, REQ-002, REQ-003, REQ-005 | `ToolExecutor._check_startup_mode` exists with zero call sites repo-wide; `ToolTransportInvoker.__init__` already assigns `self._server_configs` | tests/shared/test_tool_executor.py (`test_invoke_rejects_disabled_server`), tests/shared/test_tool_executor_order.py, tests/shared/test_tool_executor_routing.py, tests/shared/test_tool_transport_invoker.py — all pass unmodified | Verified |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Correct the `startup_mode="none"` rejection-location sentence | Current text attributes rejection to "the `ToolExecutor` startup mode check" — the dead method; becomes actively false after deletion | REQ-004 | "`...rejected with a \"disabled (startup_mode=none)\" error by the `ToolExecutor` startup mode check...`" sentence in the `startup_mode="none"` entry | N/A: documentation file | Verified |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Correct the `ToolExecutor.server_configs` note so it no longer presents `self._server_configs.get(...)` in `tool_executor.py` as a startup-mode-check location | That code reference disappears with the method; the live `get()` call lives in `ToolTransportInvoker` | REQ-004 | "Not to be confused with `ToolExecutor.server_configs`" paragraph citing `self._server_configs.get(server_key)` in `shared/tool_executor.py` | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/tool_transport_invoker.py | Live guards that must remain untouched: `__init__` transport-skip (`cfg.is_disabled`) and the REQ-004 `StartupMode.NONE` rejection in `_run_precall_gates()`; also proves the inherited `self._server_configs` attribute | scripts/shared/tool_executor.py; REQ-003, REQ-005 |
| scripts/shared/mcp_config.py | `is_disabled` property and `StartupMode` semantics (read-only) | scripts/shared/tool_executor.py; REQ-005 |
| tests/shared/test_tool_executor.py | Contains the disabled-server regression test (`TestDisabledServerRejection`-style test `test_invoke_rejects_disabled_server`) proving the live guard covers the removed behavior | scripts/shared/tool_executor.py; REQ-005 |
| tests/shared/test_tool_executor_order.py | Assigns `executor._server_configs = {}` directly — must keep working via the inherited attribute | scripts/shared/tool_executor.py; REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): `rg -n _check_startup_mode scripts/ tests/ docs/` returns no hits after the
  change (fresh pre-deletion `rg` is Phase 1).
- `AC-2` (REQ-005): `test_invoke_rejects_disabled_server` in
  `tests/shared/test_tool_executor.py` passes unmodified — a `startup_mode=none` server is
  still rejected at the invocation boundary.
- `AC-3` (REQ-005): All `tests/shared/` tool-executor and transport-invoker suites pass with
  no test edits; `ruff` reports no unused-import findings (REQ-002 satisfied).
- `AC-4` (REQ-004): The two documentation sentences name `ToolTransportInvoker._run_precall_gates()`
  as the rejection location; no text still attributes it to a `ToolExecutor` check.

## Tests
- Regression (REQ-005): `uv run pytest tests/shared/` — the executor/invoker suites including
  the disabled-server rejection test and the order test that assigns `_server_configs`.
- Static (REQ-002): `uv run ruff check scripts/` — no F401 in `tool_executor.py`.
- Grep gate (REQ-001): `rg -n _check_startup_mode scripts/ tests/ docs/` → zero hits.

## Documentation Impact
- Required (corrected from the Issue's "None expected"): repository evidence shows two 22_mcp
  docs currently misattribute the disabled-server rejection to the dead `ToolExecutor` method,
  so the task mapping for MCP startup modes / `McpServerConfig` fields
  (`docs/00_index.md` "Document References by Task") applies: the `mcp_06_02` field note and
  the `mcp_03_01` `ToolExecutor.server_configs` note must be corrected. Driven by REQ-004.

## Assumptions
- No external plugin or generated test outside the repository references the symbol; the
  Issue's unresolved question is covered by a fresh `rg` at implementation time (Phase 1)
  before the deletion is applied.
- The redundant `self._server_configs` assignment removal is in-scope as a "reference left
  behind" (Issue Required Changes) because the attribute existed solely to serve the dead
  method and the parent class assigns the identical attribute.
- Overlap with the mcpinv001 Plan on `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` is
  Compatible: disjoint sections ("Idempotency and retry" vs the `ToolExecutor.server_configs`
  note); whichever Plan implements second rebases on the first.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | External/generated references to `_check_startup_mode` outside the searched trees | Cannot inspect anything outside this repository | Phase 1 fresh `rg` gate before deletion, per the Issue's unresolved question | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/tool_executor.py | Deletion of dead method + leftover references (no behavior change) | None at runtime (zero call sites); import block only | 1 | High (single author, all historical authors are the same person) | None: no module added or removed |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Location-attribution sentence fix | Docs domain 22_mcp | 9 | High (single author, 100%) | None |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | `ToolExecutor.server_configs` note fix | Docs domain 22_mcp | 24 (high churn — coordinate with sibling mcpinv plans) | High (single author) | None |

## Design
- Deletion-only change; no new abstraction. The live guard already covers the removed behavior
  via class inheritance (`ToolExecutor` → `ToolTransportInvoker`), so removing the shadow
  guard cannot weaken enforcement: every `ToolExecutor.execute()` call already runs
  `_run_precall_gates()`.
- Keeping the docs honest is part of the fix: the deletion makes two existing doc claims
  actively false, so the Plan carries them as target rows instead of leaving doc drift for a
  later cycle.

## Implementation steps
1. **Phase 1: Pre-deletion verification gate**
   - [ ] Fresh `rg -n _check_startup_mode scripts/ tests/ docs/` confirms the only occurrence
     is the definition (REQ-001; `scripts/shared/tool_executor.py`).
2. **Phase 2: Deletion**
   - [ ] Delete `_check_startup_mode` from `ToolExecutor` (REQ-001;
     `scripts/shared/tool_executor.py`).
   - [ ] Remove the now-unused `StartupMode` import (REQ-002; `scripts/shared/tool_executor.py`).
   - [ ] Remove the redundant `self._server_configs = server_configs` assignment in
     `ToolExecutor.__init__` (REQ-003; `scripts/shared/tool_executor.py`).
3. **Phase 3: Documentation and verification**
   - [ ] Fix the `startup_mode="none"` rejection-location sentence (REQ-004;
     `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`).
   - [ ] Fix the `ToolExecutor.server_configs` note (REQ-004;
     `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`).
   - [ ] Run the full `rules/toolchain.md` validation sequence; deployment/scripts check: no
     new or removed module, so `deploy.sh` and configs are unchanged (REQ-005).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/tool_executor.py | Regression (existing suites, no test edits) | `uv run pytest tests/shared/` then `uv run pytest tests/` | Green; `test_invoke_rejects_disabled_server` unmodified and passing |
| scripts/shared/tool_executor.py | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; no unused-import findings |
| scripts/shared/tool_executor.py | Symbol-absence gate | `rg -n _check_startup_mode scripts/ tests/ docs/` | Zero hits |
| docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Documentation consistency (22_mcp domain) | `rules/toolchain.md` documentation consistency check | Guard location attributed to `ToolTransportInvoker._run_precall_gates()` |

## Risks
- **Risk**: removing `self._server_configs` in `ToolExecutor.__init__` could break a hidden
  reader of the attribute → **Mitigation**: the attribute remains defined by the parent
  `ToolTransportInvoker.__init__` with the identical value; `test_tool_executor_order.py`
  (which assigns it directly) and the full `tests/shared/` suite validate this in Phase 3.
- **Risk**: an external plugin calls the private method → **Mitigation**: Phase 1 `rg` gate is
  a hard precondition; private (underscore) symbols are not part of any documented public API
  (the two docs that mention startup-mode rejection are corrected to name the live guard).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: pre-deletion verification gate | Completed | — | 20261028-111441 |  |
| 2 | Phase 2: deletion | Completed | — | 20261028-111441 |  |
| 3 | Phase 3: documentation and verification | Completed | — | 20261028-111441 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-005859_01_scripts_shared_tool_executor.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-005859_02_docs_22_mcp_mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-005859_03_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-001347_mcpinv002_remove-dead-check-startup-mode-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-103047
- **Related target files**: scripts/shared/tool_executor.py, docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md, docs/22_mcp/mcp_03_01_dispatch-and-routing.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary; zero call sites verified by repository-wide search | scripts/shared/tool_executor.py | Phase 2 | AC-1 | rg symbol-absence gate | Confirmed by repository evidence |
| REQ-002 | Required Changes "Remove any import or reference left behind" | scripts/shared/tool_executor.py | Phase 2 | AC-3 | `ruff check` | Confirmed by repository evidence |
| REQ-003 | Required Changes "Remove any import or reference left behind"; parent assignment evidence | scripts/shared/tool_executor.py | Phase 2 | AC-3 | `tests/shared/` suites incl. `test_tool_executor_order.py` | Confirmed by repository evidence |
| REQ-004 | Verified stale claims in `mcp_06_02` and `mcp_03_01` | docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md | Phase 3 | AC-4 | 22_mcp documentation consistency check | Confirmed by repository evidence |
| REQ-004 | Verified stale claim in `mcp_03_01` `ToolExecutor.server_configs` note | docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Phase 3 | AC-4 | 22_mcp documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Constraints "Must not change runtime behavior"; live-guard verification | scripts/shared/tool_executor.py | Phase 2 | AC-2 | `test_invoke_rejects_disabled_server` unmodified | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-005859 -->