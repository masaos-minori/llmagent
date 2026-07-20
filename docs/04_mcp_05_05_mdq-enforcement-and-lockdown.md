---
title: "MCP Security and Safety Model: MDQ/RAG Boundary Enforcement, Fail-Open/Fail-Closed Defaults and Deny-All Lockdown"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - mdq
  - rag
  - lockdown
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_04_04_mdq.md
---

# MCP セキュリティと安全性モデル: MDQ/RAG 境界の強制と Fail-Open/Fail-Closed・Deny-All ロックダウン

## 境界の強制

自動化された pytest チェック（`tests/test_mdq_rag_boundary.py`）が、CI 実行ごとに MDQ/RAG の
境界を検証する。エージェント層における、禁止されたクロス DB 参照および許可されない直接 SQLite アクセスを
ソースファイル内でスキャンする。

### 許可されたアクセスパス

| 層 | DB | 機構 | コンテキスト |
|---|---|---|---|
| `mcp_servers/mdq/` | `mdq.sqlite` | 自身のサービス | 通常運用 |
| `scripts/mcp_servers/rag_pipeline/` | `rag.sqlite` | 自身のサービス | 通常運用 |
| エージェント層 | `session.sqlite` | `SQLiteHelper("session")` | 通常運用 |
| エージェント層 | `workflow.sqlite` | `SQLiteHelper("workflow")` | 通常運用 |
| エージェント層 | `rag.sqlite` | `RagMaintenanceService` 経由の `SQLiteHelper("rag")` | 管理者専用の `/db` コマンド |

#### 禁止されたアクセスパス

| 層 | DB | 理由 |
|---|---|---|
| `mcp_servers/mdq/` | `rag.sqlite` | クロス DB 依存 |
| `scripts/mcp_servers/rag_pipeline/` | `mdq.sqlite` | クロス DB 依存 |
| エージェント層（通常時） | `mdq.sqlite` または `rag.sqlite` | 直接 DB アクセスではなく MCP ツールを使用すること |

#### 誤検知への対応

新しい管理者向け保守ファイルが `rag.sqlite` への直接アクセスを必要とする場合は、そのファイル名を
`tests/test_mdq_rag_boundary.py` の `ALLOWED` セットに追加し、その例外を上記の許可パス表に
記載すること。`ALLOWED` への変更には PR での設計レビューコメントが必要である。

---

### mdq-mcp 自身の allowed_dirs 認可（fail-closed）

mdq-mcp は他サーバーとの DB 境界とは別に、ファイルパス単位の fail-closed allowlist を持つ。
`config/mdq_mcp_server.toml` の `allowed_dirs`（デフォルト `[]`）で読み取り対象ディレクトリを
制限し、`scripts/mcp_servers/mdq/auth.py` の `authorize_path()` が実際の許可判定を行う
(Explicit in code)。

- `allowed_dirs` が空の場合、`authorize_path()` は常に `False` を返す — 全パスアクセスを拒否する
  fail-closed 実装(Explicit in code)。
- 判定前に `Path.resolve()` で対象パスと許可ルートの双方を正規化し、`../` トラバーサルや
  シンボリックリンクによる allowlist 外への脱出を防ぐ(Explicit in code)。
- 認可チェックの適用箇所は `MdqService.outline()`（`outline` ツール）、
  パス検証関数（`index_paths`/`refresh_index` ツールが使用）、および
  `search_docs`・`get_chunk`・`grep_docs`（**2026-07-20 に読み取り時の再チェックを追加**、
  下記参照）の計5ツール。違反時は `MdqAuthorizationError` を送出し、HTTP 層では 403 に
  変換される(`scripts/mcp_servers/mdq/server.py` の例外ハンドラ) (Explicit in code)。
- `search_docs`・`get_chunk`・`grep_docs` は、返却前にインデックス済みチャンクの
  `source_path` を現在の `allowed_dirs` に対して `authorize_path()` で再チェックする。
  `search_docs` と `grep_docs`（`paths` 未指定時）は未認可の行を無音で除外し件数にも
  計上しない（fail-closed、未認可結果の存在自体を漏らさない）。`get_chunk` と
  `grep_docs`（`paths` 明示指定時）は未認可対象が含まれる場合、呼び出し全体を
  `MdqAuthorizationError` で拒否する(Explicit in code)。
