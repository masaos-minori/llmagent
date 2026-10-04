# AppServices: Constructor does not validate required services are non-None

## Background

`AppServices` in `scripts/agent/context.py` represents fully-initialized service references built by `factory.py`. Its docstring states: "All required services are non-None."

## Problem

The constructor accepts `None` for all parameters including required ones (`http`, `llm`, `tools`, `lifecycle`, `hist_mgr`, `audit_logger`). There is no runtime validation that required services are present.

## Evidence

- File: `scripts/agent/context.py`
- Lines 248-281:

```python
class AppServices:
    """Fully-initialized service references built by factory.py.

    All required services are non-None.  memory is None when
    use_memory_layer=False (intentionally absent, not uninitialised).
    gateway is None until factory.py constructs and injects RepositoryGateway.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,           # Required — no default
        llm: LLMClient,                     # Required — no default
        tools: ToolExecutor,                # Required — no default
        lifecycle: LifecycleManagerProtocol,# Required — no default
        hist_mgr: HistoryManager,           # Required — no default
        audit_logger: Logger,               # Required — no default
        memory: MemoryServices | None = None,   # Optional
        health_registry: McpServerHealthRegistry | None = None,  # Optional
        gateway: RepositoryGateway | None = None,  # Optional
        runtime_tools: RuntimeToolRegistry | None = None,  # Optional
    ) -> None:
        """Initialize all required service references for the agent runtime."""
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        ...
```

## Impact

- A caller passing `None` for a required service creates an invalid object
- Errors manifest later at access time, far from the root cause
- Type hints suggest required services but enforcement is absent

## Recommended action

Add validation in the constructor for required services:

```python
def __init__(
    self,
    http: httpx.AsyncClient,
    llm: LLMClient,
    tools: ToolExecutor,
    lifecycle: LifecycleManagerProtocol,
    hist_mgr: HistoryManager,
    audit_logger: Logger,
    memory: MemoryServices | None = None,
    health_registry: McpServerHealthRegistry | None = None,
    gateway: RepositoryGateway | None = None,
    runtime_tools: RuntimeToolRegistry | None = None,
) -> None:
    required = {
        "http": http,
        "llm": llm,
        "tools": tools,
        "lifecycle": lifecycle,
        "hist_mgr": hist_mgr,
        "audit_logger": audit_logger,
    }
    for name, value in required.items():
        if value is None:
            raise RuntimeError(f"Required service '{name}' is None")
    self.http = http
    self.llm = llm
    self.tools = tools
    self.lifecycle = lifecycle
    self.hist_mgr = hist_mgr
    self.audit_logger = audit_logger
    ...
```

## Acceptance criteria

- [ ] Constructor raises `RuntimeError` when any required service is `None`
- [ ] Test verifies error message includes the service name
- [ ] Existing callers reviewed for compatibility
- [ ] Docstring updated to clarify which services are optional vs required

## Out of scope

- Changes to the service initialization order in `factory.py`
- Changes to the type annotations
