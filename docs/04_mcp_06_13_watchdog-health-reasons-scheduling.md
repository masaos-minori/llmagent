---
title: "Watchdog Behavior — Health Reasons and Scheduling"
category: mcp
tags:
  - mcp
  - watchdog
  - health-reasons
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Watchdog Behavior — Health Reasons and Scheduling


### ヘルス理由の優先順位

`/health`経由でHTTP MCPサーバーをプローブすると、LIFECYCLEのアクションと表示用の理由の両方を決定する構造化フィールドが返される。

```python
# From McpProbeResult model
restart_recommended: bool       # True if health endpoint says so OR lifecycle_state == FAILED
operator_action_required: bool  # True only if health endpoint sets this flag
health_reason: str              # Derived priority: operator_action > restart_recommended
```

`health_reason`導出の優先順位:

| 条件 | 結果 |
|-----------|--------|
| `operator_action_required=true` かつ reachable+HTTP_OK | `"operator_action_required"` |
| `restart_recommended=true` かつ reachable+HTTP_OK | `"restart_recommended"` |
| サーバーが到達不能/失敗中 | ボディが提供する理由文字列(`details.reason`、なければ`message`にフォールバック) |
| それ以外のすべてのケース | 空文字列 |

`restart_recommended`フィールドには、異なるセマンティクスを持つ2つの発生源がある。

1. **`/health`エンドポイントから**: サーバー自身によるプロアクティブな推奨を示す
2. **LifecycleProtocol.ensure_ready()から**: `lifecycle_state == FAILED`のときに設定される — トランスポート層の障害に基づくリアクティブな検出を示す

両者は表示レベルでは同等に扱われる。

#### プローブチェーン全体でのボディ理由の追跡

HTTP MCPサーバーの`/health`をプローブする際、bodyフィールドは次のように伝播する。

```python
# Step 1: Probe returns raw body
probe_result.body["reason"] or probe_result.body["message"]

# Step 2: Resolved to endpoint string  
_resolve_endpoint() returns tuple including body_reason

# Step 3: HealthRegistry receives it via record_failure(record_success())
registry.record_failure(reason=str(body_reason))

# Step 4: Displayed at two levels
# - Per-server degraded reason: registry.get_degraded_reason(key)
# - Global table column: McpProbeResult.health_reason derived below
```

#### watchdogのロギング動作

watchdogが`_watchdog_check_http()`経由で問題を検出した場合:

```python
# In _probe_mcp_health_detail():
if not probe.reachable or probe.status_code != HTTPStatus.OK:
    # Unreachable/degraded: no restart attempt; log WARNING with details
elif probe.restart_recommended:
    # Proactive restart recommended: proceed with subprocess shutdown/startup
else:
    # No issue detected: normal operation continues
```

`reachable=True`だが`status_code=503`(degraded)のサーバーの場合、`restart_recommended=false`であるため、watchdogは自動的に再起動しない。代わりに`probe.body["reason"]`または`probe.body["message"]`のボディ理由を含む警告をログに記録する。`operator_action_required=true`の場合も同様のロジックが適用される — 自動再起動はせず、手動対応が必要な旨のWARNINGのみを出す。

---



### ツールエラーの監視

`ToolExecutor`は2種類のエラーカテゴリを区別する。

| カテゴリ | ログフィールド | 条件 |
|----------|-----------|-----------|
| トランスポートエラー | `error_type=transport` | ネットワーク障害、タイムアウト、サーバー到達不能 |
| ツールエラー | `error_type=tool` | サーバーは到達可能だが、ツール実行が`is_error=true`を返した |

トランスポートエラーはMCPサーバーのヘルス状態に影響し、watchdogの再起動をトリガーする可能性がある。
ツールエラーはそうではない — サーバーは正常に動作しているが、特定のツール呼び出しが失敗した
(例: 不正な引数、上流APIのエラー)。

トランスポートエラーは`HttpTransport`によって`TransportError`として発生し、
トランスポートエラーハンドラによって捕捉される。ハンドラは`stat_transport_errors`をインクリメントし、
`HealthRegistry.record_failure()`を呼び出す。

#### サーバーごとのツールエラーカウンタ

`ToolExecutor.stat_tool_errors`は`dict[str, int]`(server_key → カウント)で、
プロセスの生存期間中利用可能である。エージェントコンテキストから参照する。

```python
ctx.services.tools.stat_tool_errors   # {"rag_pipeline": 3, "github": 0}
```

#### 繰り返し発生する障害の警告

サーバーごとのツールエラー数が`repeated_tool_error_threshold`(デフォルト: 3)の倍数に
達した場合、次の警告がログに記録される。

```
WARNING repeated tool errors from 'rag_pipeline': 3 failures (error_type=tool)
```

このしきい値は`ToolExecutor`の構築時に設定可能である。カウンタはプロセス再起動時にリセットされる。
ツールエラーによるサーバーの自動再起動は行われない(watchdogをトリガーするのはトランスポート障害のみ)。

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

エージェントはリソーススコープでグループ化してツール呼び出しを実行する(`use_tool_dag=true`のときに有効なDAGスケジューリング)。`use_tool_dag=false`に設定すると、レガシーな非本番モード(ラウンド内でリソーススコープの並列性を持たずに、すべてのWRITE_TOOLSをREAD_TOOLSより先に実行する)に戻る。ほとんどのツールは並列実行されるが、
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

```
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

例:

```
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

#### /mcp statusにおける直列化統計

`/mcp status`を実行すると、セッションの累積統計を確認できる。

```
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


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

watchdog
health-reasons
scheduling
