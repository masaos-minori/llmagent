# Plan: Bounded default per-server concurrency cap in `ToolTransportInvoker`

## Goal
- Apply a named, process-wide default concurrency ceiling to every configured MCP server that has
  no explicit positive `tool_concurrency_limits` entry, so the invocation path always has
  backpressure, while preserving the documented "explicit 0/negative = unlimited" opt-out and the
  existing behavior of configured positive limits.

## Priority
Low

## Scope
- **In-Scope**:
  - A module-level named constant `DEFAULT_PER_SERVER_CONCURRENCY = 8` in
    `scripts/shared/tool_transport_invoker.py`.
  - `_ensure_semaphores()` restructured to build a semaphore for every key in
    `self._server_configs`: configured positive value wins, an omitted key gets the default, a
    configured `0`/negative value stays unlimited (no semaphore entry) with the existing
    once-per-process warning.
  - Docstring updates: `_ensure_semaphores()`, `ToolTransportInvoker.__init__`, and the
    `concurrency_limits` parameter note in `ToolExecutor.__init__`.
  - Unit tests for the default cap, the positive-limit override, and the 0/negative opt-out.
  - Documentation updates in the two agent docs that describe the limits map.
- **Out-of-Scope**:
  - Restructuring the pre-call gate chain (carried from the Issue).
  - A global cross-server cap (carried from the Issue; the Issue's own constraint prefers
    per-server semaphores under the shared `httpx.AsyncClient`).
  - New configuration keys: `config/*.toml`, `scripts/agent/config_dataclasses.py`, and
    `scripts/agent/config_section_builders.py` are not touched. The existing
    `tool_concurrency_limits` map remains the tuning surface (Scope decision, see Design).
  - Adding a `default_concurrency` constructor parameter (rejected — see Design).
  - Changing which servers receive a semaphore beyond the default (carried from the Issue).
- **Dependencies**: N/A: none. Overlap notes:
  - `scripts/shared/tool_executor.py` is also a target of the mcpinv002 Plan (dead-guard
    deletion). Compatible: mcpinv002 deletes `_check_startup_mode`, the `StartupMode` import, and
    the redundant `_server_configs` assignment; this Plan edits only the `concurrency_limits`
    parameter docstring in `__init__`. Whichever Plan lands second rebases.
  - `scripts/shared/tool_transport_invoker.py` is a Reference File (not a target) in the mcpinv001
    and mcpinv002 Plans; no write conflict.

## Background
- `ToolTransportInvoker.__init__` stores `concurrency_limits` (`dict(concurrency_limits or {})`)
  and leaves `self._semaphores` as `None` until `_ensure_semaphores()` runs lazily from
  `_run_precall_gates()`. That method currently builds semaphores only for positive entries
  present in the map (`if self._semaphores is None and self._concurrency_limits:` guard, then a
  comprehension over `self._concurrency_limits.items()` with `if n > 0`).
- `_run_precall_gates()` resolves `sem = (self._semaphores or {}).get(server_key)` and passes it
  to `_invoke_and_record`, which wraps the call in `_maybe_semaphore(sem)`; a `None` semaphore
  yields `contextlib.nullcontext()`, i.e. no limit.
- Production configuration (`config/agent.toml`) sets `tool_concurrency_limits` for 8 of the 10
  configured MCP servers: `file_read=4, file_write=1, file_delete=1, shell=2, web_search=2,
  github=3, rag_pipeline=4, cicd=2`. The configured servers `git` and `mdq` have no entry, so
  today their calls run with no per-server ceiling at all.
- All transports share one `httpx.AsyncClient` (built in `scripts/agent/factory.py` with only a
  timeout argument; no `limits=` override anywhere in `scripts/`), so the implicit ceiling is
  httpx's library default pool, not a project decision.

## Problem
- A server omitted from `tool_concurrency_limits` — `git` and `mdq` in the current production
  config — has no in-flight ceiling; a wide parallel tool group can fan out an arbitrary number of
  concurrent POSTs to that server and consume the shared client pool.
- The health registry's HALF_OPEN logic permits one recovery trial but does not bound ordinary
  concurrent load, so it provides no protection.
- Verified doc statements that encode the gap: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
  states a `0`/negative value means unlimited "the same as the unconfigured default" — after this
  Plan the unconfigured default is bounded, so that sentence becomes false. `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`
  describes the map-and-semaphore mechanism with no default. `ToolExecutor.__init__`'s
  `concurrency_limits` docstring says "If None, no concurrency limiting is applied" — also becomes
  false.