- `stats` は集計件数のみを返しパス単位のコンテンツを含まないため、
  引き続き `authorize_path()` を経由しない(Explicit in code)。

#### HTTP レベル認証（auth_token）は意図的に無効

mdq-mcp は `attach_auth_middleware(app, "")` という空の Bearer トークンで起動する
ため、HTTP 層でのトークン検証は行われない（`scripts/mcp_servers/server.py` の
`attach_auth_middleware()` docstring: "When token is empty, auth is skipped..."）
(Explicit in code)。

これは見落としではない。`scripts/mcp_servers/mdq/server.py` の `MdqMCPServer`
クラスの docstring には次のように明記されている:
`"auth_token: empty string (no auth required — mdq has its own authorization
via allowed_dirs)"`(Explicit in code)。実際の呼び出しは
`scripts/mcp_servers/mdq/server.py:308`: `attach_auth_middleware(cast(_FastAPIApp, app), "")`。

代わりに、上記の `allowed_dirs`（デフォルト `[]`）ベースのパス認可が実際のセキュリティ
境界として機能する。`allowed_dirs = []` は fail-closed（全パスアクセス拒否）である
(Explicit in code、上記セクション参照)。

> **重要:** 空の `auth_token` は、この 2026-07-16 の MDQ 互換性クリーンアップ一式
> （`audit_log_path`, `concurrency_limit`, `enable_refresh`, embedding/hybrid
> 関連キー, summary-cache 関連キー）で削除された「読み込まれるが強制されない」
> 設定キーとは正反対のケースである。これらは未強制のため削除されたが、
> `auth_token=""` は読み込まれ、その効果（HTTP 認証のスキップ）が完全に強制・
> 意図されている**現行の仕様**であり、削除・「修正」の対象ではない。
>
> 将来 MDQ の HTTP 認証モデルを変更する場合（例: 実際の Bearer トークンを追加する
> 等）は、独立したセキュリティ設計課題として扱うべきであり、互換性クリーンアップ
> の一部として行ってはならない。

---

### 既知の課題

- MDQ-02（解決済み）: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は実装されたことのない
  永続的なプレースホルダーだった（`_search_vector()` は常に空リストを返していた）ため、
  **2026-07-16 に `mode` パラメータを `bm25` のみに制限し、関連コード（`_search_vector()`,
  `_merge_hybrid()`, `_RRF_K`）と設定項目（`use_embedding`, `embedding_dims`,
  `vector_table`, `embedding_model`）を完全に削除した**(Explicit in code)。
  セマンティック検索が必要な場合は RAG パイプラインを使用する。
- `scripts/mcp_servers/mdq/tools.py` の `TOOL_LIST` に `fts_consistency_check` と `fts_rebuild`
  が `status: "admin"` として定義されていたが、`scripts/mcp_servers/mdq/server.py` の
  `_DISPATCH_TABLE` にハンドラが登録されておらず、呼び出すと「Unknown tool」エラーとなる
  スキーマ・設定・実行経路間の不整合があった。運用上この2ツールを呼び出すクライアントは
  存在せず、正式な配線（safety tier・serialization・audit・テスト整備）を行う積極的な
  要件もないため、**2026-07-16 に両ツールをスキーマ（`TOOL_LIST`）、モデル（`models.py`）、
  サービス層（`service.py`）、`db_fts.py`、レジストリ（`tool_constants.py`）、設定
  （`config/agent.toml`）から完全に削除した**。実装は git 履歴（`db_fts.py` 削除前の
  リビジョン）から復元可能(Explicit in code)。
- `mdq_mcp_server.toml` の `concurrency_limit` は、`scripts/mcp_servers/mdq/` 配下および
  リポジトリ全体のどこからも参照されていないことを確認した（`grep -rn '"concurrency_limit"'`
  でヒットなし）ため、**2026-07-13 に設定ファイルから削除した**。実際の直列化は `MdqService`
  内の `asyncio.Lock`（`_index_lock`）により `index_paths`/`refresh_index` に対してのみ
  達成されており、設定値には依存しない(Explicit in code)。
