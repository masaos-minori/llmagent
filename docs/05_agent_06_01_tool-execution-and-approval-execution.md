---
title: "Agent Tool Execution and Approval - Execution"
category: agent
tags:
  - agent
  - tool-execution
  - toolexecutor
  - dag-scheduler
  - parallel-execution
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
  - 05_agent_04_01_state-and-persistence-state-model-part1.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)
- GitHub変更操作の承認/gitops制御 → [05_agent_06_02_tool-execution-and-approval-approval.md](05_agent_06_02_tool-execution-and-approval-approval.md)

## 目的

`ToolExecutor`の挙動、並列実行と逐次実行、承認フロー、
プランモード、ツール実行結果の要約、キャッシュ、安全制御、`allowed_tools`を文書化する。

---

## ToolExecutor (`shared/tool_executor.py`)

`execute(tool_name, args) -> ToolCallResult`のディスパッチ優先順位:

``` text
1. TTL cache                           — 期限切れでなければキャッシュ結果を返す
2. MCP server dispatch via internal method
     → ToolRouteResolver.resolve()     — tool_name → server_key (ルーティングの権威; 04_mcp_03 §Routing Source of Truth 参照)
     → McpServerHealthRegistry check  — UNAVAILABLEなサーバーをスキップ
     → LifecycleProtocol.ensure_ready() — 必要に応じてondemandサーバーを起動
     → HttpTransport — MCPサーバーへ送信
```

`ToolCallResult`はfrozenなdataclass: `(output: str, is_error: bool, request_id: str, server_key: str)`

---

## 並列実行と逐次実行

`execute_all_tool_calls()`は`ctx.cfg.tool.serial_tool_calls`のみに基づいてディスパッチする。

| Condition | Execution |
|---|---|
| `serial_tool_calls=False` (デフォルト) | DAGスケジューリング |
| `serial_tool_calls=True` | 標準実行 — 逐次/並列判定 (副作用のあるツールが1つでもあれば逐次、なければ`asyncio.gather()`で並列) |

> **Explicit in code:** ツール呼び出し実行関数は`if not ctx.cfg.tool.serial_tool_calls: DAGスケジューリング(...) else: 標準実行(...)`という2分岐のみで構成される。`use_tool_dag`という設定フィールドはコードベース全体 (`agent/config_dataclasses.py`含む) に存在しない。DAGスケジューリングは`serial_tool_calls=False`の場合に常時有効であり、「レガシー動作」への切替フラグは実装上存在しない。旧版ドキュメントにあった`use_tool_dag`および`ProductionConfigValidator`による`use_tool_dag=false`の起動時エラー化の記述は実装と一致しないため削除した。`ProductionConfigValidator.validate()` (`shared/production_config_validator.py`) が実際に検証するのは`tool_definitions_strict`/`routing_drift_strict`のstrictキー、`tool_safety_tiers`の登録漏れ・不明キー、および`allowed_tools=[]`のみである (詳細は[05_agent_06_03](05_agent_06_03_tool-execution-and-approval-concurrency-safety.md)参照)。

---

## DAG Tool Scheduler (`agent/tool_scheduler.py`)

`build_execution_groups(tool_calls, tool_meta)`はツール呼び出しを順序付きバッチにグルーピングする。

### ルール (優先順位順に適用)

1. **`requires_serial=True`** — ツールは単一要素のシリアルバリアを形成し、他のすべてのツールより前に単独で実行される
2. **同一の`resource_scope` + `is_write=True`** — 同じスコープを共有するツールはそのスコープのグループ内でシリアル化される
3. **`resource_scope`のない`is_write=True`** — `write_first`グループに入る (保守的に、読み取りより前に実行される)
4. **その他すべて** — 末尾の並列グループ

### `concurrent_groups`構造

`metadata.concurrent_groups: list[list[list[dict]]]` — バッチのリスト:
- 各**バッチ**は他のバッチに対して逐次実行される
- バッチ**内**のグループは`asyncio.gather()`により並行実行される
- `serial_barrier`ツール: それぞれ単独のバッチ
- `write_first`グループ: 専用の逐次バッチ
- すべての`resource_scope`グループ + 並列グループ: 共有の並行バッチ

