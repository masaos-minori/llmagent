
title: "Shared Types and Protocols - Tool and Execution DTOs (Part 1)"
category: shared
tags:
  - shared
  - types
  - tool-dto
  - action-result
  - tool-spec
  - cache
  - events
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_03_types_and_protocols-reference.md
source:
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto.md


# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 6. `LLMUsage` / `LLMResponse` (`shared/llm_types.py`)

`LLMUsage` (prompt_tokens, completion_tokens — トークン計測用)、`LLMResponse` (message, finish_reason, usage) — トークン計測 + レスポンス包囲。呼び出し元が `LLMClient` をインポートせずに DTO をインポートできるよう `llm_client.py` から分離。(Explicit in code)

Import: `from shared.llm_types import LLMUsage, LLMResponse`

---

## 6a. `ToolCallResult` / `TransportErrorInfo` (`shared/transport_dto.py`)

`ToolCallResult` はすべてのツール呼び出し実行 (transport, cache) における正規の結果契約 — 出力/エラーメタデータ、トランスポート情報、監査情報を含む。`source` フィールドは呼び出し元の種別(`"mcp"`/`"cache"`)を区別する。(Explicit in code: `scripts/shared/transport_dto.py`)

`TransportErrorInfo` はオーディットログ用の構造化エラー情報として使われる。

Import: `from shared.transport_dto import ToolCallResult, TransportErrorInfo`

---

## 7. `ActionResult` (`shared/action_result.py`)

`ActionType` enum (`continue`/`call_tool`/`retrieve_more_context`/`ask_user`/`fail`/`retry`) と frozen dataclass (`reason`, `required_context`, `payload`, `errors`, `confidence`) — エージェントのアクションルーティング用の汎用的な機械判定スキーマ。(Explicit in code)

---

## 7a. `ToolSpec` (`shared/tool_spec.py`)

実行メタデータ (call_id, name, args, resource_scopes（kind接頭辞付きスコープ文字列のタプル）, requires_serial, is_write) — DAG スケジューリングで使用される。`resource_scopes` は呼び出しごとに `shared/resource_scope.py::resolve_resource_scopes()` で解決される。実際のスケジューリングロジックは `agent/tool_scheduler.py` にある。(Explicit in code: `scripts/agent/tool_scheduler.py`)

Import: `from shared.tool_spec import ToolSpec`

---

## 7b. `CacheEntry` / `ToolResultCache` (`shared/tool_cache.py`)

`CacheEntry` (output, is_error, cached_at) — LRU+TTL キャッシュユーティリティ。現在 ToolExecutor では使用されておらず、将来のスタンプデ対策なしでの再利用のために保持。(Explicit in code)

---

## 7c. `RuntimeTool` (`shared/runtime_tool.py`)

15フィールドの正規化されたツール実行メタデータ (ルーティング、LLMスキーマ、スケジューラメタデータ、副作用検出、安全性ティア、承認要否、引数バリデーションの緩和フラグ) を1つの型で表現。`AgentSafetyTier` の4値 (`READ_ONLY`/`WRITE_SAFE`/`WRITE_DANGEROUS`/`ADMIN`) は `shared-is-leaf` インポート制約のため `agent.tool_enums` からインポートせず、本モジュール内でローカルな `Literal` 型として重複定義。(Explicit in code)

`build_runtime_tool()` は未指定の注釈フィールドに安全側のデフォルトを適用する。`allow_extra_fields` はツール単位のフラグで、`agent/tool_preparation.py` の準備フェーズ（`prepare_tool_calls()`/`_prepare_one()`、承認より前に実行される）が読み取り、`agent/tool_arg_validator.py` の `validate_tool_arguments()` に渡す。(Explicit in code)

**web_search-mcp の `browser_fetch` ツールが `config_dependent: True` を採用したことで、`RuntimeTool` / `build_runtime_tool()` が初めて実データで使用されている。**

Import: `from shared.runtime_tool import RuntimeTool, build_runtime_tool, AgentSafetyTier`

---

## 7d. `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`)

`{name: RuntimeTool}` を保持するインメモリレジストリ。`resolve()` は未登録名に対して `None` を返し、`get()` は `KeyError` を送出 — 「登録済みだが注釈不足」と「レジストリに存在しない」を区別する設計。(Explicit in code)

`classify_operation_type()` は `Literal["read", "write"]` を返す — `shared-is-leaf` インポート制約により `agent.tool_enums` はインポートしない。(Explicit in code)

`apply_policy()` はプレーンな `tier_map: Mapping[str, AgentSafetyTier]` と `allowed_tools: Sequence[str] = ()` を受け取る（同じく `shared-is-leaf` 制約のため）。(Explicit in code)

`is_side_effect()` は `shared.tool_executor_helpers.is_side_effect()`（`_SIDE_EFFECT_TOOLS` frozenset ベース）を置き換えるものではなく、意図的に並行して重複させた実装（登録済み `RuntimeTool.is_write` を参照する）。(Explicit in code)

**MCP ディスカバリ（`McpToolDiscoveryService`）がレジストリを実データで投入し、`ToolExecutor.set_runtime_registry()` で接続済み。**

