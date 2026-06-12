# Refactoring Plan

## 1. General Policy

### 1.1 Design Principles

- Unify Dependency Direction: Enforce `REPL -> Orchestrator/UseCase -> Service -> Repository/Adapter`. Currently, responsibilities are overly concentrated across `orchestrator.py`, `factory.py`, and `session.py`.
- Standardize Exception Contracts: Unify error handling across components. Currently, return values, raising exceptions, and injecting synthetic history messages are inconsistently mixed, with fragmented policies among `orchestrator.py`, `llm_turn_runner.py`, and `error_injection_service.py`.
- Eliminate Legacy Flat Access: Phased deprecation of backward-compatibility flat access. Enforce explicit nested routing: `ctx.conv.*`, `ctx.turn.*`, `ctx.stats.*`, `ctx.services.*`, and `ctx.cfg.*`. Clean up remaining compatibility-preserving comments in `context.py` and `config.py`.
- Centralize Lifecycle and Monitoring: Consolidate monitoring and component lifecycles into a structured state transition model. Current logic is fragmented across `repl_health.py`, `lifecycle.py`, `http_lifecycle.py`, and `stdio_lifecycle.py`.

## 2. Refactoring Plan

### 2.1 Target Files

- `factory.py`
- `session.py`
- `history.py`

### 2.2 Objectives

- Decompose Dependency Injection (DI) construction, data persistence, and history compression by distinct domains to significantly improve testability and long-term maintainability.

### 2.3 File-Specific Plans

#### 2.3.1 `factory.py`

- Current State
  - `build_agent_context()` handles service injection into `ctx.services`. The same file also hosts individual builders for the LLM client, ToolExecutor, HistoryManager, MemoryLayer, plugin registry, and tracer.
  - The plugin directory path is hardcoded using a fixed relative look-up: `Path(__file__).parent.parent.parent / "plugins"`.
- Proposed Changes
  - Split the monolith into granular sub-modules: `agent/bootstrap.py`, `agent/service_factory.py`, and `agent/logger_factory.py`.
  - Expose the plugin directory path as a configurable setting.
  - Explicitly define the cleanup and rollback contract when initialization fails (exact execution path details are currently unverified).
- Code Example

```python
# agent/bootstrap.py
async def bootstrap_agent(ctx: AgentContext, view: CLIView) -> None:
    init_plugins(ctx)
    init_tracing(ctx)
    ctx.services = build_services(ctx, view)

```

* Impact & Blast Radius
* Modifies the application startup and bootstrapping sequence within `repl.py`.
* Requires clarifying the exact initialization sequence and the mandatory versus optional boundaries of fields in `AppServices`.



#### 2.3.2 `session.py`

* Current State
* `SessionMessageRepository`, `DocumentRepository`, `NoteRepository`, and `AgentSession` are tightly coupled and co-exist inside a single file.
* Database error handling is fragmented, returning mixed types such as `None`, `False`, `[]`, or `0`.


* Proposed Changes
* Separate responsibilities into isolated individual files: `agent/session_message_repository.py`, `agent/document_repository.py`, `agent/note_repository.py`, and `agent/agent_session.py`.
* Unify the error contract by enforcing a custom exception pattern like `RepositoryError` or a robust `Result[T, E]` type wrapper.
* Align database transaction boundaries so that turn persistence and undo actions are executed as atomic blocks.


* Code Example

```python
# agent/session_message_repository.py
class SessionMessageRepository:
    def __init__(self, db: SessionDb) -> None:
        self._db = db

    def save_many(self, session_id: int, messages: list[SessionMessage]) -> None:
        ...

```

* Impact & Blast Radius
* Requires adjusting all orchestration logic where `ctx.session.save(...)` is invoked inside `orchestrator.py` and `llm_turn_runner.py`.
* Enables decoupling database repository testing from `AgentSession` integration testing.



#### 2.3.3 `history.py`

* Current State
* `HistoryManager` encapsulates character/token budget tracking, compression target identification, LLM-based summarization, summary appending, and update notification callbacks.
* `_select_turns_to_compress()` determines compression candidates based on rigid categories: `temporary`, `temporary_reasoning`, `factual`, and `history`.


* Proposed Changes
* Decouple the monolithic component into `agent/history_selection_policy.py` and `agent/history_summarizer.py`.
* Refactor the `[Conversation summary]` append mechanism into a chained model. The current strategy appends directly to the existing summary block, which scales poorly and bloats easily.
* Make the underlying token counting strategy completely pluggable via dependency injection.


* Code Example

```python
# agent/history_selection_policy.py
class HistorySelectionPolicy:
    def select(self, history: list[LLMMessage]) -> CompressionPlan:
        ...

# agent/history_summarizer.py
class HistorySummarizer:
    async def summarize(self, messages: list[LLMMessage]) -> str | None:
        ...

```

* Impact & Blast Radius
* Changes the setup inside `factory.py`'s `_build_history_manager()`, which will now instantiate multiple separate services.
* Impact on `orchestrator.py` is minimal as long as the high-level public `compress()` API contract remains unchanged.



### 2.4 Phase 2 Execution Order

1. Deconstruct `factory.py` into separate application bootstrapping and service factory modules.
2. Separate `session.py` into individual database domain repository modules.
3. Split `history.py` into isolated selection policy and summarization domain services.

## 3. Risks and Uncertainties

* Unverified Core Implementation: The full source implementations of `context.py` and `config.py` have not been entirely cross-referenced. A complete codebase verification is mandatory before removing legacy compatibility layers.
* Opaque REPL Lifecycle: `repl.py` is only partially visible via primary imports and high-level documentation. The precise application bootstrap and execution sequence remain unverified.
* Test Suite Status: The existence, coverage, and structure of current automated tests are unknown. Consequently, this plan focuses exclusively on structural readiness and architectural refactoring without defining specific test suite updates.
