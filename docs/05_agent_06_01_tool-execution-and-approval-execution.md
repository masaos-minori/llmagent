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
2. **同一の`resource_scope` + `is_write=True`** — 同じスコープのグループ内でシリアル化
3. **`resource_scope`のない`is_write=True`** — `write_first`グループに入る (保守的に読み取りより前に実行)
4. **その他すべて** — 末尾の並列グループ

#### concurrent_groups構造

- 各**バッチ**は他のバッチに対して逐次実行
- バッチ**内**のグループは`asyncio.gather()`により並行実行
- `scheduling_mode`: `"dag_concurrent"` / `"dag_sequential"`

### 引数バリデーション

`_validate_tool_args()`はJSON解析直後の1回だけ呼び出される:
- `RuntimeToolRegistry`が未接続の場合: no-op
- 未登録ツール: 寛容にフォールバック
- 登録済みツール: スキーマバリデーション + カスタムフック

### 履歴への結果反映

`ConversationState.append_message()` / `extend_messages()` を経由する検証付きメソッドを使用。

## Responsibility Boundary

- **正典**: `shared/tool_executor.py`, `agent/tool_scheduler.py`
- **ルーティングの権威**: `ToolRouteResolver.resolve()` ([04_mcp_03 §Routing Source of Truth](04_mcp_03_01_dispatch-and-routing.md))

## Key Constraints

- DAGスケジューリングは`serial_tool_calls=False`の場合に常時有効（レガシー動作への切替不可）
- 同一`resource_scope`を持つwriteツールの複数呼び出しは同一グループ内で並行実行される

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
validated history append/extend
