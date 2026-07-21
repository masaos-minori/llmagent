# Issue: context.py - AppServices.gateway field inconsistent between docstring and implementation

## 概要

`AppServices.gateway` フィールドについて、docstringでは「None until factory.py constructs and injects RepositoryGateway」と説明されているが、`build_agent_context()` では常に `gateway=gateway` が渡される。docstringと実装の不一致。

## 該当コード

`scripts/agent/context.py:127-161`

```python
class AppServices:
    """Fully-initialized service references built by factory.py.

    All required services are non-None.  memory is None when
    use_memory_layer=False (intentionally absent, not uninitialised).
    gateway is None until factory.py constructs and injects RepositoryGateway.  # ← この説明
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        llm: LLMClient,
        tools: ToolExecutor,
        lifecycle: LifecycleManagerProtocol,
        hist_mgr: HistoryManager,
        audit_logger: Logger,
        memory: MemoryServices | None,
        health_registry: McpServerHealthRegistry | None = None,
        gateway: RepositoryGateway | None = None,  # ← optional parameter
        runtime_tools: RuntimeToolRegistry | None = None,
    ) -> None:
        self.gateway: RepositoryGateway | None = gateway
```

`scripts/agent/factory.py:432`:

```python
ctx.services = AppServices(
    http=http,
    llm=llm,
    tools=tools,
    lifecycle=lifecycle,
    hist_mgr=hist_mgr,
    audit_logger=audit_logger,
    memory=memory,
    health_registry=health_registry,
    gateway=gateway,  # ← always passed
)
```

## 問題点

- docstringの説明が古く、現在は常に `gateway` が注入される
- `gateway` がoptional parameterになっているのは、過去のAPIの名残の可能性
- `ctx.services_required.gateway` のアクセスで `None` チェックが必要になるが、それは不要
- 将来のAPI変更で `gateway=None` が意図せず混入するリスク

## 改善案

- docstringを更新して、`gateway` は常に存在することを明記
- または、`gateway` をrequiredパラメータに変更し、`None` の場合のみ例外を送出

```python
class AppServices:
    """All required services are non-None. memory is None when use_memory_layer=False."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        llm: LLMClient,
        tools: ToolExecutor,
        lifecycle: LifecycleManagerProtocol,
        hist_mgr: HistoryManager,
        audit_logger: Logger,
        memory: MemoryServices | None,
        health_registry: McpServerHealthRegistry | None = None,
        gateway: RepositoryGateway,  # ← required
        runtime_tools: RuntimeToolRegistry | None = None,
    ) -> None:
        assert gateway is not None
        self.gateway = gateway
```

## 優先度

低 - 現在の実装では問題ないが、ドキュメントと実装の不一致は保守性を低下させる