Import: `from shared.runtime_tool_registry import RuntimeToolRegistry`

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 6a. `LLMUsage` / `LLMResponse` (`shared/llm_types.py`)

`LLMUsage` (prompt_tokens, completion_tokens — トークン計測用)、`LLMResponse` (message, finish_reason, usage) — トークン計測 + レスポンス包囲。呼び出し元が `LLMClient` をインポートせずに DTO をインポートできるよう `llm_client.py` から分離。(Explicit in code)

Import: `from shared.llm_types import LLMUsage, LLMResponse`

---

## 6a. `ToolCallResult` / `TransportErrorInfo` (`shared/transport_dto.py`)

`ToolCallResult` はすべてのツール呼び出し実行 (transport, cache) における正規の結果契約 — 出力/エラーメタデータ、トランスポート情報、監査情報を含む。`source` フィールドは呼び出し元の種別(`"mcp"`/`"cache"`)を区別する。(Explicit in code: `scripts/shared/transport_dto.py`)

`TransportErrorInfo` はオーディットログ用の構造化エラー情報として使われる。

Import: `from shared.transport_dto import ToolCallResult, TransportErrorInfo`

---

## 7a. `ActionResult` (`shared/action_result.py`)

`ActionType` enum (`continue`/`call_tool`/`retrieve_more_context`/`ask_user`/`fail`/`retry`) と frozen dataclass (`reason`, `required_context`, `payload`, `errors`, `confidence`) — エージェントのアクションルーティング用の汎用的な機械判定スキーマ。(Explicit in code)

---

## 7a. `ToolSpec` (`shared/tool_spec.py`)

実行メタデータ (call_id, name, args, resource_scopes（kind接頭辞付きスコープ文字列のタプル）, requires_serial, is_write) — DAG スケジューリングで使用される。`resource_scopes` は呼び出しごとに `shared/resource_scope.py::resolve_resource_scopes()` で解決される。実際のスケジューリングロジックは `agent/tool_scheduler.py` にある。(Explicit in code: `scripts/agent/tool_scheduler.py`)

Import: `from shared.tool_spec import ToolSpec`

---

## 7b. `CacheEntry` / `ToolResultCache` (`shared/tool_cache.py`)

`CacheEntry` (output, is_error, cached_at) — LRU+TTL キャッシュユーティリティ。現在 ToolExecutor では使用されておらず、将来のスタンプデ対策なしでの再利用のために保持。(Explicit in code)

---

## 7c. `RuntimeTool` (`shared/runtime_tool.py`)

15フィールドの正規化されたツール実行メタデータ (ルーティング、LLMスキーマ、スケジューラメタデータ、副作用検出、安全性ティア、承認要否、引数バリデーションの緩和フラグ) を1つの型で表現。`AgentSafetyTier` の4値 (`READ_ONLY`/`WRITE_SAFE`/`WRITE_DANGEROUS`/`ADMIN`) は `shared-is-leaf` インポート制約のため `agent.tool_enums` からインポートせず、本モジュール内でローカルな `Literal` 型として重複定義。(Explicit in code)

`build_runtime_tool()` は未指定の注釈フィールドに安全側のデフォルトを適用する。`allow_extra_fields` はツール単位のフラグで、`agent/tool_preparation.py` の準備フェーズ（`prepare_tool_calls()`/`_prepare_one()`、承認より前に実行される）が読み取り、`agent/tool_arg_validator.py` の `validate_tool_arguments()` に渡す。(Explicit in code)

**web_search-mcp の `browser_fetch` ツールが `config_dependent: True` を採用したことで、`RuntimeTool` / `build_runtime_tool()` が初めて実データで使用されている。**

Import: `from shared.runtime_tool import RuntimeTool, build_runtime_tool, AgentSafetyTier`

---

## 7d. `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`)

`{name: RuntimeTool}` を保持するインメモリレジストリ。`resolve()` は未登録名に対して `None` を返し、`get()` は `KeyError` を送出 — 「登録済みだが注釈不足」と「レジストリに存在しない」を区別する設計。(Explicit in code)

`classify_operation_type()` は `Literal["read", "write"]` を返す — `shared-is-leaf` インポート制約により `agent.tool_enums` はインポートしない。(Explicit in code)

`apply_policy()` はプレーンな `tier_map: Mapping[str, AgentSafetyTier]` と `allowed_tools: Sequence[str] = ()` を受け取る（同じく `shared-is-leaf` 制約のため）。(Explicit in code)

`is_side_effect()` は `shared.tool_executor_helpers.is_side_effect()`（`_SIDE_EFFECT_TOOLS` frozenset ベース）を置き換えるものではなく、意図的に並行して重複させた実装（登録済み `RuntimeTool.is_write` を参照する）。(Explicit in code)

**MCP ディスカバリ（`McpToolDiscoveryService`）がレジストリを実データで投入し、`ToolExecutor.set_runtime_registry()` で接続済み。**

