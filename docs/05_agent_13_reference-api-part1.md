---
title: "Agent Reference API (Part 1)"
category: agent
tags:
  - agent
  - reference
  - api
  - types
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_13_reference-api-part1.md
---

# Agent Reference API

- ドキュメントガイド → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## 目的

役割、主要な公開 API、呼び出し元、呼び出し先、関連する設定、失敗時の動作を含む、
モジュールごとの簡潔な API リファレンス。完全なメソッドシグネチャはリンク先の各章を参照。

> **本章の範囲:** 関数シグネチャ、パラメータ型、戻り値、エラー条件。
> コンポーネントのコンテキスト、データフロー、実行時の動作については → [05_agent_02 §Runtime Architecture](05_agent_02_runtime-architecture-part1.md) を参照。

---

## AgentREPL（`agent/repl.py`）

- **役割:** REPL コーディネーター。薄い起動／ループドライバ
- **主要な API:** `await AgentREPL().run()`
- **呼び出し元:** `agent/__main__.py`
- **呼び出し先:** `Orchestrator`、`CommandRegistry`、`CLIView`、`factory.build_agent_context()`
- **設定:** `AgentConfig` 全体
- **失敗時:** 未処理の例外はイベントループに伝播する。`finally` は常にリソースをクローズする

完全な詳細: [05_agent_02_runtime-architecture-part1.md §AgentREPL](05_agent_02_runtime-architecture-part1.md)

---

## Orchestrator（`agent/orchestrator.py`）

- **役割:** ターンレベルのファサード。メモリ注入 → 圧縮 → LLM → ツールループを管理する
- **主要な API:** `await Orchestrator.handle_turn(line)`
- **呼び出し元:** REPL ループドライバ
- **呼び出し先:** `LLMTurnRunner`、`HistoryManager`、`AgentSession`、`MemoryInjectionService`
- **設定:** `cfg.llm.*`、`cfg.tool.*`、`cfg.memory.*`
- **失敗時:** `LLMTransportError` は内部で捕捉される。REPL は継続する

完全な詳細: [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

---

## AgentContext（`agent/context.py`）

- **役割:** セッションごとの DI ハブ。共有される可変状態のコンテナ
- **主要な API:** `ctx.conv`、`ctx.turn`、`ctx.stats`、`ctx.cfg`、`ctx.session`、`ctx.services`
- **呼び出し元:** すべてのコンポーネント
- **呼び出し先:** なし（純粋な状態保持クラス）
- **設定:** `AgentConfig` が `ctx.cfg` として保持される
- **失敗時:** 該当なし

完全な詳細: [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)

---

## LLMClient（`shared/llm_client.py`）

- **役割:** LLM との HTTP 通信。SSE ストリーミング＋リトライ
- **主要な API:** `await client.stream(url, history, tool_defs)`、`client.build_payload(...)`
- **呼び出し元:** `LLMTurnRunner`、`HistoryManager`（`call()` 経由）、`SessionTitleService`
- **呼び出し先:** `RobustSSEParser`、`httpx.AsyncClient`
- **設定:** `cfg.llm.*`
- **失敗時:** ストリーム失敗時に `partial_text` を伴う `LLMTransportError` を発生させる

完全な詳細: [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md)

---

## ToolExecutor（`shared/tool_executor.py`）

- **役割:** TTL キャッシュ、副作用の分類、並行数制限を伴う MCP ツールルーティング
- **主要な API:** `await executor.execute(tool_name, args) -> ToolCallResult`
- **呼び出し元:** `LLMTurnRunner`（`execute_all_tool_calls` 経由）
- **呼び出し先:** `ToolRouteResolver`、`HttpTransport`、`McpServerHealthRegistry`
- **設定:** `cfg.tool.*`、`cfg.mcp.*`
- **失敗時:** トランスポート失敗時に `ToolCallResult(is_error=True)` を返す

完全な詳細: [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md)

---

## ToolRouteResolver（`shared/route_resolver.py`）— ToolExecutor の内部コンポーネント

- **役割:** 4層構成のツール・サーバー間ルーティングカスケード（live discovery > ToolRegistry > config `tool_names` > 静的定数）
- **主要な API:** `resolve(tool_name) -> server_key`
- **呼び出し元:** ツール実行層
- **呼び出し先:** `McpServerHealthRegistry`、`LifecycleProtocol`（サーバー起動経由）
- **設定:** 直接の設定なし。優先順位に従って ToolRegistry、live discovery マップ、config `tool_names`、`tool_constants.py` の frozenset から読み取る
- **失敗時:** どの層でもツール名を解決できない場合に `KeyError` を発生させる

完全な詳細: [04_mcp_03 §Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md#routing-source-of-truth)

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_13_reference-api-part2.md`

## Keywords

agent
reference
api
types
