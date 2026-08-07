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

## Responsibility Boundary

### コンポーネント依存関係

``` text
AgentREPL (agent/repl.py)          — REPL coordinator; input loop + output only
   ├─ StartupOrchestrator (agent/startup.py) — startup sequence; created once in run()
   ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
   │    ├─ LLMClient            — SSE streaming, retry
   │    ├─ ToolExecutor         — MCP routing, TTL cache
   │    ├─ HistoryManager       — char counting, LLM compression
   │    └─ ServerLifecycleRouter — HTTP subprocess lifecycle
   ├─ CLIView (agent/cli_view.py)    — readline, progress display, multiline input
   └─ Orchestrator (agent/orchestrator.py) — turn-level facade
        └─ LLMTurnRunner             — SSE stream + inner tool-call loop
```

### 責務境界の補足

- `AgentContext`は共有される可変状態とコンポーネント参照のハブ。`factory.build_agent_context()`が
  すべてのサービスを注入する。
- `Orchestrator`は1回のユーザーターンをエンドツーエンドで処理し、LLMストリーミングとツールループを
  `LLMTurnRunner`に委譲する。
- `AppServices.lifecycle`の実行時実装は`agent/factory.py`内に定義されており、HTTPサブプロセスの
  起動・終了は`agent/http_lifecycle.py`に委譲される。

## Key Constraints

- `Orchestrator.__init__()`は`WorkflowLoader().load()`でワークフロー定義を読み込み、失敗時は
  `RuntimeError`を送出する（起動が止まる）。
- MCPサブプロセス起動後に例外が発生した場合、起動済みのMCPサブプロセスはロールバックされる。
- 副作用検出: write/delete/shell_runが含まれる場合、並列ツール呼び出しを直列化する。

## Operational Notes

- `AgentContext.diagnostics`は上図に含まれていなかった属性で、`Orchestrator.__init__()`実行後に
  設定される。
- `handle_turn()`はワークフローエンジン経由でplan/execute/verifyステージを実行する。
  `ctx.workflow.approval_pending`がTrueの間、およびバックグラウンドタスクが一時停止中の間は
  新規ターンを拒否する。（詳細は[05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)参照）

## Known Limitations

- バックグラウンドタスクの失敗閾値到達時通知と一時停止機構はオプトイン（既定無効）。（詳細は
  [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)参照）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture-part2.md`

## Keywords

agent
runtime
architecture
lifecycle
