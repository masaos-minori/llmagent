# Refactoring Plan

## 1. General Policy

### 1.1 Design Principles

- Unify Dependency Direction: Enforce `REPL -> Orchestrator/UseCase -> Service -> Repository/Adapter`. Currently, responsibilities are overly concentrated across `orchestrator.py`, `factory.py`, and `session.py`.
- Standardize Exception Contracts: Unify error handling across components. Currently, return values, raising exceptions, and injecting synthetic history messages are inconsistently mixed, with fragmented policies among `orchestrator.py`, `llm_turn_runner.py`, and `error_injection_service.py`.
- Eliminate Legacy Flat Access: Phased deprecation of backward-compatibility flat access. Enforce explicit nested routing: `ctx.conv.*`, `ctx.turn.*`, `ctx.stats.*`, `ctx.services.*`, and `ctx.cfg.*`. Clean up remaining compatibility-preserving comments in `context.py` and `config.py`.
- Centralize Lifecycle and Monitoring: Consolidate monitoring and component lifecycles into a structured state transition model. Current logic is fragmented across `repl_health.py`, `lifecycle.py`, `http_lifecycle.py`, and `stdio_lifecycle.py`.

## 2. Refactoring Plan

### 2.1 Target Files

- `repl.py`
- `repl_health.py`
- `lifecycle.py`
- `http_lifecycle.py`
- `stdio_lifecycle.py`
- `cli_view.py`

### 2.2 Objectives

- Streamline application bootstrapping, health monitoring, server restart mechanisms, and CLI presentation to decouple operational and infrastructure responsibilities from core application logic.

### 2.3 File-Specific Plans

#### 2.3.1 `repl.py`

- Current State
  - `AgentREPL` serves as the primary entry point, orchestrating `CLIView`, `CommandRegistry`, `AgentContext`, `build_agent_context`, `Orchestrator`, and internal functions from `repl_health.py`. The complete implementation details of its methods remain unverified.
- Proposed Changes
  - Migrate all initialization and bootstrapping responsibilities into a new `agent/app_runner.py` or `agent/bootstrap.py` module, downsizing `AgentREPL` to strictly handle the interactive input/output loop.
  - Remove all direct wiring for health checking and watchdog loops from `repl.py`.
- Code Example

```python
# agent/app_runner.py
async def run_app() -> None:
    ctx = build_initial_context()
    view = CLIView(...)
    await bootstrap_agent(ctx, view)
    repl = AgentREPL(ctx, view, ...)
    await repl.run()

```

* Impact & Blast Radius
* Restructures the application startup sequence across `factory.py` and `repl_health.py`.
* Since the complete codebase implementation details are unverified, specific diffs must be adjusted after further code inspection.



#### 2.3.2 `repl_health.py`

* Current State
* `check_service_health()`, tool definition validations (at both startup and runtime), and `watchdog_loop()` are coupled within a single file. There is a high degree of overlap between startup and runtime tool validation logic.


* Proposed Changes
* Subdivide the file into isolated specialized modules: `agent/health_probe.py`, `agent/tool_definition_validator.py`, and `agent/watchdog.py`.
* Introduce a unified `validate_tool_definitions(strict: bool)` function to eliminate redundant verification code paths.
* Evaluate moving the management of the application restart counter into the lifecycle domain.


* Code Example

```python
# agent/tool_definition_validator.py
async def validate_tool_definitions(ctx: AgentContext, strict: bool) -> list[str]:
    ...

```

* Impact & Blast Radius
* Changes the required imports and initialization ordering within `repl.py`.



#### 2.3.3 `lifecycle.py`

* Current State
* Functions as a facade that blindly delegates to the respective HTTP or stdio managers. The `get_transport_state()` method exhibits asymmetric behavior, returning `None` for HTTP but returning a structured `TransportState` object for stdio.


