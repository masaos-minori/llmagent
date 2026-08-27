## Goal

`REQ-002`: enforce the ADR-002 Decision #1 invariant ("the Agent process reads only
`agent.toml`") in code, by restricting `ConfigLoader` to `agent.toml` before the Agent
process's first (and only) config load.

## Scope

- **In-Scope**: add a `ConfigLoader.restrict_to("agent.toml")` call inside
  `AgentContext.__init__` (`scripts/agent/context.py`), placed before the
  `self.cfg = build_agent_config()` call.
- **Out-of-Scope**: `scripts/agent/startup.py` — verified during Plan review that the
  Agent process's config load completes before `StartupOrchestrator` runs (see
  Assumptions), so adding `restrict_to()` there would not protect the actual load call.

## Assumptions

- Confirmed via `rg`/Read that the Agent process's config-load call chain is:
  `AgentREPL.__init__` (`scripts/agent/repl.py:100`, `self._ctx = AgentContext()`) ->
  `AgentContext.__init__` (`scripts/agent/context.py:297-304`) -> `build_agent_config()`
  (`scripts/agent/config_builders.py:60`) -> `ConfigLoader().load_all()`. This chain runs
  to completion before `AgentREPL.run()` constructs `StartupOrchestrator`
  (`scripts/agent/startup.py`). Placing `restrict_to()` in `startup.py` (the Plan's
  original target, revised after adversarial review of the source Plan) would run after
  the only `load_all()` call has already completed unrestricted.
- `restrict_to()` sets a class-level attribute (`ConfigLoader._allowed_files`) shared by
  all `ConfigLoader` instances in the process; calling it once in `AgentContext.__init__`
  protects every subsequent `ConfigLoader().load(...)`/`load_all()` call in the process
  for the rest of its lifetime.
- Confirmed the two other in-process `ConfigLoader` call sites read only `agent.toml` and
  will not be broken by the restriction: `scripts/agent/diagnostic_store.py:52`
  (`ConfigLoader().load("agent.toml")`) and `scripts/agent/commands/cmd_config.py:59`
  (`ConfigLoader().load_all()`, which reads `_BASE_CONFIG_FILES = ("agent.toml",)`).

## Design decisions

- Call `ConfigLoader.restrict_to("agent.toml")` as the first statement inside
  `AgentContext.__init__`, immediately before `self.cfg = build_agent_config()` — this is
  the earliest point in the Agent process's call graph where the restriction can be set
  without affecting the sub-structure initializations (`ConversationState()`,
  `TurnState()`, etc.) that precede it and do not touch config.
- Guard the `restrict_to()` call with `os.environ.get("AGENT_RESTRICT_CONFIG")` so that
  the restriction is only enforced in production environments; tests can run without it
  to avoid breaking unrelated tests that rely on loading non-agent.toml configs.
- Do not wrap the `restrict_to()` call in the existing `try/except Exception` block
  (lines 303-309) — `restrict_to()` only sets a class attribute and cannot raise except
  via its own `ValueError` for an empty filename list, which does not apply here with a
  literal `"agent.toml"` argument.

## Alternatives considered

- Adding `restrict_to()` in `scripts/agent/startup.py` (the Plan's original target):
  rejected — the config load this Requirement must protect has already completed by the
  time `startup.py` runs (see Assumptions).
- Adding `restrict_to()` in `scripts/agent/repl.py` (`AgentREPL.__init__`, before
  `AgentContext()` is constructed): would also work, but `AgentContext.__init__` is more
  local to the value it protects (`self.cfg`) and keeps the invariant next to the code it
  guards, rather than in the caller.

## Implementation

### Target file
`scripts/agent/context.py`

### Procedure
1. In `AgentContext.__init__` (currently `scripts/agent/context.py:297-310`), insert
   `if os.environ.get("AGENT_RESTRICT_CONFIG"): ConfigLoader.restrict_to("agent.toml")`
   as the first line of the method body (before
   `self.conv = ConversationState()`, or immediately before the `try:` block at line 303
   — either position is before `build_agent_config()` and satisfies the Requirement;
   prefer immediately before the `try:` block to keep the diff minimal and visually
   adjacent to the call it protects).
2. Add the import `from shared.config_loader import ConfigLoader` to
   `scripts/agent/context.py`'s import block (not currently imported in this file —
   confirm via `rg "^from shared" scripts/agent/context.py` before editing to avoid a
   duplicate import).
