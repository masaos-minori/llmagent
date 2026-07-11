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
| コンテキスト圧縮(HistoryManager) | `/stats` で `Compress: N > 0` と表示される。エージェントログ: `INFO Compressed history` | `compression_char_threshold` を増やす、またはコンテキストサイズを削減する |
| 最大ツールターン数に到達 | エージェントログ: `WARNING max_tool_turns=N reached` | `config/agent.toml` の `max_tool_turns` を増やす |

正式な部分完了モデルについては → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md)。

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

診断情報の永続化に失敗した場合はDEBUGレベルでログに記録され、REPLの終了処理には影響しない。

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
