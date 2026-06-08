# Refactoring Plan

## 1. General Policy

### 1.1 Design Principles

- Unify Dependency Direction: Enforce `REPL -> Orchestrator/UseCase -> Service -> Repository/Adapter`. Currently, `orchestrator.py`, `factory.py`, and `session.py` are coupled with multiple responsibilities.
- Standardize Exception Contracts: Unify error handling across components. Currently, `return`, `raise`, and synthetic history message injection are mixed inconsistently, particularly among `orchestrator.py`, `llm_turn_runner.py`, and `error_injection_service.py`.
- Eliminate Legacy Flat Access: Phased deprecation of backward-compatibility flat access. Enforce explicit nested routing: `ctx.conv.*`, `ctx.turn.*`, `ctx.stats.*`, `ctx.services.*`, and `ctx.cfg.*`. Clean up remaining compatibility-preserving comments in `context.py` and `config.py`.
- Centralize Lifecycle and Monitoring: Consolidate monitoring and component lifecycles into a structured state machine model. Current logic is fragmented across `repl_health.py`, `lifecycle.py`, `http_lifecycle.py`, and `stdio_lifecycle.py`.

## 2. Refactoring Plan

### 2.1 Target Files

- `orchestrator.py`
- `llm_turn_runner.py`
- `config.py`
- `context.py`

### 2.2 Objectives

- Isolate Turn Execution and Shared State: Clarify boundaries between turn control flow and shared data context to establish a solid foundation for subsequent modular refactoring. This area has the largest blast radius since `orchestrator.py` governs the turn lifecycle/auditing and `llm_turn_runner.py` drives the LLM streaming and tool execution loop.
- Stabilize State Reference Paths: Clean up legacy flat-access compatibility logic within `config.py` and `context.py` to ensure predictable state lookup paths.

### 2.3 File-Specific Plans

#### 2.3.1 `orchestrator.py`

- Current State
  - `handle_turn()` acts as a monolith handling turn initialization, memory injection, user message attachment, history truncation, LLM invocation, and turn audit logging within a single class.
  - `_append_user_message()` tightly couples system prompt synchronization, turn count increments, first-turn callback execution, and session state persistence.
  - `_handle_llm_transport_error()` handles partial completion saving alongside pre-stream failure rollbacks.
- Proposed Changes
  - Extract responsibilities into separate granular services: `agent/turn_start_service.py`, `agent/prompt_assembly_service.py`, `agent/turn_audit_service.py`, and `agent/turn_error_policy.py`. Downsize `Orchestrator` to a thin controller.
  - Refactor `TurnResult` into a structured `dataclass` to decouple UI messaging from control logic.
  - Offload `asyncio.create_task(self._on_first_turn(line))` to a managed background task registry to prevent unhandled background exceptions.
- Code Example

```python
# agent/orchestrator.py
@dataclass
class TurnResult:
    success: bool
    answer: str = ""
    error_kind: str | None = None

class Orchestrator:
    def __init__(self, ctx: AgentContext, services: TurnServices) -> None:
        self._ctx = ctx
        self._services = services

    async def handle_turn(self, line: str) -> TurnResult:
        started = self._services.turn_start.begin(line)
        try:
            await self._services.prompt_assembly.prepare(line)
            await self._services.history.compress_if_needed()
            return await self._services.llm.run(self._ctx.conv.llm_url)
        except Exception as e:
            return await self._services.error_policy.handle(e)
        finally:
            await self._services.turn_audit.end(started)

```

* Impact & Blast Radius
* Requires updating how `Orchestrator` is instantiated inside `repl.py` (switching from direct callback passing to injecting a unified service bundle).
* May require introducing a dedicated background task tracking field to `TurnState` in `context.py`.



#### 2.3.2 `llm_turn_runner.py`

* Current State
* `run()` contains a monolithic loop managing maximum tool turns, LLM streaming, tool call parsing, guardrails, tool execution, and error metric updates.
* `_handle_llm_error()` dynamically instantiates `ErrorInjectionService` on every execution path.