Import: `from shared.runtime_tool_registry import RuntimeToolRegistry`

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`



# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 7c. `ToolDefinition` (`shared/tool_registry.py`)

不変のツール定義 — 1 つのツールは必ず 1 つの MCP サーバーに属する。(Explicit in code: `scripts/shared/tool_registry.py` docstring)

**境界条件:** `description` と `input_schema` は将来利用のための予約フィールドであり、デフォルトレジストリ初期化関数では一切設定されず、現状どの呼び出し元からも読まれない。LLMに見せるツールスキーマは各サーバー自身の `tools.py` の `TOOL_LIST` が情報源であり、この `ToolRegistry` からではない。(Explicit in code)

`ToolRegistry` はツールの所有権・ルーティングのみを扱う。ライブ `/v1/tools` の応答は起動時のドリフト検証にのみ使われ、ルーティング判断には使われない。(Explicit in code)

Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

`ArtifactEvent` (event_type, repo, branch, commit, path, pr_number, session_id, timestamp) — リポジトリアーティファクト作成/更新時に発行。(Explicit in code: `scripts/shared/events.py` モジュールdocstring)

> **Note:** `ArtifactEvent` は純粋なデータ構造(`TypedDict`)である。配信の仕組み・イベントバス・購読者は一切存在しない。将来的にアーティファクトイベントを発行しうるコードのための型注釈としてのみ存在する。`ArtifactEvent` のインスタンス生成が何らかのアクションをトリガーすると仮定してはならない。

`RetryEvent` (event_type, workflow_id, task_id, attempt_number, max_attempts, error_type, backoff_sec, session_id, timestamp) — ワークフローステージのリトライ時に発行。

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

不変の `frozen=True` dataclass — FastAPI、MCP、エージェントへの依存はない(shared → external のみ)。`mcp_servers/shell/service.py`(`ShellService`)がその設定オブジェクトとして使用する。(Explicit in code: `scripts/shared/protocols/shell.py`)

**失敗時の意図:** `__post_init__` で以下を検証し、違反時は `ValueError` を送出する: `kill_policy` は `{"sigterm_then_sigkill", "sigkill_only"}` のいずれか、`sandbox_backend` は `{"firejail", "none"}` のいずれか、`timeout_sec >= 1`、`max_output_kb >= 1`、`max_memory_mb >= 1`、`kill_grace_sec >= 0`。(Explicit in code: `scripts/shared/protocols/shell.py`)

目的: シェル実行ポリシーを MCP サーバー実装から分離すること。

Import: `from shared.protocols.shell import ShellPolicy`

---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 7c. `ToolDefinition` (`shared/tool_registry.py`)

不変のツール定義 — 1 つのツールは必ず 1 つの MCP サーバーに属する。(Explicit in code: `scripts/shared/tool_registry.py` docstring)

**境界条件:** `description` と `input_schema` は将来利用のための予約フィールドであり、デフォルトレジストリ初期化関数では一切設定されず、現状どの呼び出し元からも読まれない。LLMに見せるツールスキーマは各サーバー自身の `tools.py` の `TOOL_LIST` が情報源であり、この `ToolRegistry` からではない。(Explicit in code)

`ToolRegistry` はツールの所有権・ルーティングのみを扱う。ライブ `/v1/tools` の応答は起動時のドリフト検証にのみ使われ、ルーティング判断には使われない。(Explicit in code)

Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## 8a. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

`ArtifactEvent` (event_type, repo, branch, commit, path, pr_number, session_id, timestamp) — リポジトリアーティファクト作成/更新時に発行。(Explicit in code: `scripts/shared/events.py` モジュールdocstring)

> **Note:** `ArtifactEvent` は純粋なデータ構造(`TypedDict`)である。配信の仕組み・イベントバス・購読者は一切存在しない。将来的にアーティファクトイベントを発行しうるコードのための型注釈としてのみ存在する。`ArtifactEvent` のインスタンス生成が何らかのアクションをトリガーすると仮定してはならない。

`RetryEvent` (event_type, workflow_id, task_id, attempt_number, max_attempts, error_type, backoff_sec, session_id, timestamp) — ワークフローステージのリトライ時に発行。

---

## 9a. `ShellPolicy` (`shared/protocols/shell.py`)

不変の `frozen=True` dataclass — FastAPI、MCP、エージェントへの依存はない(shared → external のみ)。`mcp_servers/shell/service.py`(`ShellService`)がその設定オブジェクトとして使用する。(Explicit in code: `scripts/shared/protocols/shell.py`)

**失敗時の意図:** `__post_init__` で以下を検証し、違反時は `ValueError` を送出する: `kill_policy` は `{"sigterm_then_sigkill", "sigkill_only"}` のいずれか、`sandbox_backend` は `{"firejail", "none"}` のいずれか、`timeout_sec >= 1`、`max_output_kb >= 1`、`max_memory_mb >= 1`、`kill_grace_sec >= 0`。(Explicit in code: `scripts/shared/protocols/shell.py`)

目的: シェル実行ポリシーを MCP サーバー実装から分離すること。

Import: `from shared.protocols.shell import ShellPolicy`

---



