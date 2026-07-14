---
title: "Agent System Overview"
category: agent
tags:
  - agent
  - system
  - overview
  - architecture
related:
  - 05_agent_00_document-guide.md
---

# Agent System Overview

- ドキュメントガイド → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## Purpose

LLMのfunction callingを用いてMCPツールサーバーと対話し、マルチターンの会話履歴を維持し、
ターミナルに回答を返すCLI REPLインターフェースを提供する。

---

## Scope

**対象範囲:**
- CLI REPL (`python -m agent`、エントリポイント: `scripts/agent/__main__.py`)
- MCPツールサーバーとの通信(HTTP)
- SQLiteセッション永続化によるマルチターン会話
- スラッシュコマンドインターフェース
- SSEストリーミングによるLLM応答

**対象外:**
- RAGパイプライン内部(`scripts/mcp_servers/rag_pipeline/`がMCP経由でこれを担う)
- MCPサーバーの実装
- Embeddingサーバー

---

## Entry Point and Interaction Model

```
python -m agent   (scripts/agent/__main__.py)
  → asyncio.run(AgentREPL().run())
  → REPL loop: agent[:#N]> prompt
  → User text → LLM (SSE streaming) → tool_calls → MCP → answer
```

- プロンプト: `agent>` または `agent[:#N]>` (N = セッションID)
- 行編集: readline (bash互換のキーバインド)
- 履歴ファイル: `~/.agent_history`
- 複数行入力: 末尾の`\`で次の行へ継続、`...`プロンプトを表示

### Current behavior (差異)

- `agent/repl.py`の`AgentREPL._prompt`プロパティは常に`"> "`を返す。`agent>`/`agent[:#N]>`形式のプロンプトはコード上に見当たらない。(Explicit in code)
- 複数行継続時のプロンプトは`agent/cli_view.py`の`read_multiline()`で`"... "`固定。(Explicit in code)

---

## Overall Tool-Calling Model

```
[1] User enters question at REPL prompt
[2] User message + tool definitions → LLM (SSE streaming)
[3] LLM returns tool_calls → execute via MCP servers
[4] Tool results added as "tool" role messages → re-send to LLM
[5] Steps [3]–[4] repeat up to max_tool_turns (default 5)
[6] Final answer displayed; conversation history carried to next turn
```

MCPサーバーはHTTP POST `/v1/call_tool`経由で呼び出される。

### Current behavior (ワークフローエンジン経由の実行)

`agent/orchestrator.py`の`Orchestrator.handle_turn()`は、起動時に`WorkflowLoader().load()`で
読み込んだ`WorkflowDef`(`config/workflows/default.json`相当)を用い、各ユーザーターンを
`WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn)`の3ステージ(plan/execute/verify)として
実行する。上記の`[1]-[6]`のシンプルな模式図は`execute_fn`内で行われるLLMターン処理(メモリ注入 →
ユーザーメッセージ追加 → 履歴圧縮 → LLMターン)に相当する。ワークフロー定義のロードに失敗した場合、
`Orchestrator.__init__()`は`RuntimeError`を送出し起動が止まる。承認待ち(`ctx.workflow.approval_pending`)
中は新規ターンを受け付けず、`/approve`または`/reject`を促すエラーを返す。(Explicit in code)
詳細は`05_agent_03`系(turn processing flow)を参照。(Strongly implied by code — 本ドキュメントの管轄外のため詳細記述は行わない)

---

## High-Level Component Map

| Component | Class | File | Role |
|---|---|---|---|
| REPLコーディネーター | `AgentREPL` | `agent/repl.py` | 起動フローとREPLループを管理する |
| ターンオーケストレーション | `Orchestrator` | `agent/orchestrator.py` | メモリ注入 → 圧縮 → LLM → ツールループ |
| 共有状態 | `AgentContext` | `agent/context.py` | セッション単位のDIハブ |
| LLM通信 | `LLMClient` | `shared/llm_client.py` | SSEストリーミング、リトライ |
| ツールルーティング | `ToolExecutor` | `shared/tool_executor.py` | MCPルーティング、TTLキャッシュ |
| 履歴管理 | `HistoryManager` | `agent/history.py` | 文字数カウント、LLMによる圧縮 |
| スラッシュコマンド | `CommandRegistry` | `agent/commands/registry.py` | すべての`/cmd`ディスパッチ |
| CLI表示 | `CLIView` | `agent/cli_view.py` | readline、進捗表示、複数行入力 |
| セッション永続化 | `AgentSession` | `agent/session.py` | sessions/messages SQLite |
| 設定 | `AgentConfig` | `agent/config_dataclasses.py` | 7つのサブ設定、ホットリロード |
| メモリサービス | `MemoryServices` | `agent/memory/` | オプションのセマンティックメモリレイヤー |

---

## Session, SSE, and History Compression (Summary)

**セッション:** REPLを実行するたびにSQLiteにセッション行が作成される。メッセージはターンごとに
永続化される。`/session load <id>`で過去の会話を復元できる。

**SSEストリーミング:** LLMの応答はServer-Sent Eventsによりトークンごとにストリーミングされる。`LLMClient`が
再接続(`sse_reconnect_max`まで)、ハートビートタイムアウト、部分的な補完の処理を担う。

**履歴圧縮:** `ctx.conv.history`が`context_char_limit`(デフォルト
8000文字)を超えると、`HistoryManager.compress()`が最も古いターンをLLMで要約する。
直近の`history_protect_turns`(デフォルト2)ターンは常に保護される。

---

## Slash Command Categories (Summary)

> **本リストを最新に保つために:** 新しいコマンドを追加した場合は、本サマリーと[05_agent_07 §Slash Command Reference](05_agent_07_01_cli-and-commands-cli-reference.md)の完全な参照テーブルの両方を更新すること。手順の詳細は[05_agent_07 §Maintaining the Command List](05_agent_07_01_cli-and-commands-cli-reference.md)を参照。

| Category | Commands |
|---|---|
| セッション | `/session list\|load\|rename\|delete`, `/clear [new]`, `/undo`, `/history`, `/export` |
| MCP | `/mcp status` |
| 設定/統計 | `/config`, `/stats`, `/set`, `/reload` |
| コンテキスト | `/context`, `/compact`, `/system` |
| DB | `/db rag stats\|urls\|clean\|rebuild-fts\|vec-rebuild\|reconcile-url\|recover\|consistency; session stats\|health\|checkpoint\|vacuum\|purge\|recover` |
| プラン | `/plan` |
| ワークフロー | `/approve <approval_id> [reason]`, `/reject <approval_id> [reason]` |
| デバッグ/監査 | `/debug`, `/audit` |
| エクスポート/コンパクト | `/export`, `/compact` |
| メモリ | `/memory list\|search\|show\|pin\|unpin\|delete\|prune\|status` |
| プラグイン | `/plugin status` |
| MDQ | `/mdq status\|index\|refresh\|search\|outline\|get\|grep` |
| スキル | `/skill [name] [args]` |
| その他 | `/help` |

### Current behavior (コマンド一覧の相違)

`scripts/agent/commands/command_defs_list.py`の`_COMMANDS`(単一の正本)には上記に加え、
`_PluginsMixin`(`/plugin`)、`_MdqMixin`(`/mdq`)、`_SkillMixin`(`/skill`)が存在する。
一方`agent/repl.py`の`AgentREPL.SLASH_COMMANDS`(readlineタブ補完用リスト)には
`/plugin`、`/mdq`、`/skill`、`/memory`が含まれていない。タブ補完対象外という
挙動であり、コマンドとして無効という意味ではない。(Explicit in code)

---

## Major Constraints

| Constraint | Value |
|---|---|
| 1メッセージあたりの最大ツールターン数 | `max_tool_turns` (default 5) |
| 履歴圧縮の閾値 | `context_char_limit` (default 8000 chars) |
| HTTPタイムアウト | `http_timeout` (default 30.0 sec) |
| LLMリトライ上限 | `llm_max_retries` (default 3) |
| ツール結果キャッシュのTTL | `tool_cache_ttl` (default 300 sec) |

### Current behavior (MCP watchdog)

`ctx.cfg.mcp.mcp_watchdog_interval`が0より大きい場合、`AgentREPL`はバックグラウンドで
watchdogタスク(`agent/repl_health.py`の`watchdog_loop`)を起動する。0の場合はwatchdog無効。
本表には未記載の起動時パラメータであり、`mcp_watchdog_max_restarts`と併用される。
(Explicit in code — 挙動の詳細はrepl_health.pyの管轄)

---

## Related Chapters

| Topic | File |
|---|---|
| ランタイムコンポーネントアーキテクチャ | [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md) |
| ターン処理フロー | [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md) |
| 状態と永続化 | [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md) |
| LLMとストリーミング | [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) |
| ツール実行と承認 | [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) |
| CLIとコマンド | [05_agent_07_01_cli-and-commands-cli-reference.md](05_agent_07_01_cli-and-commands-cli-reference.md) |
| 設定 | [05_agent_08_01_configuration-loading-agent-config-part1.md](05_agent_08_01_configuration-loading-agent-config-part1.md) |
| データレイヤー | [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) |
| 運用と可観測性 | [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) |
| 拡張ポイント | [05_agent_11_01_extension-points-plugin-command.md](05_agent_11_01_extension-points-plugin-command.md) |
| APIリファレンス | [05_agent_13_reference-api-part1.md](05_agent_13_reference-api-part1.md) |

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
system
overview
architecture