- Corrected Issue claim: the Background's "with the default (no config)" framing understates the
  live state — most servers are capped in production; the gap is exactly the servers missing from
  the map (plus any future server).

## Reason for Change
- The invocation path is the single choke point for every MCP tool call. A guardrail that only
  exists if an operator happens to list every server key silently fails for the keys that were
  never listed, which is already the case for two production servers.

## Implementation Intent
- Decide the effective limit per server inside `_ensure_semaphores()`: positive configured value →
  that value; key absent from the map → `DEFAULT_PER_SERVER_CONCURRENCY`; `0`/negative configured
  value → unlimited (no entry, existing warning retained). Build the dict over the known server
  keys so an empty or absent map still produces caps, and keep `_maybe_semaphore(None)` as the
  unlimited path for explicit opt-outs and unknown keys.

## Requirements
- `REQ-001`: `scripts/shared/tool_transport_invoker.py` defines a module-level named constant
  `DEFAULT_PER_SERVER_CONCURRENCY: int = 8` with a comment recording the sizing rationale (highest
  configured production limit is 4; 10 configured servers x 8 = 80 stays under the shared
  `httpx.AsyncClient` default pool ceiling of 100 connections).
- `REQ-002`: `_ensure_semaphores()` creates a semaphore for every key in `self._server_configs`
  whose effective limit (configured positive, else the default) is positive, and creates no entry
  for keys explicitly configured `0`/negative. The lazy-creation guard must no longer require a
  non-empty `_concurrency_limits`, so an unconfigured invoker still gets caps.
- `REQ-003`: Configured positive limits, the unknown-key warning in `__init__`, the
  `0`/negative unlimited warning, and the `_maybe_semaphore(None)` nullcontext path are unchanged.
- `REQ-004`: The `_ensure_semaphores()` docstring, `ToolTransportInvoker.__init__` docstring, and
  the `concurrency_limits` parameter description in `ToolExecutor.__init__` state the default
  ceiling and how explicit `0`/negative limits opt out of it.
- `REQ-005`: `docs/23_agent/agent_08_03_configuration-tools-memory.md` and
  `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` describe the
  default ceiling for servers with no entry, keeping `0`/negative = unlimited.
- `REQ-006`: The intentional behavior change for currently uncapped servers (`git`, `mdq`) is
  recorded in the Plan, the docstrings, and the docs; no server currently capped is re-capped.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/tool_transport_invoker.py | Add `DEFAULT_PER_SERVER_CONCURRENCY` and restructure `_ensure_semaphores()` to cap every known server; update its docstring and the `__init__` docstring | The semaphore construction site is the only place a per-server ceiling exists in the invocation path | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006 | `_ensure_semaphores()` builds semaphores only for positive map entries; `_maybe_semaphore(None)` returns `nullcontext()` | tests/shared/test_tool_transport_invoker.py (`test_semaphore_applied_with_concurrency_limit`, the `srv=0` unlimited test, `test_positive_limit_bounds_semaphore`) | Verified |
