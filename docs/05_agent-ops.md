# エージェント — 起動・確認・トラブルシューティング

ツール仕様・チューニング → [`docs/05_agent.md`](05_agent.md)

## 1. エージェント起動

`agent.py` は CLI REPL ツール。`deploy/deploy.sh` 実行後、LLM サービス (llama-chat-llm または llama-coding-llm) が起動済みであることを確認してから起動。

```bash
# agent.py と関連モジュールを配置する (deploy.sh で一括実施可能)
cp scripts/agent.py          /opt/llm/scripts/
cp scripts/agent_repl.py      /opt/llm/scripts/
cp scripts/config_loader.py   /opt/llm/scripts/

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