例: `[write_file(scope=file), github_push(scope=github), read_text_file]` →
3つのグループを持つ1つの並行バッチとなり、すべて同時に実行される。

### `scheduling_mode`監査フィールド

`"dag_concurrent"` — 少なくとも1つのバッチで複数のグループが並行実行された。
`"dag_sequential"` — すべてのバッチが単一グループで実行された (バッチ内の並行性なし)。

### `execute_one_tool_call(ctx, tc, turn)`

1つのtool_call dictを解析、実行し、必要に応じて要約する。`(tc_id, name, args, full_text, is_error, llm_text)`を返す。

- `arguments` JSONを解析する; 不正なJSONの場合は`ToolArgumentsDecodeError`を発生させる
- `ctx.services_required.tools`がNoneの場合`ToolExecutorUnavailableError`を発生させる
- JSON解析後、ディスパッチ (gateway経由 or 直接executor) の前に`_validate_tool_args(ctx, name, args)`を呼び出し、`RuntimeTool.input_schema`に対するスキーマバリデーションを行う (下記「引数バリデーション」参照)
- トランスポートエラーの場合: 失敗を`ctx.diagnostics`に保存する
- 要約が有効かつ結果が閾値を超える場合: `summarize_tool_result()`を呼び出す → `llm_text`
- それ以外: `tool_result_max_llm_chars`まで切り詰め + "\n... (truncated)"

### 引数バリデーション (`_validate_tool_args()`, `agent/tool_arg_validator.py`)

`execute_one_tool_call()`は`orjson.loads()`によるJSON解析の直後、gateway/直接executorへのディスパッチの前に`_validate_tool_args(ctx, name, args) -> ToolCallResult | None`を1回だけ呼び出す。ディスパッチ分岐ごとの重複バリデーションは行わない。

- `ctx.services_required.runtime_tools`が`None`の場合 (デフォルト、`RuntimeToolRegistry`が未接続の場合): バリデーションはno-opで`None`を返す (既存の挙動と完全互換)
- `registry.get(name)`が`KeyError`を送出した場合 (未登録ツール): `None`を返し、寛容にフォールバックする
- 登録済みツールが見つかった場合: `agent/tool_arg_validator.py::validate_tool_arguments(tool_name, args, input_schema=runtime_tool.input_schema, allow_extra_fields=runtime_tool.allow_extra_fields)`を呼び出す
  - 必須フィールド欠如、スキーマ未定義の余剰フィールド (`allow_extra_fields=True`の場合は許容)、`jsonschema`による型不一致の3種類をチェックする
  - 上記3種類のチェックがすべて成功した場合のみ、`tool_name`をキーに`_CUSTOM_VALIDATORS`レジストリ (`register_custom_validator(tool_name)`デコレータで登録) からカスタムフックを検索して実行する (`_run_custom_validator()`)。未登録のツールはno-op (`ValidationResult(success=True)`) で従来通りの挙動を維持する。フック内で発生した例外は`_run_custom_validator()`が捕捉し、`ValidationResult(success=False, reason=...)`に変換する (伝播させない)
  - 検証成功時は`None`を返し、通常のディスパッチ (gateway or 直接executor) に進む
  - 検証失敗時は合成の`ToolCallResult(is_error=True, source="validation", error_type="validation", output=<理由>)`を返し、`gateway.execute()`/`tools.execute()`のいずれも呼び出されない
- `source="validation"`(非空文字列)を設定することで、`audit_tool_exec()`の早期リターンガード (`if not mcp_request_id and not source: return`) を回避し、拒否イベントも監査ログに記録される
- **Residual risk (documented, not fixed):** MCPサーバー由来の構造的に不正なスキーマは`jsonschema.SchemaError`を送出しうるが、`_check_type_validation()`はこれを捕捉しない。`tool_arg_validator.py`内部の挙動でありスコープ外 (将来のフォローアップ候補)。

### 履歴への結果反映 (`_collect_tool_result_msgs()`, `_build_denied_messages()`)

