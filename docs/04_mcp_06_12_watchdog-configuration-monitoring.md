---
title: "Watchdog Behavior — Configuration and Monitoring"
category: mcp
tags:
  - mcp
  - watchdog
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Watchdog Behavior — Configuration and Monitoring


## Watchdogの動作

watchdogループ(`agent/repl_health.py`の`watchdog_loop()`)は、すべてのMCPサーバーを定期的にプローブし、障害が発生した際に再起動を試みる。バックグラウンドのasyncioタスクとして動作する。

**注記:** watchdogによる定期的な`record_success()`/`record_failure()`呼び出しは、ツール実行層からのHealthRegistry更新(呼び出しごと)を補完するものであり、置き換えるものではない。各ツール呼び出しは、watchdogとは独立して自身の失敗カウントをインクリメントする。

#### ステータス表示におけるプロセススナップショットの統合

`_probe_single_server()`がMcpStatusService.probe_all()経由で実行されると、ライフサイクル情報を各行に統合する。

```python
snapshot_fn = getattr(lifecycle, "get_process_snapshot", None)
snapshot = snapshot_fn(key) if snapshot_fn else None

# PID column shows actual process ID if managed by this agent
pid_display = str(snapshot.get("pid")) if snapshot else "-"

# LIFECYCLE column combines two sources:
lifecycle_state = lifecycle.get_transport_state(key).value   # RUNNING/STARTING/etc.
restart_rec_http = probe_result.restart_recommended          # HTTP endpoint flag
restart_recommended = (lifecycle_state == FAILED.value) or restart_rec_http
operator_action_required = op_action_http                    # Only from HTTP endpoint
health_reason = body_reason                                   # Priority-derived reason string
```

つまり、`/health`エンドポイントを直接呼び出さなくても、ツールディスパッチ中の過去のトランスポート障害によってサブプロセスモードのサーバーがFAILEDとマークされているかどうかを判定できる。これはLIFECYCLE状態と、そこから導出される`restart_recommended`フィールドの両方から確認できる。



### 設定

| 設定項目 | LOCALデフォルト | PRODUCTIONデフォルト | 効果 |
|---|---|---|---|
| `mcp_watchdog_interval` | `0`(無効) | `30.0` | プローブ間隔(秒);`0`は無効 |
| `mcp_watchdog_max_restarts` | `3` | `3` | サーバーごとの最大再起動試行回数(超過すると諦める) |



### 無効化状態の影響

`mcp_watchdog_interval = 0`の場合:
- watchdogループ自体は起動するが、警告ログを出力する: `Watchdog: disabled (interval=0) — failed servers will not be auto-restarted`
- クラッシュしたHTTPサーバーは、エージェントプロセスを手動で再起動するまで到達不能のままとなる
- クラッシュしたサブプロセスサーバー(shell-mcp)は自動的に再起動されない



### 推奨値と運用上の影響

| プロファイル | `mcp_watchdog_interval` | 根拠 |
|---|---|---|
| LOCAL開発環境 | `0`(無効) | 開発時は手動再起動で十分であり、不要なログノイズを避けられる |
| PRODUCTION | `30.0` | 検出速度とプローブのオーバーヘッドのバランスを取り、30秒以内にクラッシュを検知できる頻度 |

**`mcp_watchdog_interval`を低すぎる値(10秒未満)に設定した場合:**
- すべてのMCPサーバーに対するプローブのオーバーヘッドが増加する
- 一時的な障害に対するログエントリが頻発する
- 復旧が遅いサーバーで再起動ループが高速に発生する可能性がある

**`mcp_watchdog_interval`を高すぎる値(120秒超)に設定した場合:**
- サーバー障害の検出が遅延する
- 自動再起動までのサービス劣化期間が長引く
- クラッシュから復旧までの間、重要なMCPサーバーのダウンタイムが延びる

**一般的な指針:** 本番環境では`mcp_watchdog_interval`を15〜60秒の範囲に保つこと。この範囲外の値は、明確な根拠がある場合にのみ使用すべきである。



### watchdog状態の確認方法

現在のwatchdog状態は次の2箇所で確認できる。

1. **起動ログ**(`/opt/llm/logs/agent.log`):
   ```
   INFO  Watchdog: enabled (interval=30s, max_restarts=3)
   ```
   または
   ```
   WARNING Watchdog: disabled (interval=0) — failed servers will not be auto-restarted
   ```

2. **`/mcp status`コマンド**(REPL):
   ```
   Watchdog    enabled (interval=30s, max_restarts=3)
   ```
   または
   ```
   Watchdog    disabled (interval=0) — no auto-restart
   ```


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

watchdog
configuration
monitoring
