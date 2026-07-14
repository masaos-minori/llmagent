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

**`workflow_mode`と`workflow_require_approval`は有効なキーではない** (2026-07-09に
`scripts/agent/config_dataclasses.py::AgentConfig`に対して検証済み — いずれのフィールドも存在しない)。
両キーとも設定読み込み時に拒否される: `_FORBIDDEN_KEYS`に含まれ、マージされた設定に
いずれかが出現すると`ConfigLoadError`が発生する (`_FORBIDDEN_KEYS = {"workflow_mode",
"workflow_require_approval", "use_tool_summarize", "tool_summarize_threshold"}`)。

**現在の挙動:** エージェントは無条件に有効なワークフロー定義を要求する。
`StartupOrchestrator._initialize()`は、`Orchestrator.__init__()`の**前**に
2つのプレフライトチェックを順に呼び出す (`agent/startup.py:85-86`):
1. ワークフロー定義の存在チェック — `agent/repl_health.py`内の
   `check_workflow_definition()`をラップ。`config/workflows/default.json`が
   存在しない場合、期待されるパスを明記した実行可能なメッセージと共に
   `RuntimeError`を発生させる。
2. `_check_workflow_schema()` — `agent/repl_health.py`内の
   `check_workflow_schema()`をラップし、ワークフローDBスキーマを検証する。
   失敗時はログ出力の上`RuntimeError`を再送出する
   (根拠: Explicit in code — `agent/startup.py:156-164`)。

`Orchestrator.__init__()`自体 (`agent/orchestrator.py:126-132`) はその後無条件に
`WorkflowLoader().load()`を呼び出し、いかなる失敗 (`WorkflowLoadError`など) に対しても
`RuntimeError`を発生させる — これをスキップまたは縮退させるモードは存在しない。
いずれのチェックも`StartupOrchestrator.run()`によって捕捉されない; 失敗はREPLに伝播し、
起動を中止させる。この失敗はエージェント起動時に発生するものであり、最初のターンで
発生するものではない。これが「起動時のみ」であるのは、常に起動時に一度だけ実行される
という意味であり、単にホットリロードできない設定トグルだからではない。

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
