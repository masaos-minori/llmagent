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

# Agent Reference API — Part 1

## Purpose

役割、主要な公開 API、呼び出し元、呼び出し先、関連する設定、失敗時の動作を含む、
モジュールごとの簡潔な API リファレンス。完全なメソッドシグネチャはリンク先の各章を参照。

> **本章の範囲:** 関数シグネチャ、パラメータ型、戻り値、エラー条件。
> コンポーネントのコンテキスト、データフロー、実行時の動作については → [05_agent_02 §Runtime Architecture](05_agent_02_runtime-architecture-part1.md) を参照。

## Design Intent

API レファレンスは「API は何か」「どのように動作するか」に焦点を当てる。「なぜこの API がこのように設計されたか」は設計文書の範囲である。

## Responsibility Boundary

- このファイルが所有するもの: 関数シグネチャ、パラメータ型、戻り値、エラー条件
- このファイルが所有しないもの: コンポーネントのコンテキスト、データフロー、実行時の動作

## Key Constraints

- API レファレンスの詳細は Canonical Source Rule で定められた正本にのみ存在する
- 他章での API/type/method 詳細の重複は禁止（Canonical Source Rule）
- 不完全な実装変更は `Needs Confirmation` マークで明示する

## Operational Notes

- REPL ループドライバからの呼び出しは常に `await` 形式
- 失敗時はエラー種別ごとに異なるフォールバック動作が存在する
- メモリレイヤーはオプションであり、`ctx.services.memory is None` の場合に安全にガードできる設計になっている

## Known Limitations

- 一部の呼び出し先は間接的な依存関係を含んでいる（例: `factory.build_agent_context()` は `StartupOrchestrator` を経由して呼ばれる）
- 旧版ドキュメントと現行コードの差分は `Needs Confirmation` マークで明示されている

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_13_reference-api-part2.md`

---

## AgentREPL（`agent/repl.py`）

- **役割:** REPL コーディネーター。薄い起動／ループドライバ
- **主要な API:** `await AgentREPL().run()`
- **呼び出し元:** `agent/__main__.py`
- **呼び出し先:** `agent/startup.StartupOrchestrator`（`run()` 内で構築・実行し、`CommandRegistry` と `Orchestrator` を受け取る）、`CLIView`
- **設定:** `AgentConfig` 全体
- **失敗時:** 未処理の例外はイベントループに伝播する。`finally` は常にリソースをクローズする

完全な詳細: [05_agent_02_runtime-architecture-part1.md §AgentREPL](05_agent_02_runtime-architecture-part1.md)

---

## Orchestrator（`agent/orchestrator.py`）

- **役割:** ターンレベルのファサード。メモリ注入 → 圧縮 → LLM → ツールループを管理する
- **主要な API:** `await Orchestrator.handle_turn(line)`、`workflow_status() -> dict[str, str]`
- **呼び出し元:** REPL ループドライバ
- **呼び出し先:** `LLMTurnRunner`、`HistoryManager`（`ctx.services_required.hist_mgr.compress()`）、`AgentSession`、`MemoryServices`（`ctx.services_required.memory.on_user_prompt()`）、`WorkflowEngine` / `StateStore` / `WorkflowLoader`（`agent/workflow/`）、`ToolLoopGuard`
- **設定:** `cfg.llm.*`、`cfg.tool.*`、`cfg.memory.*`
- **失敗時:** `LLMTransportError` は内部で捕捉される。REPL は継続する。`__init__()` 時点で `WorkflowLoader().load()` が失敗すると `RuntimeError` を送出し、`Orchestrator` 自体の構築が失敗する（ワークフロー定義は必須）

完全な詳細: [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

---

## AgentContext（`agent/context.py`）

- **役割:** セッションごとの DI ハブ。共有される可変状態のコンテナ
- **主要な API:** `ctx.conv`、`ctx.turn`、`ctx.stats`、`ctx.workflow`、`ctx.cfg`、`ctx.session`、`ctx.services`、`ctx.diagnostics`、`ctx.services_required`
- **呼び出し元:** すべてのコンポーネント
- **呼び出し先:** なし（純粋な状態保持クラス）
- **設定:** `AgentConfig` が `ctx.cfg` として保持される
- **失敗時:** `ctx.services_required`（プロパティ）は `ctx.services` が `None`（`factory.build_agent_context()` 完了前）の場合に `RuntimeError` を送出する。`ctx.services` 自体への直接アクセスは失敗しない（`None` を返すのみ）

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

- **役割:** `RuntimeToolRegistry`（`shared/runtime_tool_registry.py`、McpToolDiscoveryService によりライブ `/v1/tools` discovery で構築）を**唯一のルーティング権威**として `tool_name → server_key` を解決する
- **主要な API:** `resolve(tool_name) -> server_key`
- **呼び出し元:** ツール実行層（`ToolExecutor._raw_execute`）
- **呼び出し先:** なし（`RuntimeToolRegistry` インスタンスを参照するのみ。`ToolRegistry` には一切触れない）
- **設定:** 直接の設定なし。コンストラクタは `server_configs` を後方互換のために受け取るが読み取らない
- **失敗時:** ツール名がレジストリに見つからない場合、フォールバックなしで即時 `ValueError` を発生させる

> **根拠分類: Explicit in code（訂正）。** 旧版は「4層カスケード（live discovery > ToolRegistry > config `tool_names` > 静的定数）」
> および失敗時 `KeyError` と記載していたが、その後 `shared/route_resolver.py::ToolRouteResolver.resolve()`
> の実装が `ToolRegistry` のみを参照し、一致しない場合は `ValueError` を送出する形に一度修正された。
> しかし現行コードはさらに `RuntimeToolRegistry`（`shared/runtime_tool_registry.py`）への移行を経ており、
> `resolve()` は起動時のライブ `/v1/tools` discovery から構築された `RuntimeToolRegistry.resolve()` のみを参照する。
> `ToolRegistry` はドリフト検出用のシードデータに格下げされ、ルーティング判断には一切使われない。
> config `tool_names` はドリフト検証メタデータに過ぎず、ルーティングの入力ではない。
> `04_mcp_03_01_dispatch-and-routing.md` §ルーティングの信頼できる情報源 は既にこの実装内容に追随済みであり、
> 本ファイルのみ旧記述が残っていたため修正した。

完全な詳細: [04_mcp_03_01_dispatch-and-routing.md §ルーティングの信頼できる情報源](04_mcp_03_01_dispatch-and-routing.md)