- **直列化モデルの詳細:** `index_paths` と `refresh_index` はいずれも
  `MdqService._index_lock`（遅延生成される `asyncio.Lock`）を実行前に取得し、
  同時実行を防ぐ(Explicit in code)。これは `tools.py` の `requires_serial: True`
  （`scripts/agent/tool_scheduler.py` が1エージェントターン内の同時ツール呼び出しに対して
  適用するグローバルなバリア）とは別の、独立した直列化機構である。両者は補完的であり、
  いずれも削除・統合の対象ではない。この直列化が実際に機能することは
  `tests/test_mdq_index_serialization.py` で検証されている。
- `mdq_mcp_server.toml` の `enable_refresh` は、`refresh_index()` にゲートチェックが
  一度も実装されなかった（読み込まれるが常に無視される）ため、
  **2026-07-16 に `service.py` と設定ファイルから削除した**。対照的に `enable_grep` は
  `grep_docs()` 内で実際に強制されており（`not self.enable_grep` の場合
  `MdqValidationError` を発生させる）、`tests/test_mdq_service.py`
  の `TestGrepDocsConfigGate` でテストされている — 両者は設定上似ているが、
  一方のみが実際の挙動に接続されている(Explicit in code)。
- `chunks` テーブルの `tags_json` と `token_count` は、これまで `scripts/mcp_servers/mdq/indexer.py`
  の `_index_single_file()` 内で常に `""` / `None` としてハードコードされたプレースホルダー
  だったが、**2026-07-19 に実データを格納するよう変更した**。`tags_json` は
  `scripts/mcp_servers/mdq/parser.py` の `parse_markdown()` が YAML frontmatter の `tags:`
  フィールド（リスト形式・カンマ区切り文字列形式のどちらも可）を抽出した結果を JSON 配列と
  して格納する。`token_count` はローカルなヒューリスティック（`len(content) // 4`）による
  概算値であり、正確なトークナイザーによる値ではない。`search_docs` の `tag_filter` は
  `scripts/mcp_servers/mdq/search.py` の既存の `tags_json LIKE` 条件により、この実データに
  対して照合されるようになった(Explicit in code)。

---

## Fail-open 対 Fail-closed のデフォルト

「Fail-closed」とは、リストが空の場合にその設定がアクセスを拒否することを意味する。
「Fail-open」とは、リストが空の場合にその設定が全アクセスを許可することを意味する。

| サーバー | 設定 | デフォルト | 空の場合の挙動 |
|---|---|---|---|
| shell-mcp | `command_allowlist` | `[]` | **Fail-closed** — 全シェルコマンドを拒否 |
| git-mcp | `allowed_repo_paths` | `[]` | **Fail-closed** — 全リポジトリアクセスを拒否 |
| github-mcp | `allowed_repos` | `[]` | **Fail-closed** — 全 GitHub 書き込み操作を拒否 |
| cicd-mcp | `workflow_allowlist` | `[]` | **Fail-closed** — 全ワークフロートリガーを拒否 |

### 本番デプロイ前に確認すべき危険なデフォルト値

- `shell-mcp`: `sandbox_backend = "none"`（デフォルト）は OS レベルのサンドボックスがないことを意味する。
  本番環境では `"firejail"` を設定すること; `/health` レスポンスで確認可能。
- `cicd-mcp`: `workflow_allowlist = []` は fail-closed（全拒否）である; 許可するワークフローを明示的に列挙すること。
- `github-mcp`: `allow_force_push = false`（デフォルト）; `require_pr_review = true`（デフォルト）。

### 起動時の audit

  `agent/repl_health.py` の `audit_security_defaults()` は起動時に実行され、以下をログに記録する。
- 空である全ての fail-closed 設定（情報提供 — アクセスは正しく拒否されている）
- 空である全ての fail-open 設定（警告 — 意図しないアクセスが許可される可能性がある）
- 要約行: `Security posture summary — fail-closed (...): ...; fail-open (...): ...`

**mdq-mcp はこの起動時 audit の対象外である。** `audit_security_defaults()` が明示的に
チェックするのは `shell.command_allowlist`・`git.allowed_repo_paths`・`github.allowed_repos`・
`cicd.workflow_allowlist` の4設定のみで、mdq-mcp の `allowed_dirs` は `fail_closed_empty` /
DENY-ALL 警告ロジックに含まれていない(Explicit in code)。したがって
`mdq_mcp_server.toml` の `allowed_dirs = []`（deny-all 状態）は、他の fail-closed 設定と異なり
起動ログに警告として出力されない。運用上は `04_mcp_05_01_access-control-and-allowlists.md`
の「サーバー別アクセス制御」表と本ドキュメントの記載を頼りに手動で確認する必要がある
(Strongly implied by code)。

