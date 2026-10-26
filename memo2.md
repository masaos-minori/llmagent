以下のファイル一覧の計画書を順番に読み込み、敵対的検証を実施し、検証結果を反映してください。
計画書が Draft であれば、関連する実装とドキュメントを読み込んで、Frozen になるように調査してください。

検証後に計画書を読み直し、作業順を考慮して実装手順書を作成してください。
各計画書から実装手順書を作成した後に以下のファイル一覧から作業が完了した計画書ファイル名を削除してください。
作業が終了した計画書はアーカイブしてください。

## 完了済み（2026-10-26）

- ~~plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md~~ — 未存在
- ~~plans/20261025-120857_eventbus005_nack-idempotency-retries.md~~ — 未存在
- ~~plans/20261026-222848_mcp001_systemexit-not-caught-by-run_http.md~~ — 完了（server.py: SystemExit捕捉追加）
- ~~plans/20261026-223206_mcp004_contextvars-contextvar-cross-request-leakage.md~~ — 完了（mdq_server.py: ContextVar default=None化、set()ガード追加）
- ~~plans/20261026-223348_mcp005_repositorystate-repo-no-cleanup.md~~ — 完了（repository_state.py: close()/コンテキストマネージャー追加）
- ~~plans/20261026-223522_mcp006_web-search-broad-except-in-call-tool.md~~ — 完了（web_search_server.py: error_type=type(e).__name__化）
- ~~plans/20261026-223655_mcp007_classify-dispatch-error-fragile-string-prefix.md~~ — 完了（dispatch.py: error_typeフィールド追加、web_search_server.py: 構造化分類へ移行）
- ~~plans/20261026-223840_mcp008_sanitize-for-audit-leaks-sensitive-paths.md~~ — 完了（git_server.py: len(parts)<=3化）
- ~~plans/20261026-224032_mcp009_validate-pre-snapshot-blocking-os-path-calls.md~~ — 完了（git_server.py: asyncio.to_thread()ラッパー追加）
- ~~plans/20261026-224227_mcp010_git-mcp-server-missing-dispatch-override.md~~ — 完了（git_server.py: dispatch()メソッド追加）
- ~~plans/20261026-224412_mcp011_git-mcp-server-missing-http-host-attribute.md~~ — 完了（git_server.py: http_host="127.0.0.1"追加）
- ~~plans/20261026-224641_mcp012_git-audit-failure-count-mutable-global-no-synchronization.md~~ — 完了（git_server.py: threading.Lock追加）
- ~~plans/20261026-224700_mcp013_file-delete-audit-target-truncation-loses-context.md~~ — 完了（delete_server.py: requested_target追加）