| scripts/shared/tool_executor.py | Update the `concurrency_limits` parameter description in `ToolExecutor.__init__` ("If None, no concurrency limiting is applied" is no longer true) | The Issue's Documentation Impact names this docstring; it is the public-facing description agents and callers read | REQ-004, REQ-006 | `ToolExecutor.__init__` docstring: "concurrency_limits: Optional concurrency limits per server. If None, no concurrency limiting is applied." | tests/shared/test_tool_executor*.py (docstring-only change, no test edit) | Verified |
| tests/shared/test_tool_transport_invoker.py | Add default-cap, override, and opt-out tests with a concurrency-measuring fake | Issue Testing Expectations; no test today asserts the unconfigured default | REQ-001, REQ-002, REQ-003 | Existing semaphore tests assert configured-limit behavior only | the file itself | Verified |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Replace the "same as the unconfigured default" sentence with the bounded default plus the preserved `0`/negative opt-out | That sentence becomes actively false after the change | REQ-005, REQ-006 | "A `0` (or negative) value means \"unlimited\": no per-server semaphore is created, the same as the unconfigured default." | N/A: documentation file | Verified |
| docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md | State the default ceiling in the concurrency-mechanism description | The mechanism description omits the default and would understate the guardrail | REQ-005 | "`tool_concurrency_limits: dict[str, int]` in `ToolConfig` maps server keys to maximum concurrent calls. It is implemented as an `asyncio.Semaphore` created on-demand during tool execution." | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| config/agent.toml | Live `tool_concurrency_limits` map (8 entries) and the 10 configured `[mcp_servers.*]` keys; identifies `git` and `mdq` as the uncapped servers | scripts/shared/tool_transport_invoker.py; REQ-001 sizing, REQ-006 |
| scripts/agent/factory.py | Confirms the single shared `httpx.AsyncClient` passed to `ToolExecutor` (timeout only, no `limits=`), the pool-exhaustion premise and the sizing headroom | REQ-001, REQ-003 |
| scripts/agent/config_dataclasses.py, scripts/agent/config_section_builders.py | `tool_concurrency_limits` config surface that must remain unchanged (no new key) | Scope (new config key rejected) |
| scripts/shared/tool_transport_invoker.py `_run_precall_gates()`, `_maybe_semaphore()` | Gate order and the lazy call site of `_ensure_semaphores()`; confirms the nullcontext path stays for explicit unlimited | REQ-002, REQ-003 |
| tests/shared/test_tool_executor_order.py | Sets `executor._semaphores = None` directly and must keep working with the restructured lazy builder | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): With no `concurrency_limits` configured, concurrent calls to one
  server never exceed `DEFAULT_PER_SERVER_CONCURRENCY` in flight simultaneously.
- `AC-2` (REQ-003): A configured positive limit still caps at that configured value, not the
  default.
- `AC-3` (REQ-003): A configured `0` or negative limit produces no semaphore entry and the existing
  unlimited warning is still emitted once per process.
- `AC-4` (REQ-003): All pre-existing semaphore, health, lifecycle, and gate-order tests pass
  without modification.
- `AC-5` (REQ-004, REQ-005): Code docstrings and both agent docs describe the bounded default and
  the preserved opt-out; no text still says an unconfigured server is unlimited.

## Tests
- `REQ-002`: Unit — a fake transport that records max simultaneous in-flight calls; 20 concurrent
  `invoke()` calls against an unconfigured server assert the observed peak is exactly
  `DEFAULT_PER_SERVER_CONCURRENCY` (deterministic via asyncio events, no wall-clock sleeps).
- `REQ-003`: Unit — the same fake with `concurrency_limits={"srv": 2}` asserts the peak is 2
  (override), and with `concurrency_limits={"srv": 0}` asserts the peak reaches the full 20 (the
  opt-out bypasses the default).
- `REQ-001`: Unit — the constant exists at module level and the default-cap test references the
  constant rather than a duplicated literal.
- Regression: `tests/shared/test_tool_transport_invoker.py` and the `tests/shared/test_tool_executor*`
  suites pass unmodified.

