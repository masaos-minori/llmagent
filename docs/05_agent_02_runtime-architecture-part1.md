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
            └─ ToolLoopGuard             — dedup/cycle/retry/error guards
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture-part2.md`

## Keywords

agent
runtime
architecture
lifecycle
