---
title: "Agent Tool Execution and Approval - Execution"
category: agent
tags:
  - agent
  - tool-execution
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_06_01_tool-execution-and-approval-execution.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)
- GitHub変更操作の承認/gitops制御 → [05_agent_06_02_tool-execution-and-approval-approval.md](05_agent_06_02_tool-execution-and-approval-approval.md)

## Purpose

`ToolExecutor`の責任分割、並列/逐次実行の設計判断、DAGスケジューリングについて文書化する。

## Design Intent

### ToolExecutor の責任分割

`ToolExecutor.execute(tool_name, args)`のディスパッチ優先順位:
1. TTL cache
2. MCP server dispatch via `ToolRouteResolver.resolve()` → `McpServerHealthRegistry` → `LifecycleProtocol.ensure_ready()` → `HttpTransport`

### 並列実行と逐次実行

`execute_all_tool_calls()`は常に`agent/tool_runner.py::_execute_with_dag()`（単一の実行パス）に
処理を委譲する。`_execute_standard()`という第2の実行エンジンは廃止された。`ctx.cfg.tool.serial_tool_calls`は
もはや実行エンジンを選択するフラグではなく、`agent/tool_scheduler.py::build_execution_groups()`への
`force_serial`入力としてスケジューラに渡される:

| Condition | Execution |
|---|---|
| `serial_tool_calls=False` (デフォルト) | DAGスケジューリング（フェーズ構築 + コンフリクトグラフ） |
| `serial_tool_calls=True` | `force_serial=True` — フェーズ構築/コンフリクトグラフ構築を丸ごとバイパスし、呼び出し順に1件ずつの単独シリアルフェーズを生成 |

**Design judgment**: `_execute_with_dag()`が唯一の実行パスであり、「レガシー動作（標準実行）」への
切替フラグは実装上存在しない。`serial_tool_calls=True`は依然として全呼び出しを1件ずつ逐次実行させるが、
それは別関数への分岐ではなく、単一のスケジューラへの入力を通じて実現される。

### DAG Tool Scheduler の設計判断

#### ルール（入力順に呼び出しを走査し、フェーズを構築する）

1. **`requires_serial=True`** — インプレースのバリア。それまでに蓄積したフェーズを閉じ、当該呼び出し
   単独のシリアルフェーズを元の出現位置で発行し、後続の呼び出し用に新しいフェーズを開始する
   （バッチ先頭への引き上げはしない）
2. **`resource_scopes`が重複する呼び出し同士（うち少なくとも1件は`is_write=True`）** — 同一フェーズ内で
   コンフリクトグラフの連結成分としてグループ化され、そのグループ内はシリアル化される（完全一致に加え、
   ファイルシステムスコープは祖先/子孫関係でも重複と判定される。`shared/resource_scope.py::_scopes_conflict()`）
3. **`resource_scopes`が空の`is_write=True`** — 合成スコープ`("global:write",)`とみなされ、ルール2と
   同じコンフリクトグラフに参加する。専用の`write_first`バケットは廃止され、スコープなしwrite同士も
   衝突として検出されシリアル化される（他の呼び出しと衝突しなければ、通常どおり並行実行グループにプールされる）
4. **同一フェーズ内でルール1〜3のいずれにも該当しない呼び出し** — 1つの並行実行グループにプールされる
5. **`force_serial=True`**（`ctx.cfg.tool.serial_tool_calls`から供給）— 上記すべてをバイパスし、
   呼び出し順に1件ずつの単独シリアルフェーズを生成する

グルーピングは`agent/tool_scheduler.py::build_execution_groups()`が`call_id`をキーとする
`ToolSpec`（`agent/tool_runner.py::_execute_with_dag()`が`RuntimeToolRegistry.tool_spec_for_call()`
経由で呼び出しごとに構築）を対象に行う — ツール名単位ではない。同じツール名への異なる呼び出しでも
`resource_scopes`が重複しなければ同一バッチ内で並行実行され得る。

#### ExecutionPlan構造（batches / ScheduledGroup）

`build_execution_groups()`は単一の`ExecutionPlan`（`batches: tuple[ScheduledBatch, ...]`、
`serialization_events: tuple[SerializationEvent, ...]`）を返す。旧`tuple[list[list[dict]], _GroupMetadata]`
という2値タプル + `serialize_flags`の並行配列形式は廃止された。

- 各**バッチ**は他のバッチに対して逐次実行
- バッチ**内**の`ScheduledGroup`は`asyncio.gather()`により並行実行され、各グループの`sequential`
  フラグが`True`の場合はグループ内の呼び出しを順に実行する
- `scheduling_mode`: `"dag_concurrent"` / `"dag_sequential"`

### 引数バリデーション

引数の解析・解決・バリデーションは`agent/tool_preparation.py::prepare_tool_calls()`が承認フェーズより前の
専用の準備フェーズとして一括で行う（`execute_all_tool_calls()`内で`_run_approval_gate()`より前に呼ばれる）。
呼び出しごとに以下を順に行い、いずれかに失敗した場合はフェイルクローズド（`PreparedToolCall`を生成せず、
承認・スケジューリング・実行のいずれにも到達させず、合成エラー結果として即座に却下する）:
- `id`/`function.name`の存在確認
- `arguments`のJSON解析（1回のみ）およびdict型チェック
- `RuntimeToolRegistry`への解決 — 未接続の場合、または対象ツールが未登録の場合はいずれも却下（フォールバックなし）
- 登録済みツール: `agent/tool_arg_validator.py::validate_tool_arguments()`によるスキーマバリデーション + カスタムフック
- `RuntimeToolRegistry.tool_spec_for_call()`によるメタデータ構築

準備フェーズを通過した呼び出しのみが`PreparedToolCall`（`call_id`/`name`/`args`/`spec`/`original_call`）として
承認・実行に渡される。`execute_one_tool_call()`・`_execute_with_dag()`は
`PreparedToolCall.spec`（準備フェーズで解決済み）を参照するのみで、独自の引数バリデーションやレジストリ照会は行わない。

### 履歴への結果反映

`ConversationState.append_message()` / `extend_messages()` を経由する検証付きメソッドを使用。

## Responsibility Boundary

- **正典**: `shared/tool_executor.py`, `agent/tool_scheduler.py`, `agent/tool_preparation.py`（引数バリデーション/レジストリ解決を含む準備フェーズ）
- **ルーティングの権威**: `ToolRouteResolver.resolve()` ([04_mcp_03 §Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md))

## Key Constraints

- `_execute_with_dag()`が唯一の実行パス。`serial_tool_calls=True`は別エンジンへの切替ではなく、
  `build_execution_groups()`への`force_serial`入力としてのみ作用する
- `resource_scopes`が重複するwriteツールの複数呼び出しは同一グループ内で並行実行される
- 準備フェーズはフェイルクローズド: id欠落・JSON不正・未登録ツール・レジストリ未接続・スキーマ違反・メタデータ構築失敗のいずれかがあれば、承認/実行/スケジューリングに到達する前に却下される

## Operational Notes

- 不明

## Known Limitations

- MCPサーバー由来の構造的に不正なスキーマは`jsonschema.SchemaError`を送出しうるが、`_check_type_validation()`はこれを捕捉しない

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

ToolExecutor
parallel vs sequential execution
DAG tool scheduler
tool argument validation
tool call preparation phase
PreparedToolCall
fail-closed
validated history append/extend
ExecutionPlan
ScheduledGroup
force_serial
global:write scope