`agent/tool_runner.py`の2箇所の`ctx.conv.history`変更は、生の`list.append()`/`list.extend()`ではなく
`ConversationState`の検証付きメソッド (`ConversationState.append_message()`/`extend_messages()`;
詳細は[05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)
§検証付き履歴変更メソッド を参照) を経由する:

- `_collect_tool_result_msgs()`: 各ツール結果ごとに`ctx.conv.append_message({"role": "tool",
  "tool_call_id": tc_id, "content": llm_text})`を`source`指定なしで1件ずつ呼ぶ
- `execute_all_tool_calls()`: `_build_denied_messages(denied_ids)`が構築した拒否メッセージのリスト
  (`denied_history`) をまとめて`ctx.conv.extend_messages(denied_history)`で追加する。
  `replace_history()`は使わない — 拒否メッセージは既存のターン履歴に**追記**するものであり、
  履歴全体の置き換えではないため
- どちらのメッセージ形状も`role`/`tool_call_id`/`content`のみで構成され、
  `ROLE_KEY_WHITELIST["tool"]`と完全一致するため、検証は常に成功し、
  以前の生の`.append()`/`.extend()`呼び出しと比較して保存内容は変化しない
  (内部の呼び出し経路の変更のみであり、挙動に変化はない)

### シリアル化統計

シリアル化統計はラウンドをまたいだシリアル化の影響を追跡する:

| Counter | Description |
|---|---|
| `total_events` | 全ラウンドを通じた累積シリアル化イベント数 |
| `total_tools_affected` | シリアル化の影響を受けた累積ツール数 |
| `tools_affected_last_round` | 直近のラウンドで影響を受けたツール数 (シリアル化がない場合は0にリセット) |

### 表示閾値

500文字を超える結果は、ログ上で全文の代わりに行数/文字数として表示される。

---

### シリアル化イベントスキーマ

各ラウンドは`round_exec`監査イベントを発行する:

| Field | Type | Description |
|---|---|---|
| `round_id` | string | このラウンドを識別するUUIDv4 |
| `tool_count` | int | ラウンド内のツール呼び出し数 |
| `mode` | string | `"parallel"`または`"serial"` |
| `has_side_effect` | bool | シリアル化イベントが発生した場合True |
| `trigger_tool` | string or null | シリアル化を引き起こした最初のツール |
| `elapsed_ms` | float | ラウンド全体の実時間 (ミリ秒) |
| `scheduling_mode` | string or null | DAGモード: `"dag_concurrent"`または`"dag_sequential"`; 標準モードではnull |
| `affected_tools` | list[string] | このラウンドで実行されたツール名一覧 |
| `serial_reason` | string or null | シリアル化理由 (例: `"side_effect"`。DAGモードでは`requires_serial`/`resource_scope_conflict`/`is_write_overlap`のいずれか) |
| `estimated_parallel_ms` | float or null | 標準モードでのみ設定。並列実行だった場合の推定所要時間 (各ツール実行時間の合計) |
| `source` | string | 固定値`"agent"` |
| `ts` | float | イベント発行時刻 (UNIX時間) |

> **Explicit in code:** 監査ロギング関数が上記フィールドをすべて発行する。DAG実行関数は`mode`フィールドに常に文字列`"parallel"`を設定する (DAG実行であることを示す固定値であり、バッチ内の逐次/並列の別は`scheduling_mode`側で表現される)。一方標準実行の`mode`は実際の実行方式に応じて`"serial"`または`"parallel"`になる。同じ`mode`フィールドでも経路によって意味が異なる点に注意。

`elapsed_ms`を使ってシリアル化のオーバーヘッドを特定する。`has_side_effect=true`かつ
同等の並列ラウンドと比較して`elapsed_ms`が高いラウンドは、最適化の候補となる。

監査ログの検索:
``` text
grep round_exec /path/to/audit.log
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`
- `05_agent_04_01_state-and-persistence-state-model-part1.md`

## Keywords

ToolExecutor
parallel vs sequential execution
DAG tool scheduler
execute_one_tool_call
tool argument validation
validate_tool_arguments
RuntimeToolRegistry
validated history append/extend
_collect_tool_result_msgs
_build_denied_messages
