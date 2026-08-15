---
title: "Shared Runtime and Execution - Tool Runtime"
category: shared
tags:
  - shared
  - runtime
  - token-counter
  - otel-tracer
  - git-helper
  - tool-executor
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 4. `ToolExecutor` (`shared/tool_executor.py`, `shared/tool_executor_helpers.py`)

ToolExecutor は ToolTransportInvoker を継承し、http client/cache_ttl/server_configs/オプションパラメータを受け取るコンストラクタを持つ。apply_config() はホットリロード可能。execute() はキャッシュ参照→同時実行保護→ヘルスチェックゲート→transport解決→per-server semaphore実行→成功結果のみキャッシュの順序で実行。clear_cache()/get_error_counters() は状態管理。キャッシュは失敗結果を保存しない。

補助関数: `is_side_effect()` は WRITE_TOOLS/DELETE_TOOLS/shell_run/GIT_WRITE_TOOLS/GITHUB_WRITE_TOOLS/GITHUB_DANGEROUS_TOOLS に属するツールを判定する（本モジュール内では TTL キャッシュのバイパス判定にのみ用いる）。ツール呼び出しバッチの並列/直列判定は唯一の実行パスである `agent/tool_runner.py::_execute_with_dag()` が `agent/tool_scheduler.py::build_execution_groups()` に委譲して行い、こちらは `RuntimeToolRegistry` 登録済みの `is_write`（`PreparedToolCall.spec`経由）を参照する（`is_side_effect()`とは無関係な別経路 — [90_shared_03_03](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md)参照）。`format_transport_error()` は TransportErrorInfo を生成。`tool_hash_key()` は MD5 ハッシュを返すがキャッシュキーには使われず失敗追跡用途専用。

---

## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (ツール所有権とルーティング)

**責務分離 (Explicit in code — module docstring):**
- `shared/runtime_tool_registry.py`: **ルーティング権威**（唯一の解決元）。McpToolDiscoveryService によりライブ `/v1/tools` discovery で構築され、`ToolExecutor.set_runtime_registry()` で接続される
- `shared/tool_registry.py`: **ドリフト検出用の入力**（ルーティングには使われない）。`tool_constants.py` の frozenset群がインポート時にこのレジストリへ登録される
- `shared/route_resolver.py`: `ToolRouteResolver` — ツール名→server_key解決。**RuntimeToolRegistry のみを参照して解決する。未解決のツール名は即座に `ValueError`**
- `shared/tool_routing_validation.py`: config / live `/v1/tools` 応答とレジストリの整合性検証 (ドリフト検出専用。ルーティングには使わない)

### `ToolRegistry` (`shared/tool_registry.py`)

ToolRegistry は ToolDefinition オブジェクトを登録し、ツール名の所有サーバー解決、サーバー別/全ツール名の取得、config/live ツール名の整合性検証を行う。get_registry() はグローバルシングルトンを返し、初回呼び出し時に tool_constants から自動登録される。

ToolDefinition.description / input_schema は**予約フィールドで現状未使用**。LLM向けツールスキーマは各サーバーの `tools.py` の TOOL_LIST が正本。デフォルト登録は tool_constants.py の READ_TOOLS/WRITE_TOOLS/DELETE_TOOLS/RAG_TOOLS/CICD_TOOLS/MDQ_TOOLS/GIT_TOOLS/SHELL_TOOLS/GITHUB_TOOLS/WEB_SEARCH_TOOLS を対応するserver_keyに登録する。

### `ToolRouteResolver` (`shared/route_resolver.py`)

Resolves tool_name → server_key using RuntimeToolRegistry as sole authority; raises ValueError for unresolved names. server_configs accepted for backward compatibility but unused; discovery_map diagnostic-only; known_tools not passed in production.

**Current behavior:**
- `server_configs` is constructor parameter only for backward compatibility — never read or stored
- `runtime_registry` takes priority in resolve() when set
- `discovery_map` is a diagnostic-only feature not called from anywhere in production
- No production calls pass `known_tools`; startup coverage logging is effectively dead code

### Validation functions (`shared/tool_routing_validation.py`)

validate_routing_against_config/live/all return empty dict meaning no drift. check_tool_safety_tiers/check_unknown_tool_safety_tiers short-circuit when tool_safety_tiers is empty/unset (opt-in feature).

## 4b. `LifecycleProtocol` (`shared/tool_lifecycle.py`)

```python
@runtime_checkable
class LifecycleProtocol(Protocol):
    async def ensure_ready(self, server_key: str) -> None
```
- `ToolExecutor` に注入されるライフサイクル管理者の最小プロトコル。実装は `MCPServer` 側のライフサイクルマネージャ (詳細は MCP系ドキュメント参照)

---

## 5. `token_counter` (`shared/token_counter.py`)

POST {tokenize_url}/tokenize for exact count (is_exact=True); falls back to category-based character-to-token estimation (text: 4.0, tool_calls: 2.5, system: 3.5) returning estimated count (is_exact=False). Connection errors silently fall back.

カテゴリ別推定は旧来の chars // 4 ヒューリスティックを置き換え、多言語テキストと構造化ツールペイロードでの精度を高めたもの。トークン推定は (total_tokens, breakdown: dict[str, int]) をカテゴリ別カウント付きで返す。

---

## 6. `otel_tracer` (`shared/otel_tracer.py`)

build_tracer returns NoOp stub when enabled=False; ConsoleSpanExporter when otlp_endpoint empty; OTLP HTTP exporter when endpoint set. Uses private TracerProvider — does not touch global OTel provider.

---

## 7. `git_helper` (`shared/git_helper.py`)

get_repo_info returns RepoInfoResult(success, data dict with branch/commit(8-char)/message/author, failure_reason). Returns None on any error. ImportError caught separately; GitPython/GitError/OSError/AttributeError=ValueError individually caught.

---

## 8. `formatters` (`shared/formatters.py`)

truncate(text, max_chars) truncates text; fmt_kvlog(op, **kwargs) formats key=value log string; fmt_size(size) formats human-readable size; fmt_md_link(text, url) formats markdown link; MAX_SNIPPET_CHARS constant for snippet display limit.

---
