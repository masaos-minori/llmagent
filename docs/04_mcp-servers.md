# MCP サーバ (インデックス)

各 MCP サーバの詳細は下記ファイルを参照。

| ファイル | 内容 |
|---|---|
| [`04_mcp-web-search.md`](04_mcp-web-search.md) | §1 web-search-mcp — Web 検索機能 (ポート 8004) |
| [`04_mcp-file.md`](04_mcp-file.md) | §1 file-mcp — ローカルファイル操作 (ポート 8005, 8007, 8008) |
| [`04_mcp-github.md`](04_mcp-github.md) | §1 github-mcp — GitHub 操作 (ポート 8006) |
| [`04_mcp-protocol.md`](04_mcp-protocol.md) | §1 HTTP API フォーマット / §2 トランスポートモード・追加手順 |
| [`04_mcp-rag.md`](04_mcp-rag.md) | §1 rag-pipeline-mcp — RAG パイプライン (ポート 8010) |
| [`04_mcp-cicd.md`](04_mcp-cicd.md) | §1 cicd-mcp — GitHub Actions 操作 (ポート 8012) |
| [`04_mcp-mdq.md`](04_mcp-mdq.md) | §1 mdq-mcp — Markdown コンテキスト圧縮エンジン (ポート 8013) |
| [`04_mcp-git.md`](04_mcp-git.md) | §1 git-mcp — ローカル git 操作 (ポート 8014) |

`shell-mcp` (ポート 8009) は単独のドキュメントファイルを持たない。実装: `mcp/shell/server.py` / `mcp/shell/service.py`。ツールは `shell_run` 1 種のみ。`shared/tool_constants.py` には含まれず、`route_resolver.py` の静的 fallback で `"shell"` サーバキーに直接マッピングされる。

`sqlite-mcp` (ポート 8011) は単独のドキュメントファイルを持たない。仕様は `CLAUDE.md` の「SQLite MCP (eighth server)」セクションおよび実装 (`mcp/sqlite/server.py` / `mcp/sqlite/service.py`) を参照。ツールは `query_sqlite` 1 種のみ (SELECT のみ許可、`db_allowlist` で対象 DB を制限、`max_rows` 件で上限、`PRAGMA query_only=ON` で書き込み禁止)。