---

## 意図的な deny-all ロックダウン

空の fail-closed allowlist は、MCP サーバーの操作カテゴリ全体を無効化する。
これは、特定のツールカテゴリを完全に禁止したいセキュリティ制限付きデプロイメント
（例: シェルコマンド禁止、DB クエリ禁止）における正しい挙動である。

### deny-all を引き起こす設定

| 設定 | サーバー | 空の場合の効果 |
|---------|--------|-------------------|
| `shell.command_allowlist` | shell-mcp | 全シェルコマンドを拒否 |
| `git.allowed_repo_paths` | git-mcp | 全 git 操作を拒否 |
| `github.allowed_repos` | github-mcp | 全リポジトリアクセスを拒否 |

mdq-mcp の `allowed_dirs` も同種の fail-closed 設定（空 = 全パスアクセス拒否）だが、
上表・`security_lockdown_enabled` による警告抑制ロジックのいずれにも含まれていない
（前節「起動時の audit」参照）。mdq-mcp のロックダウンは設定ファイル上は成立するが、
起動ログ上の deny-all 通知・抑制の対象にはならない(Explicit in code)。

### 意図的なロックダウンの設定方法

1. 該当する TOML で、対象の allowlist を空に設定する。
   ```toml
   # shell_mcp_server.toml
   command_allowlist = []   # deny all shell commands
   ```

2. 起動時の警告を抑制するため、`config/agent.toml` でロックダウンを明示的に認める。
   ```toml
   [agent]
   security_lockdown_enabled = true
   ```

3. エージェントを再起動する。起動ログには以下が表示される。
   ``` text
   INFO Security: security_lockdown_enabled=True — deny-all warnings suppressed
   ```

### ランタイムでの deny-all 状態の確認

起動時、`audit_security_defaults()` は各 deny-all 状態をログに記録する。
``` text
WARNING DENY-ALL detected: shell.command_allowlist is empty. shell-mcp will
        reject ALL shell commands. Verify this is intentional or add allowed
        commands to shell_mcp_server.toml.
```

`security_lockdown_enabled=False`（デフォルト）の場合、これらの警告は起動ごとに
表示される — これは config を見直すよう促す意図的なリマインダーである。deny-all の状態が
意図的であると確認できた場合にのみ `true` に設定すること。有効化した場合:
- fail-closed 設定（`command_allowlist`, `db_allowlist`, `allowed_repo_paths`）に対する DENY-ALL 警告は抑制される
- fail-open の警告（`tool.allowed_tools`）は引き続き表示される
- セキュリティ姿勢の要約行は詳細情報付きで引き続き表示される

### ロックダウンの解除

該当する TOML に許可値を戻し、
`security_lockdown_enabled = false` を設定する。適用するにはエージェントを再起動すること。

---

## Fail-Open / Fail-Closed 設定のレビュー

| 設定 | デフォルト | fail-open 時の挙動 | 本番環境での推奨 |
|---|---|---|---|
| `tool_definitions_strict` | `true` | `false` = スキーマ不一致が WARNING に格下げされる | `true` を維持する |
| `shell_sandbox_backend` | `"none"` | `"none"` = OS 分離なし | 本番環境では `"firejail"` を設定する |
| `workflow_allowlist`（cicd-mcp） | `[]` | `[]` = 全トリガーを拒否（fail-closed） | 許可するワークフローを明示的に列挙する |
| `command_allowlist`（shell-mcp） | `[]` | `[]` = 全コマンドを拒否（fail-closed） | 許可するコマンドを列挙する |
| `allowed_dirs`（mdq-mcp） | `[]` | `[]` = 全パスアクセスを拒否（fail-closed）; ただし起動時 audit の対象外(Explicit in code) | 読み取りを許可するディレクトリを明示的に列挙する |

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_04_04_mdq.md`

## Keywords

mcp
security
safety-model
mdq-rag-boundary-enforcement
deny-all
lockdown
fail-open
fail-closed
security-audit
mdq-allowed-dirs
authorize-path
mdq-authorization-error
fts-consistency-check
fts-rebuild