* Proposed Changes
* Define a common `LifecycleState` enum to ensure both HTTP and stdio transport managers return a unified, predictable state model.
* Refactor the transport-specific branching logic inside `ensure_ready()` using the Strategy pattern.


* Code Example

```python
class LifecycleState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"

```

* Impact & Blast Radius
* Requires updating components that consume the lifecycle status API. The exact downstream impacts cannot be determined from the current partial codebase analysis.



#### 2.3.4 `http_lifecycle.py`

* Current State
* Implements subprocess spawning, `/health` polling endpoint checks, process termination/killing on timeout thresholds, process restarts, and a global `shutdown_all` workflow. While a `StartupFailure` dataclass exists, error handling heavily relies on plain `RuntimeError` text strings.


* Proposed Changes
* Elevate the `StartupFailure` dataclass to a fully structured custom exception type.
* Encapsulate the process termination sequence into a shared helper utility to eliminate code duplication.
* Decouple the subprocess spawning routine from the health-polling monitoring loop.


* Code Example

```python
class HttpStartupError(RuntimeError):
    def __init__(self, failure: StartupFailure) -> None:
        self.failure = failure
        super().__init__(failure.reason)

```

* Impact & Blast Radius
* Enables structured logging and precise restart decisions within `lifecycle.py` and `repl_health.py`.



#### 2.3.5 `stdio_lifecycle.py`

* Current State
* Manages on-demand process invocation, double-checked locking mechanisms, idle-timeout process shutdowns, restarts, and transport state transitions. The file suffers from redundant state keeping via `_stdio_procs` and `_transport_states`.


* Proposed Changes
* Consolidate the transport instance and its state into a single cohesive `TransportHandle` object.
* Disentangle configuration validation from the active process invocation inside `_start()` to enable clear categorization of failure reasons.


* Code Example

```python
@dataclass
class TransportHandle:
    transport: StdioTransport | None
    state: TransportState
    last_error: str | None = None

```

* Impact & Blast Radius
* Simplifies the state management API exposed by `lifecycle.py`.
* Enhances the diagnostics and observability of stdio restarts inside the watchdog service.



#### 2.3.6 `cli_view.py`

* Current State
* `CLIView` is a monolith handling Writer/Reader Protocols, readline terminal history, progress indicators, warning alerts, debug RAG payload formatting, and multiline text input parsing. Visual output is tightly coupled to native `print()` statements.
* The terminal history file path is hardcoded to a fixed location: `Path.home() / ".agent_history"`.


* Proposed Changes
* Separate data formatting logic from visual rendering logic by introducing a new `agent/cli_presenter.py` component.
* Externalize the terminal history file path into a configurable parameter.
* Convert the hardcoded progress bar rendering width into a defined constant to allow future integration with dynamic terminal window width resolution.


* Code Example

```python
# agent/cli_presenter.py
def format_debug_rag(data: DebugRagData) -> list[str]:
    ...

```

* Impact & Blast Radius
* Requires reviewing the connection strategy and payload structure matching `rag_debug.py`. Currently, `write_debug_rag()` renders raw dictionaries directly.
* Requires updating `factory.py` or the configuration loader to pass the terminal history file path into the view layer.



### 2.4 Phase 3 Execution Order

1. Restructure the state models across `repl_health.py` and the respective transport lifecycle modules.
2. Separate `repl.py` into distinct application bootstrapping and operational REPL processing modules.
3. Decouple presentation and formatting logic from `cli_view.py` into a dedicated presenter.

## 3. Risks and Uncertainties

* Unverified Core Implementation: The full source implementations of `context.py` and `config.py` have not been entirely cross-referenced. A complete codebase verification is mandatory before removing legacy compatibility layers.
* Opaque REPL Lifecycle: `repl.py` is only partially visible via primary imports and high-level documentation. The precise application bootstrap and execution sequence remain unverified.
* Test Suite Status: The existence, coverage, and structure of current automated tests are unknown. Consequently, this plan focuses exclusively on structural readiness and architectural refactoring without defining specific test suite updates.
