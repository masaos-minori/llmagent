---
title: "Agent Operations and Observability - Runtime Diagnostics"
category: agent
tags:
  - agent
  - operations
  - runtime-diagnostics
  - session-end-summary
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Partial Completion and Truncation Monitoring(部分完了と切り捨ての監視)

| Condition | 検出方法 | Action |
|---|---|---|
| LLMストリームの中断(部分完了) | `/stats` で `partials > 0` と表示される。エージェントログ: `WARNING Partial LLM completion saved: {kind}` | 詳細は `session_diagnostics`(`kind=partial_completion`)を確認する。LLMエンドポイントの安定性を確認する |
| コンテキスト圧縮(HistoryManager) | `/stats` で `Compress: N > 0` と表示される。エージェントログ: `INFO Compressed history` | `context_char_limit` を増やす、またはコンテキストサイズを削減する |
| 最大ツールターン数に到達 | エージェントログ: `WARNING max_tool_turns=N reached` | `config/agent.toml` の `max_tool_turns` を増やす |

正式な部分完了モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)。

> **実装との差異(要修正の可能性):**
> - `/stats` の実際の表示ラベルは `Partial compl : N`(0件時は `Partial compl : 0`)であり、本表の `partials > 0` は正確な画面文字列ではなく意味的な要約表現である。1件以上のとき `(stored in session_diagnostics)` という補足が付く(`scripts/agent/commands/cmd_config_stats.py`)(根拠: Explicit in code)。
> - 圧縮を発生させるログ文言は実際には `"History compressed: %s messages summarized"`(`scripts/agent/history.py`)であり、本表の `Compressed history` と文字列が一致しない(根拠: Explicit in code)。
> - `compression_char_threshold` という設定キーは実装に存在しない。圧縮閾値の実際の設定キーは `context_char_limit`(既定値 8000、`config/agent.toml` および `scripts/agent/config_dataclasses.py`)であり、履歴の合計文字数がこの値を超えると圧縮がトリガーされる。圧縮しきい値を調整する場合は `context_char_limit` を使用する(根拠: Explicit in code)。
> - `max_tool_turns` 到達時の実際のログ文言は `"Reached max_tool_turns=%s"`(`scripts/agent/llm_turn_runner.py`)であり、本表の `max_tool_turns=N reached` と語順が異なる(意味は同じ)(根拠: Explicit in code)。
> - 圧縮が発生せず文字数上限を超えたままの場合、`HistoryManager` はフォールバック切り捨て(重要度の低いメッセージから削除)を行い `stat_fallback_truncate_count` をインクリメントする。`/stats` では `Fallback trunc: N` として表示される。これは本表に記載がない挙動であり、圧縮に失敗した場合のフェイルセーフとして実装されている(根拠: Explicit in code)。

---

## Troubleshooting(トラブルシューティング)

| Symptom | Cause | Action |
|---|---|---|
| `embedding attempt 3/3` がすべて失敗する | embed-llmが起動していない、または過負荷 | `curl -s http://127.0.0.1:8003/health` を実行し、モデルのロードを待つ |
| `AttributeError: enable_load_extension` | sqlite拡張サポートなしでPythonがビルドされている | `echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python && emerge dev-lang/python` |
| `no such table: chunks_vec` | sqlite-vec拡張のロードに失敗 | `ls /opt/llm/sqlite-vec/vec0.so` |
| FTS検索が0件を返す | `chunks_fts` が非同期状態 | `/db rag rebuild-fts` |
| `blob_bytes` ≠ 1536 | 埋め込み次元の不一致 | embedモデルが384次元を出力しているか確認する |
| `Sudachi tokenize error` が頻発 | sudachidict-coreが未インストール | `pip install sudachidict-core` |
| llama-serverが起動しない | モデルファイルのパスまたは権限の問題 | `ls -lh /opt/llm/models/` |
| レイテンシが非常に高い | 複数モデルのロードによりRAMが枯渇 | `--threads` を調整し、合計を4以下に保つ |
| `/mcp` でサーバがUNAVAILABLEと表示される | ヘルスレジストリがサーバを利用不可としてマークしている | 自動再起動の試行についてウォッチドッグログを確認する。サーバの*定義*(URL、認証、transportなど)が変更された場合はエージェントの完全な再起動が必要 — `/reload` はMCP設定の変更を適用しない |

---

## Runtime Diagnostics (session-end summary)(実行時診断。セッション終了時サマリ)

セッション終了時、軽量な診断概要が `DiagnosticStore.save(kind="session_summary")` を通じて `session_diagnostics` テーブルに永続化される。これはREPLセッションを超えて保持され、事後分析に利用できる。

セッション診断のクエリ:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC LIMIT 10;"
```

特定の診断エントリの取得:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE session_id = ? AND kind = 'session_summary' ORDER BY created_at DESC LIMIT 1;" | jq .content
```

