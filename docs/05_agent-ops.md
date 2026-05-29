# エージェント — 起動・確認・トラブルシューティング

ツール仕様・チューニング → [`docs/05_agent.md`](05_agent.md)

## 1. エージェント起動

`agent.py` は CLI REPL ツール。`deploy/deploy.sh` 実行後、LLM サービス (llama-chat-llm または llama-coding-llm) が起動済みであることを確認してから起動。

```bash
# agent.py とパッケージ群を配置する (deploy.sh で一括実施可能)
cp scripts/agent.py                /opt/llm/scripts/
cp -r scripts/agent               /opt/llm/scripts/agent
cp -r scripts/shared              /opt/llm/scripts/shared

# エージェントを起動する
# agent.py 先頭で sys.path を自動設定するため、任意のディレクトリから起動可能
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
```

---

## 2. 動作確認

エージェントが正常に起動して対話できることを確認。DB 統計でドキュメント・チャンクが投入済みであることも確認。

```bash
# DB 統計
sqlite3 /opt/llm/db/rag.sqlite \
    "SELECT lang, COUNT(*) AS docs FROM documents GROUP BY lang;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT COUNT(*) AS chunks FROM chunks;"
sqlite3 /opt/llm/db/rag.sqlite \
    "SELECT chunk_id, LENGTH(embedding) AS bytes FROM chunks_vec LIMIT 3;"
# 期待値: bytes = 1536 (384 次元 × 4 bytes)

# ログ確認
tail -f /opt/llm/logs/agent.log
```

CLI セッション例:

```
$ python /opt/llm/scripts/agent.py
DB: 12,345 chunks | Tools: 14 | Mode: chat
Type /help for commands, /exit to quit.

agent[chat]> llama.cpp の最新バージョンを調べて教えてください
  [tool] search_web({"query": "llama.cpp latest version"})
  [tool] search_web → 28 lines / 1842 chars (truncated)

llama.cpp の最新バージョンは b5210 (2025-05 時点) です。...

agent[chat]> /mcp
Transport : http
  web-search-mcp  :8004  (1 tool)
    - search_web
  file-mcp        :8005  (8 tools)
    - list_directory
    - ...
  github-mcp      :8006  (5 tools)
    - github_search_repositories
    - ...
Connectivity:
  web-search-mcp  :8004              OK
  file-mcp        :8005              OK
  github-mcp      :8006              OK

agent[chat]> /exit
$
```

---

## 6. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `embedding attempt 3/3` 全失敗 | embed-llm 未起動または過負荷 | `rc-service embed-llm status` 確認、モデルロード完了まで待機 |
| `AttributeError: enable_load_extension` | Python が sqlite 拡張なしでビルドされている | `echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python && emerge dev-lang/python` |
| `no such table: chunks_vec` | sqlite-vec 拡張のロード失敗 | `ls /opt/llm/sqlite-vec/vec0.so` でファイル確認 |
| FTS 検索で 0 件 | chunks_fts と chunks が不整合 | `SELECT COUNT(*) FROM chunks_fts` と `FROM chunks` を比較 |
| `blob_bytes` が 1536 以外 | 埋込次元数が異なる | `EMBED_URL` のモデルが 384 次元を出力しているか確認 |
| `Sudachi tokenize error` 多発 | sudachidict-core 未インストール | `pip install sudachidict-core` |
| llama-server が起動しない | モデルファイルのパスまたは権限 | `ls -lh /opt/llm/models/` でファイル確認 |
| レイテンシが非常に高い | 複数モデルが同時ロードで RAM 枯渇 | `--threads` を調整し合計が 4 以下になるよう設定 |

---

## 7. Observability — ログ・スパンによる切り分け手順

### 7.1 ターン単位の elapsed_ms を確認する

```bash
# audit.log でターン完了イベントの elapsed_ms を tail + jq でフィルタ
tail -f /opt/llm/logs/audit.log | jq 'select(.event == "turn_end") | {turn_id: .task_id, elapsed_ms}'
```

期待出力例:

```json
{"turn_id": "a1b2c3d4-...", "elapsed_ms": 1234.5}
```

### 7.2 OpenTelemetry スパンを確認する (otel_enabled=true, otel_endpoint="")

`config/agent.toml` で `otel_enabled: true` かつ `otel_endpoint: ""` に設定すると、
ConsoleSpanExporter がスパンを標準出力 / `agent.log` に書き出す。

```bash
# agent.log でスパン名 ("rag", "compress", "llm") を含む行を抽出
tail -f /opt/llm/logs/agent.log | grep '"name":'
```

期待出力例 (スパン JSON の一部):

```json
{"name": "rag", "context": {"trace_id": "0x...", "span_id": "0x..."}, ...}
{"name": "compress", ...}
{"name": "llm", "attributes": {"model_url": "http://127.0.0.1:8002/..."}, ...}
```

### 7.3 トークンメトリクスを確認する

LLM エンドポイントが `usage` フィールドを返す場合、audit.log に `input_tokens` /
`output_tokens` が記録される。

```bash
tail -f /opt/llm/logs/audit.log \
  | jq 'select(.input_tokens != null) | {turn_id: .task_id, input: .input_tokens, output: .output_tokens}'
```

期待出力例:

```json
{"turn_id": "a1b2c3d4-...", "input": 512, "output": 128}
```

ローカル LLM が `usage` を返さない場合は `null` になる。その場合 `/context` コマンドの
`Token estimate` 行 (chars / 4 の推定値) を参照する。

### 7.4 /context コマンドで token / memory 状態を確認する

```
agent[chat]> /context
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  System preview  : 'あなたは有能なエンジニアアシスタント...'
  Token estimate  : 1,080 (chars / 4)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 28%)
  rag           :    2,000 chars ( 46%)
  history       :      987 chars ( 22%)
  tool_results  :      100 chars (  2%)
```

`Memory layer : enabled (entries=N)` と表示された場合、MemoryLayer が有効で N 件のエントリが存在する。
