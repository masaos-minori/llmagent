---
title: "Agent Configuration - Loading and AgentConfig Structure (Part 2)"
category: agent
tags:
  - agent
  - configuration
  - config-loading
  - agentconfig
  - hot-reload
related:
  - 05_agent_00_document-guide.md
  - 05_agent_08_02_configuration-llm-rag.md
  - 05_agent_08_03_configuration-tools-memory.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## AgentConfig構造

`AgentConfig`は`cfg.llm.*`, `cfg.rag.*`などとしてアクセスされる7つのドメインサブ設定と、
2つのトップレベルのスカラーフィールドで構成される。

```python
@dataclass
class AgentConfig:
    llm:      LLMConfig
    rag:      RAGConfig
    tool:     ToolConfig
    memory:   MemoryConfig
    mcp:      MCPConfig
    approval: ApprovalConfig
    obs:      ObservabilityConfig
    security_lockdown_enabled:  bool = False
```

`security_lockdown_enabled`は、意図的なロックダウン運用のためDENY-ALL承認警告を抑制する。

**`workflow_mode`と`workflow_require_approval`はもはや存在しない** (2026-07-09に
`scripts/agent/config_dataclasses.py::AgentConfig`に対して検証済み — いずれのフィールドも存在しない)。
両キーとも設定読み込み時に拒否されるようになった: マージされた設定のどこかに
いずれかが出現した場合、`build_agent_config()`は`ConfigLoadError`を発生させる
(`_FORBIDDEN_KEYS = {"workflow_mode", "workflow_require_approval", "use_tool_summarize",
"tool_summarize_threshold"}`)。"auto" / "disabled"の縮退モードは存在せず、
ワークフローレベルの承認ゲートの切り替えも存在しない — 次節を参照。

**現在の挙動:** エージェントは無条件に有効なワークフロー定義を要求する。
`StartupOrchestrator._initialize()`は、`Orchestrator.__init__()`の**前**の
プレフライトチェックとして`_check_workflow_definition()`
(`agent/startup.py:84`、`agent/repl_health.py`内の`check_workflow_definition()`をラップ)
を呼び出す; `config/workflows/default.json`が存在しない場合、期待されるパスを明記した
実行可能なメッセージと共に`RuntimeError`を発生させる。`Orchestrator.__init__()`自体
(`agent/orchestrator.py:123-129`) はその後無条件に`WorkflowLoader().load()`を呼び出し、
いかなる失敗 (`WorkflowLoadError`など) に対しても`RuntimeError`を発生させる — これを
スキップまたは縮退させるモードは存在しない。いずれのチェックも`StartupOrchestrator.run()`
によって捕捉されない; 失敗はREPLに伝播し、起動を中止させる。この失敗はエージェント起動時に
発生するものであり、最初のターンで発生するものではない。これが「起動時のみ」であるのは、
常に起動時に一度だけ実行されるという意味であり、単にホットリロードできない設定トグルだからではない。

フィールド間の検証:
- `rag.use_semantic_cache=True` → `rag.embed_url`は非空である必要がある
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir`は非空である必要がある
- `memory.memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`

## Keywords

configuration loading
config file ownership
hot-reload eligibility
reload execution pipeline
AgentConfig structure