診断種別によるフィルタリング:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE kind = 'mid_turn_error' ORDER BY created_at DESC;" | jq -r '.content'
```

> **kind種別の網羅性(加筆):** `session_summary` / `mid_turn_error` 以外にも `DiagnosticStore` を経由して以下の`kind`が実際に保存される(`scripts/agent/diagnostic_store.py` および各呼び出し元)(根拠: Explicit in code)。
>
> | kind | 発生元 | 内容 |
> |---|---|---|
> | `partial_completion` | `scripts/agent/llm_transport_errors.py` `handle_partial_completion` | LLMストリームが部分完了で終わったターン番号・理由・部分テキスト長 |
> | `llm_transport_error` | `scripts/agent/llm_transport_errors.py`、`scripts/agent/session.py` `save_diagnostic` | 部分完了テキストそのもの、または任意の転送エラー詳細 |
> | `guard_hint` | `scripts/agent/tool_loop_guard.py` `_save_guard_hint` | ツールループガード(サイクル検出・重複しきい値超過)発火時のヒント |
> | `transport_failure` | `scripts/agent/tool_runner.py`(`DiagnosticStore.save_transport_failure`) | ツール実行時のトランスポート層失敗(ツール名・server_key・エラー内容) |
> | `serialization_event` | `scripts/agent/tool_runner.py`(`DiagnosticStore.save_serialization_event`) | ラウンド単位の直列化実行イベント |
> | `rag_query` | `scripts/agent/commands/cmd_rag_export.py` | RAGクエリのパイプライン診断(`stage_results`等)。`session_summary` の `rag_query_count`/`rag_stage_outcomes` の集計元 |
>
> `DiagnosticStore` には `save_loop_guard_hint`(kind=`loop_guard_hint`)というメソッドも定義されているが、現行コードからの呼び出し箇所は見当たらない。実際にツールループガードが保存する`kind`は `guard_hint`(`tool_loop_guard.py` `_save_guard_hint` による直接の`save()`呼び出し)である。`loop_guard_hint`というkind名は現状生成されない可能性がある(根拠: Needs confirmation)。
> 同様に `fetch_by_kind` / `fetch_all` という参照系メソッドも `DiagnosticStore` に定義されているが、`scripts/agent/` 配下から実際に呼び出している箇所は確認できなかった(将来のCLI/API用途と推測されるが未確認)(根拠: Needs confirmation)。

**各レコードのフィールド:**

| Field | Description |
|---|---|
| `session_id` | SQLiteのセッション行ID |
| `timestamp` | セッション終了のISO-8601 UTCタイムスタンプ |
| `turns` | 処理された総ターン数 |
| `tool_calls` | 実行された総ツール呼び出し数 |
| `tool_errors` | ツール呼び出しの失敗数 |
| `partial_completions` | LLMの部分完了数(中断されたストリーム) |
| `parse_errors` | SSEパースエラー数 |
| `heartbeat_timeouts` | SSEハートビートタイムアウト数 |
| `reconnects` | LLM転送の再接続数 |
| `semantic_cache_hits` | 一致したセマンティックキャッシュ検索数 |
| `input_tokens` | 入力トークンの総数(取得可能な場合) |
| `output_tokens` | 出力トークンの総数(取得可能な場合) |
| `compress_count` | 履歴圧縮の実行回数 |
| `latency_summary` | ステップごとの平均/最大レイテンシ(ms) |

> **実装との差異(表の追記漏れ):** `scripts/agent/repl.py` の `summary` 辞書には上表に記載のないフィールドが以下のとおり含まれる(根拠: Explicit in code)。
>
> | Field | Description |
> |---|---|
> | `fallback_truncate_count` | フォールバック切り捨て(重要度の低いメッセージ削除)の実行回数 |
> | `workflow_count` | セッション中に開始されたワークフロー数 |
> | `task_count` | セッション中に生成されたタスク数 |
> | `approval_events` | 承認関連イベントの件数 |
> | `retry_count` | タスク実行(`execute`ステージ)のリトライ回数 |
> | `artifacts` | セッション中に生成されたアーティファクトのURI一覧 |
> | `rag_query_count` | セッション中の`kind=rag_query`診断エントリ件数 |
> | `rag_stage_outcomes` | RAGクエリ診断から集約したステージ別結果(`stage_results`)一覧 |
>
> `workflow_count` / `task_count` / `approval_events` / `retry_count` / `artifacts` はワークフロー用DB(`workflow` DB)への問い合わせに失敗した場合、静かに既定値(0または空リスト)にフォールバックする(`try`/`except (RuntimeError, sqlite3.Error)`)(根拠: Explicit in code)。

**診断情報の読み方:**

```bash
# View all diagnostic events (most recent first)
sqlite3 /opt/llm/db/session.sqlite "SELECT id, session_id, kind, created_at FROM session_diagnostics ORDER BY created_at DESC LIMIT 50;"

# Count diagnostics by kind
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, COUNT(*) AS n FROM session_diagnostics GROUP BY kind ORDER BY n DESC;"

# View diagnostics for one session
sqlite3 /opt/llm/db/session.sqlite "SELECT id, kind, content, created_at FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC;"

# View all session summaries
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE kind = 'session_summary' ORDER BY created_at DESC;" | jq .

# Filter sessions with high error rates
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE kind = 'session_summary' AND json_extract(content, '$.tool_errors') > 0 ORDER BY created_at DESC LIMIT 10;" | jq -r '.content'

# Aggregate stats across sessions
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) as total_sessions, AVG(json_extract(content, '$.turns')) as avg_turns, SUM(json_extract(content, '$.tool_errors')) as total_tool_errors FROM session_diagnostics WHERE kind = 'session_summary';"
```

診断情報の永続化に失敗した場合はDEBUGレベルでログに記録され、REPLの終了処理には影響しない(`scripts/agent/repl.py`: `session_summary` 保存を `try`/`except (RuntimeError, sqlite3.Error)` で包み、さらに外側を `except (OSError, sqlite3.Error)` で包む二重防御構成)(根拠: Explicit in code)。`DiagnosticStore.save()` 自体は例外を握りつぶさない実装であり、呼び出し側(`repl.py`、`llm_transport_errors.py`、`tool_loop_guard.py`、`tool_runner.py` 等)がそれぞれ診断保存を失敗させても本処理を止めないよう責任を持って囲んでいる。これは「診断保存の失敗が本来の処理(会話継続やセッション終了)を妨げてはならない」という設計意図を示す(根拠: Strongly implied by code)。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

runtime diagnostics
session-end summary
diagnostic events