## Documentation Impact
- Required: the two 23_agent docs named above (the task maps to the 23_agent configuration and
  concurrency-safety domains in `docs/00_index.md`'s "Document References by Task"), plus the two
  in-code docstrings the Issue names (REQ-004, REQ-005). The 22_mcp docs do not describe the
  concurrency default and need no change (verified by searching 22_mcp for the limits map).

## Assumptions
- Design decision delegated by the user on 2026-10-27 ("consider a recommended approach"); the
  adopted recommendation is per-server (not global), constant value 8, no new config key.
  Rationale is recorded in REQ-001 and Design, and the value stays tunable per server through the
  existing `tool_concurrency_limits` map.
- `mdq` and `git` are ordinary MCP server keys present in `server_configs` (verified:
  `[mcp_servers.mdq]` and `[mcp_servers.git]` in `config/agent.toml`), so capping them is a normal
  per-server semaphore, not a special case.
- httpx's default connection pool (max 100 connections, 20 keepalive) applies because no
  `limits=` argument is passed to the shared client anywhere in `scripts/`; the 8 x 10-server worst
  case (80) fits under it with headroom. If the shared client is ever given explicit limits, the
  constant's rationale comment must be revisited.
- Capping `git` and `mdq` at 8 is acceptable operationally: no configured production limit exceeds
  4, so 8 is strictly more permissive than every limit the operator has chosen so far.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `git` or `mdq` workloads in practice need more than 8 simultaneous calls | No in-flight concurrency telemetry exists for those servers | Land with the default; the existing `tool_concurrency_limits` map raises or removes the cap for a specific server without code change; revisit if transport-error counters show semaphore-queue-induced timeouts | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/tool_transport_invoker.py | Constant + `_ensure_semaphores()` restructure + docstrings | Every MCP tool call; newly caps the `git` and `mdq` servers | 4 | High (single author, 100%) | None: existing module, no new config key |
| scripts/shared/tool_executor.py | `__init__` docstring only | None at runtime | 1 | High (single author, all historical authors are the same person) | None |
| tests/shared/test_tool_transport_invoker.py | Three new unit tests | Test suite only | 4 | High (single author, 100%) | None |
| docs/23_agent/agent_08_03_configuration-tools-memory.md | Limits-map sentence rewrite | Docs domain 23_agent | 17 | High (single author, 100%) | None |
| docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md | Mechanism description update | Docs domain 23_agent | N/A (not separately profiled; low) | High (single author) | None |

## Design
- **Per-server, not global**: one semaphore per server key, matching the existing structure and the
  Issue's constraint. A global cap would over-restrict a fan-out spread across servers while the
  failure mode being guarded against is concentration on one server.
- **Value 8**: sized from repository facts rather than convention — the highest configured
  production limit is 4, and 10 configured servers at 8 stay inside the shared client's default
  pool (100). The constant is documented with that arithmetic so a future limit change is a
  deliberate edit, not a magic number.
- **Config surface unchanged (Issue question answered)**: a new `tool_concurrency_default` key
  would widen the config loader, `ToolConfig`, and the config docs for a value that is already
  per-server tunable through `tool_concurrency_limits` (add the key to lower it; set it to 0 to
  opt out). Keeping the constant process-wide makes the guardrail the default and the config map
  the exception mechanism.
- **No new constructor parameter**: `ToolTransportInvoker.__init__` and `ToolExecutor.__init__`
  already take `concurrency_limits`; adding a second tuning knob would widen two public signatures
  for the same concern. Tuning is documented instead.
- **Guard placement in `_ensure_semaphores()`** (not `_maybe_semaphore()`): building the dicts once
  per process keeps the lazy-init semantics and keeps `_maybe_semaphore`'s nullcontext contract for
  the explicit-unlimited and unknown-key paths; building over `self._server_configs` (not the limits
  map) is what closes the omitted-key gap.
- **Unlimited semantics preserved**: `0`/negative stays unlimited and stays warned once per
  process, so the documented opt-out is never silently re-bounded.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/shared/test_tool_transport_invoker.py` and the `tests/shared/test_tool_executor*`
     suites unchanged to pin current semaphore behavior (REQ-003;
     `scripts/shared/tool_transport_invoker.py`).
2. **Phase 2: Default cap**
   - [ ] Add `DEFAULT_PER_SERVER_CONCURRENCY` with its rationale comment (REQ-001;
     `scripts/shared/tool_transport_invoker.py`).
   - [ ] Restructure `_ensure_semaphores()` to resolve effective limits over
     `self._server_configs` and drop the non-empty-map guard (REQ-002;
     `scripts/shared/tool_transport_invoker.py`).
   - [ ] Update `_ensure_semaphores()` and `ToolTransportInvoker.__init__` docstrings (REQ-004;
     `scripts/shared/tool_transport_invoker.py`).
   - [ ] Update the `concurrency_limits` parameter description in `ToolExecutor.__init__`
     (REQ-004, REQ-006; `scripts/shared/tool_executor.py`).
3. **Phase 3: Tests, docs, deployment check, and verification**
   - [ ] Add the default-cap, override, and opt-out tests with a concurrency-measuring fake
     (REQ-001, REQ-002, REQ-003; `tests/shared/test_tool_transport_invoker.py`).
   - [ ] Update the two 23_agent docs (REQ-005;
     `docs/23_agent/agent_08_03_configuration-tools-memory.md`,
     `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`).
   - [ ] Deployment validation/scripts check: confirm no new config key and no config-loader change;
     `config/agent.toml` and `deploy.sh` stay unchanged, and note in the commit message that
     `git`/`mdq` become capped at the default (REQ-006; `config/agent.toml` read-only check).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/tool_transport_invoker.py | Unit (concurrency-measuring fake transport) | `uv run pytest tests/shared/test_tool_transport_invoker.py` | Default cap, override, and opt-out tests pass |
| scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; `shared` leaf contract preserved |
| All targets | Regression | `uv run pytest tests/` | Full suite green, no pre-existing test edited |
| docs/23_agent/agent_08_03_configuration-tools-memory.md, docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md | Documentation consistency (23_agent domain) | `rules/toolchain.md` documentation consistency check | Docs describe the bounded default and the preserved opt-out |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New default-cap branches covered |

## Risks
- **Risk**: capping `git` and `mdq` (uncapped today) introduces queuing that could surface as slow
  calls or timeouts under heavy parallel fan-out → **Mitigation**: 8 exceeds every limit the
  operator has configured for the other eight servers; the map entry for a server can be raised or
  set to 0 without a code change; transport-error counters remain the detection channel (UNK-01).
- **Risk**: tests that construct invokers without limits now build semaphores, changing gate
  behavior in existing tests → **Mitigation**: verified — no test asserts `_semaphores is None` for
  an unconfigured invoker; `test_tool_executor_order.py` assigns `_semaphores` directly and stays
  valid; Phase 1 baseline plus the full-suite run confirm it.
- **Risk**: `scripts/shared/tool_executor.py` is also edited by the mcpinv002 Plan → **Mitigation**:
  disjoint regions (docstring vs. dead-method deletion); both Plans record the overlap as
  Compatible and the second implementer rebases.
- **Risk**: the sizing rationale depends on httpx's default pool, which is a library default rather
  than a pinned project value → **Mitigation**: rationale comment names the dependency (REQ-001) so
  a future `limits=` change is noticed where the constant is defined.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | — | 20261028-102436 |  |
| 2 | Phase 2: default cap | Completed | — | 20261028-102436 |  |
| 3 | Phase 3: tests, docs, deployment check, verification | Completed | — | 20261028-102436 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-004831_01_scripts_shared_tool_transport_invoker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-004831_02_scripts_shared_tool_executor.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-004831_03_tests_shared_test_tool_transport_invoker.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-004831_04_docs_23_agent_agent_08_03_configuration-tools-memory.md | 3 | Procedure | Pending | — | — |
| implementations/20261028-004831_05_docs_23_agent_agent_06_03_tool-execution-and-approval-concurrency-safety.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-104612
- **Related target files**: scripts/shared/tool_transport_invoker.py, scripts/shared/tool_executor.py, tests/shared/test_tool_transport_invoker.py, docs/23_agent/agent_08_03_configuration-tools-memory.md, docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent ("named constant"); sizing evidence from `config/agent.toml` and `scripts/agent/factory.py` | scripts/shared/tool_transport_invoker.py | Phase 2 | AC-1 | Constant-referencing default-cap test | Confirmed by repository evidence |
| REQ-002 | Problem (uncapped omitted keys); `_ensure_semaphores()` verified | scripts/shared/tool_transport_invoker.py | Phase 2 | AC-1 | Default-cap unit test | Confirmed by repository evidence |
| REQ-003 | Constraints ("positive limits unchanged", "0/negative stays unlimited") | scripts/shared/tool_transport_invoker.py | Phase 2 | AC-2, AC-3, AC-4 | Override and opt-out tests; existing suite unmodified | Confirmed by repository evidence |
| REQ-004 | Issue Documentation Impact (docstrings) | scripts/shared/tool_transport_invoker.py | Phase 2 | AC-5 | Docstring review | Confirmed by repository evidence |
| REQ-004 | Verified stale docstring in `ToolExecutor.__init__` | scripts/shared/tool_executor.py | Phase 2 | AC-5 | Docstring review | Confirmed by repository evidence |
| REQ-005 | Verified stale sentence in `agent_08_03` | docs/23_agent/agent_08_03_configuration-tools-memory.md | Phase 3 | AC-5 | 23_agent documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Mechanism description in `agent_06_03` | docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md | Phase 3 | AC-5 | 23_agent documentation consistency check | Confirmed by repository evidence |
| REQ-006 | Verified uncapped servers (`git`, `mdq`) | scripts/shared/tool_transport_invoker.py | Phase 3 | AC-1 | `config/agent.toml` read-only check + commit-message note | Confirmed by repository evidence |
| REQ-001, REQ-002, REQ-003 | Issue Testing Expectations | tests/shared/test_tool_transport_invoker.py | Phase 3 | AC-1, AC-2, AC-3 | Three new unit tests | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-004831 -->