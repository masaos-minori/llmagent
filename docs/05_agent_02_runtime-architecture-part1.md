---
title: "Agent Runtime Architecture (Part 1)"
category: agent
tags:
  - agent
  - runtime
  - architecture
  - lifecycle
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_02_runtime-architecture-part1.md
---

# Agent Runtime Architecture

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

主要なランタイムコンポーネント、それらの依存関係、および責務境界を記述し、
エンジニアやAIがどの振る舞いがどこに実装されているかを特定できるようにする。

> **本章の対象範囲:** ランタイムの振る舞い、モジュールグラフ、データフロー、コンポーネントのライフサイクル。
> 関数シグネチャ、パラメータ型、戻り値については → [05_agent_13 §Reference API](05_agent_13_reference-api-part1.md)を参照。

---

## Component Dependency Diagram

```
agent/__main__.py
  └─ AgentREPL (agent/repl.py)          — REPL coordinator; input loop + output only
       ├─ StartupOrchestrator (agent/startup.py) — startup sequence; created once in run()
       ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
       │    ├─ AgentConfig               — hot-reloadable runtime configuration
       │    ├─ AgentSession              — SQLite session/message persistence
       │    ├─ ConversationState         — history list, LLM URL, flags
       │    ├─ TurnState                 — current turn UUID (reset per turn)
       │    ├─ RuntimeStats              — cumulative session metrics
       │    ├─ WorkflowState             — active task ID, approval_pending flag (transient)
       │    └─ AppServices               — all service references (injected by factory.py)
       │         ├─ LLMClient            — SSE streaming, retry
       │         ├─ ToolExecutor         — MCP routing, TTL cache
       │         ├─ HistoryManager       — char counting, LLM compression
       │         ├─ ServerLifecycleRouter — HTTP subprocess lifecycle
       │         ├─ audit_logger         — JSON-lines audit.log writer
       │         └─ MemoryServices?      — optional semantic memory layer
       ├─ CLIView (agent/cli_view.py)    — readline, progress display, multiline input
       ├─ CommandRegistry                — all /cmd dispatch (10 mixins)
       └─ Orchestrator (agent/orchestrator.py) — turn-level facade
            ├─ LLMTurnRunner             — SSE stream + inner tool-call loop
            ├─ ToolLoopGuard             — dedup/cycle/retry/error guards
            ├─ WorkflowDef (agent/workflow/) — plan/execute/verifyの3ステージ定義。ロード失敗時は起動時RuntimeError
            └─ DiagnosticStore           — ctx.diagnosticsに束縛されるターン診断ストア
```

### Current behavior (依存グラフの補足)

- `Orchestrator.__init__()`は`WorkflowLoader().load()`で`WorkflowDef`を読み込み、失敗時は
  `RuntimeError`を送出する(起動が止まる)。各ターンは`WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn)`
  経由で実行される。(Explicit in code)
- `AppServices.lifecycle`の実行時実装(`LifecycleManagerProtocol`準拠)は`agent/factory.py`内に定義されており、
  HTTPサブプロセスの起動・終了は`agent/http_lifecycle.py`の`HttpServerLifecycleManager`に委譲される。
  クラス名はプライベート命名のため本書では割愛する。(Explicit in code)
- `AgentContext.diagnostics`(`DiagnosticStore | None`)は上図に含まれていなかった属性で、
  `Orchestrator.__init__()`実行後にのみ設定される。(Explicit in code)

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture-part2.md`

## Keywords

agent
runtime
architecture
lifecycle