* Proposed Changes
* Subdivide into isolated components: `agent/llm_stream_service.py`, `agent/tool_turn_loop.py`, and `agent/span_context.py`.
* Pass `ErrorInjectionService` via Dependency Injection (DI) and eliminate dynamic inline imports.
* Upgrade static string returns (e.g., `"Maximum tool turns reached."`) into structured outcome models or dedicated exception types.


* Code Example

```python
# agent/tool_turn_loop.py
@dataclass
class ToolLoopOutcome:
    status: Literal["completed", "tool_limit", "guard_blocked", "error"]
    answer: str = ""
    error_kind: str | None = None

class ToolTurnLoop:
    def __init__(
        self,
        ctx: AgentContext,
        stream_service: LLMStreamService,
        tool_guard: ToolLoopGuard,
        error_injector: ErrorInjectionService,
    ) -> None:
        ...

```

* Impact & Blast Radius
* Changes the return type expectation of `orchestrator.py` 's `_handle_llm_turn()` from a raw `str` to a structured `ToolLoopOutcome`.
* Requires wiring up the new sub-services inside `factory.py`.



#### 2.3.3 `config.py`

* Current State
* `AgentConfig` aggregates 7 distinct sub-configurations while preserving flat attribute access solely for backward compatibility.
* `DbConfig` is co-located within the same config file.


* Proposed Changes
* Establish a multi-phase deprecation plan to remove flat access completely, transitioning strictly to nested path access.
* Isolate I/O logic into `load_config()` and keep `build_agent_config()` as a pure configuration constructor.
* Extract `DbConfig` out into `db/config.py`.


* Code Example

```python
# agent/config_loader.py
def load_agent_config_dict() -> dict[str, Any]:
    return ConfigLoader().load_all()

# agent/config.py
def build_agent_config(raw: dict[str, Any]) -> AgentConfig:
    llm = _build_llm_config(raw)
    rag = _build_rag_config(raw)
    tool = _build_tool_config(raw, system_prompt_tool)
    return AgentConfig(llm=llm, rag=rag, tool=tool, ...)

```

* Impact & Blast Radius
* High blast radius: Requires sweeping updates to property access across `factory.py`, `orchestrator.py`, `history.py`, and `context.py`.



#### 2.3.4 `context.py`

* Current State
* Code comments outline clear architectural separation boundaries for `ConversationState`, `TurnState`, `RuntimeStats`, `AppServices`, and `AgentContext`.
* However, the actual underlying dataclass schemas and flat compatibility implementations remain unverified.


* Proposed Changes
* Deprecate the flat attribute compatibility layer completely; enforce structured access via `ctx.conv.*`, `ctx.turn.*`, `ctx.stats.*`, and `ctx.services.*`.
* Extend `TurnState` to encapsulate active background tasks and turn-local error states (`current_turn_id` is already utilized by `orchestrator.py`).
* Funnel all runtime metric/statistic increments through dedicated domain services rather than direct state mutation.


* Code Example

```python
# agent/context.py
@dataclass
class TurnState:
    current_turn_id: str | None = None
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    last_error_kind: str | None = None

```

* Impact & Blast Radius
* Fix state reference lookup paths throughout `repl.py`, `orchestrator.py`, `llm_turn_runner.py`, and `factory.py`.
* Because details are currently unverified, a full structural code review of `context.py` is required prior to execution.



### 2.4 Phase 1 Execution Order

1. Enforce and lock down the updated reference conventions for `config.py` and `context.py`.
2. Extract modular services from `orchestrator.py` to thin out the orchestrator.
3. Turn `llm_turn_runner.py` into a thin facade by extracting internal loop responsibilities.

## 3. Risks and Uncertainties

* Unverified Core Implementation: The full source implementations of `context.py` and `config.py` have not been entirely cross-referenced. A complete codebase verification is mandatory before removing legacy compatibility layers.
* Opaque REPL Lifecycle: `repl.py` is only partially visible via primary imports and high-level documentation. The precise application bootstrap and execution sequence remain unverified.
* Test Suite Status: The existence, coverage, and structure of current automated tests are unknown. Consequently, this plan focuses exclusively on structural readiness and architectural refactoring without defining specific test suite updates.
