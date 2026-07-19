---
title: "MCP Server Catalog: browser-mcp"
category: mcp
tags:
  - mcp
  - server-catalog
  - browser
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_03_rag-pipeline-and-cicd.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_04_05_git.md
---

# MCP Server Catalog: browser-mcp

## browser-mcp（ポート 8016）

**目的:** 読み取り専用のページ取得・テキスト抽出（対話操作なし; JavaScript 実行なし）。
**起動モード:** subprocess（HTTP）
**設定:** `config/browser_mcp_server.toml`
**認証:** Bearer トークン（`auth_token`）、空文字列の場合は無効

**ツール:**

| ツール | ティア | `requires_config` |
|---|---|---|
| `browser_fetch` | READ_ONLY | yes |

「ティア」列は `scripts/mcp_servers/browser/` 自体には存在しない分類であり、`config/agent.toml` の `[tool_safety_tiers]`（agent 層の承認ポリシー設定）に由来する値である。browser-mcp サーバー実装が内部でティアを判定・保持しているわけではない。(Explicit in code)

**ヘルス:** `/health` は外部依存を一切チェックせず、常に `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"service":"browser-mcp"}}` を HTTP 200 で返す（`server.py::health` が `make_health_response({}, ...)` に空の `deps` を渡すため、`degraded` になることはない）。

**設定:**

| キー | デフォルト | 備考 |
|---|---|---|
| `allowed_domains` | `[]` | fail-closed; 空 = 全て拒否（ホスト名の完全一致） |
| `max_response_kb` | `256` | 抽出テキストのサイズ上限。超過時は切り詰め、`truncated=true` |
| `timeout_sec` | `15` | 取得リクエストのタイムアウト秒数 |
| `auth_token` | `""` | MCP サーバー呼び出し認証用の Bearer トークン |

**注記:** browser-mcp は読み取り専用であり、JavaScript を実行しない（HTML を取得し `BeautifulSoup` で可視テキストを抽出するのみ）。そのため、クライアントサイドでレンダリングされる SPA/React 系ページでは、意味のあるテキストがほとんど、あるいは全く取得できない場合がある。これは意図された仕様であり（Accepted current specification）、バグでも `issues/` への記録対象でもない。

### 実装上の補足

- ホスト名が IP リテラルの場合、`ipaddress.ip_address()` で判定した上で loopback / link-local / private / reserved / multicast のいずれかに該当すれば、`allowed_domains` の内容に関わらず無条件に `BrowserAuthorizationError`（HTTP 403）を送出する。ドメイン許可リストによるチェックとは独立した defense-in-depth の経路である。(Explicit in code, `service.py::BrowserService._check_domain`)
- `url` のスキームは `http`/`https` のみ許可され、それ以外および hostname 欠落は `BrowserValidationError`（HTTP 422）となる。(Explicit in code)
- `max_response_kb` はツール呼び出し側で指定できるが、常にサーバー設定値 `max_response_kb` を上限として `min()` で clamp される（呼び出し側が大きい値を指定してもサーバー上限を超えられない）。(Explicit in code, `service.py::BrowserService.fetch`)
- テキスト切り詰めはバイト列にエンコードしてからスライスする（`_truncate`）。文字単位で素朴に切ると UTF-8 のマルチバイト文字を途中で破壊する可能性があるため。(Explicit in code)

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_04_02_file-write-file-delete-shell.md`
- `04_mcp_04_03_rag-pipeline-and-cicd.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`

## Keywords

mcp
server-catalog
browser-mcp, port 8016
