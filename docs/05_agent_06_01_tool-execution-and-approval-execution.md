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

`execute_all_tool_calls()`は`ctx.cfg.tool.serial_tool_calls`のみに基づいてディスパッチする:

| Condition | Execution |
|---|---|
| `serial_tool_calls=False` (デフォルト) | DAGスケジューリング |
| `serial_tool_calls=True` | 標準実行 — 逐次/並列判定 (副作用のあるツールが1つでもあれば逐次、なければ`asyncio.gather()`で並列) |

**Design judgment**: DAGスケジューリングは`serial_tool_calls=False`の場合に常時有効であり、「レガシー動作」への切替フラグは実装上存在しない。

### DAG Tool Scheduler の設計判断

#### ルール (優先順位順に適用)

1. **`requires_serial=True`** — シリアルバリアを形成し、他のすべてのツールより前に単独で実行
2. **`resource_scopes`が重複する呼び出し同士（うち少なくとも1件は`is_write=True`）** — コンフリクトグラフの連結成分としてグループ化され、そのグループ内はシリアル化される（完全一致に加え、ファイルシステムスコープは祖先/子孫関係でも重複と判定される。`shared/resource_scope.py::_scopes_conflict()`）
3. **`resource_scopes`が空の`is_write=True`** — `write_first`グループに入る (保守的に読み取りより前に実行)
4. **その他すべて** — 末尾の並列グループ

グルーピングは`agent/tool_scheduler.py::build_execution_groups()`が`call_id`をキーとする
`ToolSpec`（`agent/tool_runner.py::_execute_with_dag()`が`RuntimeToolRegistry.tool_spec_for_call()`
経由で呼び出しごとに構築）を対象に行う — ツール名単位ではない。同じツール名への異なる呼び出しでも
`resource_scopes`が重複しなければ同一バッチ内で並行実行され得る。

#### concurrent_groups構造

- 各**バッチ**は他のバッチに対して逐次実行
- バッチ**内**のグループは`asyncio.gather()`により並行実行
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
承認・実行に渡される。`execute_one_tool_call()`・`_execute_standard()`・`_execute_with_dag()`は
`PreparedToolCall.spec`（準備フェーズで解決済み）を参照するのみで、独自の引数バリデーションやレジストリ照会は行わない。

### 履歴への結果反映

`ConversationState.append_message()` / `extend_messages()` を経由する検証付きメソッドを使用。

## Responsibility Boundary

- **正典**: `shared/tool_executor.py`, `agent/tool_scheduler.py`, `agent/tool_preparation.py`（引数バリデーション/レジストリ解決を含む準備フェーズ）
- **ルーティングの権威**: `ToolRouteResolver.resolve()` ([04_mcp_03 §Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md))

## Key Constraints

- DAGスケジューリングは`serial_tool_calls=False`の場合に常時有効（レガシー動作への切替不可）
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
- `05_agent_04_01_state-and-persistence-state-model-part1.md`

## Keywords

ToolExecutor
parallel vs sequential execution
DAG tool scheduler
tool argument validation
tool call preparation phase
PreparedToolCall
fail-closed
validated history append/extend
