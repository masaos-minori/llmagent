---
title: "MCP Health Reasons and Scheduling (Part 2)"
category: mcp
tags:
  - mcp
  - health-reasons
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md
---

# MCP Health Reasons and Scheduling


## ツールエラーの監視

`ToolExecutor`は2種類のエラーカテゴリを区別する。

| カテゴリ | ログフィールド | 条件 |
|----------|-----------|-----------|
| トランスポートエラー | `error_type=transport` | ネットワーク障害、タイムアウト、サーバー到達不能 |
| ツールエラー | `error_type=tool` | サーバーは到達可能だが、ツール実行が`is_error=true`を返した |

トランスポートエラーはMCPサーバーのヘルス状態(`McpServerHealthRegistry`)に影響する。
ツールエラーはそうではない — サーバーは正常に動作しているが、特定のツール呼び出しが失敗した
(例: 不正な引数、上流APIのエラー)。

トランスポートエラーは`HttpTransport`によって`TransportError`として発生し、
トランスポートエラーハンドラによって捕捉される。ハンドラは`stat_transport_errors`をインクリメントし、
`HealthRegistry.record_failure()`を呼び出す。

### サーバーごとのツールエラーカウンタ

`ToolExecutor.stat_tool_errors`は`dict[str, int]`(server_key → カウント)で、
プロセスの生存期間中利用可能である。エージェントコンテキストから参照する。

```python
ctx.services.tools.stat_tool_errors   # {"rag_pipeline": 3, "github": 0}
```

#### 繰り返し発生する障害の警告

サーバーごとのツールエラー数が`repeated_tool_error_threshold`(デフォルト: 3)の倍数に
達した場合、次の警告がログに記録される。

``` text
WARNING repeated tool errors from 'rag_pipeline': 3 failures (error_type=tool)
```

このしきい値は`ToolExecutor`の構築時に設定可能である。カウンタはプロセス再起動時にリセットされる。
ツールエラーはサーバーの自動再起動を引き起こさない — 自動的な復旧経路は存在しない
([04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)参照)。

#### 監視用のgrepパターン

```bash
# Find tool errors for a specific server
grep "error_type=tool" agent.log | grep "rag_pipeline"

# Find repeated-failure warnings
grep "repeated tool errors" agent.log

# Find transport failures
grep "error_type=transport" agent.log
```

---



### ツールのスケジューリングと直列化

エージェントはリソーススコープでグループ化してツール呼び出しを実行する(`serial_tool_calls=False`のときに常時有効なDAGスケジューリング)。`use_tool_dag`という設定フィールドはコードベース上に存在しない(Explicit in code — [05_agent_08_03](05_agent_08_03_configuration-tools-memory.md#toolconfig-cfgtool)参照)。`serial_tool_calls=True`に設定すると、レガシーな標準実行モード(副作用のあるツールが1つでもあれば逐次実行、なければ並列実行)に切り替わる。ほとんどのツールは並列実行されるが、
特定の条件下ではラウンド内で直列実行が強制される。

| 条件 | トリガー | ログ上の理由 |
|-----------|---------|------------|
| ツールが`requires_serial=True`を持つ | このフラグを持つ任意のツール | `requires_serial` |
| 複数のwriteツールが同じ`resource_scope`を共有 | 同じスコープを持つ2つ以上のwriteツール | `resource_scope_conflict` |
| `resource_scope`を持たないwriteツール | スコープメタデータを持たない任意のwriteツール | `is_write_overlap` |
| ラウンド内の副作用ツール(標準実行パス) | 任意の副作用ツール | "Side-effect tool detected"としてログ記録 |

直列化は意図的な安全策である — 並行書き込みによる共有リソースの破損を防ぐ。
これは設定エラーを示すものではない。

#### 直列化ログエントリの読み方

各直列化イベントは次の形式でログに記録される。

``` text
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

例:

``` text
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

#### /mcp statusにおける直列化統計

`/mcp status`を実行すると、セッションの累積統計を確認できる。

``` text
--- Tool Scheduling ---
  Serialization events this session: 5
  Tools affected by serialization:   12
```

これらのカウンタはエージェント再起動時にリセットされる。ツール呼び出し総数に対して
直列化回数が多い場合、`resource_scope`アノテーションの追加や
`requires_serial=False`への見直しの候補になり得る — ただし、どのツールがそれを
引き起こしているかを分析した上で判断すること。

#### 最適化を行う前に

直列化ログのデータを確認せずに`requires_serial`や`resource_scope`の値を
変更してはならない。観測可能性(observability)レイヤーは、安全な判断を下すために
必要なデータを提供する。

---

### Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

### Keywords

health-reasons
scheduling