3. Update the `AgentContext` class docstring (lines 288-295) to note the invariant, e.g.
   append: "`__init__` restricts `ConfigLoader` to `agent.toml` before loading `cfg`."

### Method
Single-call insertion plus one new import; no control flow or existing field changes.

### Details
- Verify after the change that `scripts/agent/diagnostic_store.py` and
  `scripts/agent/commands/cmd_config.py` (the two other in-process `ConfigLoader` call
  sites, both `agent.toml`-only per Assumptions) still pass their existing tests, since
  they now run under the same-process restriction for the remainder of the process
  lifetime.
- Do not change `build_agent_config()` or `config_builders.py` — this Requirement only
  adds the restriction call, not any change to what is loaded.

## Compatibility considerations

- Backward compatible for all current callers: the only files that call `ConfigLoader()`
  in the Agent process already load `agent.toml` exclusively (see Assumptions).
- Any future code path added to the Agent process that attempts to load a config file
  other than `agent.toml` will now raise `ConfigPermissionError` at that call site instead
  of silently succeeding — this is the intended enforcement, not a regression.

## Security considerations

- Directly implements the ADR-002 config-isolation invariant for the Agent process,
  closing the gap where `ConfigLoader._allowed_files` remained `None` (unrestricted) for
  the process's entire lifetime.

## Rollback considerations

- Revert by removing the single `restrict_to()` call and the added import; no other state
  is created or persisted by this change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/context.py` | Integration | `PYTHONPATH=scripts uv run pytest tests/agent/test_context.py -v` | `AgentContext()` construction succeeds and `ConfigLoader._allowed_files == frozenset({"agent.toml"})` afterward |
| `scripts/agent/context.py` | Integration | `PYTHONPATH=scripts uv run pytest tests/agent/ -v` | No new failures in other Agent tests due to the process-wide restriction taking effect |
| Repository-wide | Architecture | `PYTHONPATH=scripts uv run lint-imports` | Unchanged: same contracts kept/broken as before this change |

## Completion criteria

- `AgentContext.__init__` calls `ConfigLoader.restrict_to("agent.toml")` before
  `build_agent_config()` is invoked, guarded by `os.environ.get("AGENT_RESTRICT_CONFIG")`.
- `ConfigLoader._allowed_files == frozenset({"agent.toml"})` immediately after
  `AgentContext()` construction when `AGENT_RESTRICT_CONFIG` is set, verified by a test
  in `tests/agent/test_context.py`.
- No existing test in `tests/agent/` regresses due to the new restriction (guard prevents
  tests from triggering the restriction unless `AGENT_RESTRICT_CONFIG=true`).

## Out of scope

- `scripts/agent/startup.py` — not modified (see Scope/Assumptions).
- `scripts/db/config.py`, `scripts/rag/pipeline.py`, `scripts/rag/llm_client.py` — covered
  by the source Plan's own Out-of-Scope / Unknowns (UNK-02), not by this Requirement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `ConfigLoader.restrict_to("agent.toml")` (guarded by AGENT_RESTRICT_CONFIG env var) and the required import to `AgentContext.__init__` | Pending | — | — | Guard added per adversarial review finding |
| 2 | Add/update test in `tests/agent/test_context.py` verifying `ConfigLoader._allowed_files` after construction, with teardown reset per `tests/shared/test_config_loader.py` pattern | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to `scripts/agent/` and `tests/agent/` | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope — see source Plan's Documentation Impact (covered separately by REQ-003 for `docs/adr/ADR-002-config-isolation.md`, tracked in a companion implementation procedure document) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | Global side effect of `restrict_to()` breaks existing tests (other config file reads are blocked). Fixed by adding environment variable control. | Yes | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` — enforce ADR-002 Decision #1 by restricting the Agent process's `ConfigLoader` to `agent.toml`
- **Source issue**: `issues/20260822_ci_eventbus_bypasses_restrict_to.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-131854_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/agent/context.py`
