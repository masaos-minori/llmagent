# MCP セキュリティと安全性モデル

- サーバーカタログ → [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md)

## 目的

サーバー間共通のセキュリティモデルを文書化する。対象はアクセス制御、allowlist、denylist パターン、
fail-open 対 fail-closed の方針、サンドボックス、出力制限、リスクティア、AI 安全性に関する注記。

---

## サーバー別アクセス制御

| サーバー | 制御機構 | デフォルトポリシー |
|---|---|---|
| file-read-mcp | `allowed_dirs` | `["/opt/llm", "/opt/llm/storage"]` — パスジェイル |
| file-write-mcp | `allowed_dirs`（書き込み） | `["/opt/llm/storage"]` — パスジェイル |
| file-delete-mcp | `allowed_dirs` | `["/opt/llm/storage"]` — パスジェイル |
| github-mcp | `allowed_repos` | fail-closed（空 = 全書き込みを拒否） |
| shell-mcp | `command_allowlist` + `shell_cwd_allowed_dirs` | 全拒否（デフォルトでは両方とも空） |
| cicd-mcp | `repo_allowlist` + `workflow_allowlist` | 両方とも: fail-closed |
| git-mcp | `allowed_repo_paths` + `read_only` | fail-closed（空パス = 全て拒否); read_only=true |
| mdq-mcp | `allowed_dirs` | fail-closed（デフォルト `[]` = 全て拒否); `MdqAuthorizationError` を発生させる |

---

## パス制御

### `allowed_dirs`（ファイルサーバー）

```toml
# config/file_read_mcp_server.toml
allowed_dirs = ["/opt/llm", "/opt/llm/storage"]
```

- 全パスは比較前に `Path.resolve()` で解決される（`../` やシンボリックリンクを排除）
- `allowed_dirs` 外へのアクセス → HTTP 403
- 空リストの挙動: 全アクセスを拒否（fail-closed）

### `allowed_repo_paths`（git-mcp）

```toml
# config/git_mcp_server.toml
allowed_repo_paths = ["/opt/llm/myrepo"]
```

- パスはサーバー起動時に `Path.resolve()` で正規化される
- 空 → 全リポジトリアクセスを拒否（fail-closed）

---

## リポジトリ制御

### `allowed_repos`（github-mcp）

```toml
allowed_repos = ["org/myrepo", "org/otherrepo"]
```

- 空 → 全リポジトリアクセスを拒否（fail-closed）
- 空でない → リストされたリポジトリのみ許可

以下の9個の書き込み操作に適用される: `github_create_branch`, `github_create_or_update_file`, `github_push_files`,
`github_delete_file`, `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`,
`github_update_pull_request`, `github_merge_pull_request`。

### `repo_allowlist`（cicd-mcp）

```toml
repo_allowlist = []   # IMPORTANT: empty = deny all (fail-closed)
```

---

## ブランチとパスの Denylist（github-mcp）

### `protected_branches`

```toml
# config/github_mcp_server.toml
protected_branches = ["main", "master", "release/*"]   # fnmatch patterns
```

- 対象ブランチを指定する書き込み操作に適用される
- 空リスト（デフォルト）: 全ブランチを許可
- `branch=""`（省略時）: チェック前に API 経由でデフォルトブランチを解決する

**本番環境の例:**

```toml
# Protect mainline branches and release branches
protected_branches = [
    "main",
    "master",
    "release/*",
    "develop",
]
```

この設定では、`main`, `master`, `release/v1.0`, `develop` を対象とする書き込み操作は、承認によって明示的に上書きされない限りブロックされる。

### `path_denylist`

```toml
# config/github_mcp_server.toml
path_denylist = [".github/**", "Dockerfile*"]   # fnmatch glob patterns
```

- `create_or_update_file`, `push_files`, `github_delete_file` に適用される
- 空リスト（デフォルト）: 全パスを許可

**本番環境の例:**

```toml
# Prevent modifications to CI/CD configs and container definitions
path_denylist = [
    ".github/**",           # block changes to GitHub Actions/workflows
    "Dockerfile*",          # block changes to Docker files
    "docker-compose*.yml",  # block changes to docker compose configs
]
```

この設定では、GitHub Actions のワークフローファイルや Docker 関連ファイルへの変更は、承認状態に関わらずブロックされる。

### `allow_force_push`

```toml
# config/github_mcp_server.toml
allow_force_push = false   # default: force push disabled
```

- 保護対象ブランチで `force-push` 操作を許可するかどうかを制御する
- **推奨: 本番環境では `false` を維持する。** Force push は履歴を書き換え、チームの共同作業を破壊する可能性がある。
- `true` の場合、force push は `protected_branches` の保護を回避する。

**本番環境の例:**

```toml
# NEVER enable force push in production
allow_force_push = false
```

正当な force push が必要な場合（例: rebase 後のコミットの squash）は、この設定を有効化するのではなく、適切な権限を持つ GitHub の UI を直接使用すること。

### `require_pr_review`

```toml
# config/github_mcp_server.toml
require_pr_review = true   # default: PR review required
```

- `true` の場合、保護対象ブランチへの書き込み操作にはプルリクエストが必要（直接コミット不可）
- `false` の場合、保護対象ブランチへの直接コミットが許可される（他の保護の対象となる）

**本番環境の例:**

```toml
# Require PR review for all protected branch writes
require_pr_review = true
```

これにより、`main`, `master`, `release/*` ブランチへの変更は、プルリクエストを介した標準的なコードレビュープロセスを経ることが保証される。

---

## コマンド Allowlist（shell-mcp）

```toml
command_allowlist = ["ls", "cat", "grep", "git", "python3"]
```

- `argv[0]` のベース名にマッチする
- 空 → 全コマンドを拒否（fail-closed の挙動）
- `shell_cwd_allowed_dirs` が空 → 全ての `cwd` 値を拒否

### 環境変数のフィルタリング

```
env_allowlist non-empty  → keep only listed keys (denylist ignored)
env_allowlist empty      → remove denylist pattern matches
both empty               → use req.env as-is
```

---

## ワークフロー Allowlist（cicd-mcp）

```toml
# config/cicd_mcp_server.toml
workflow_allowlist = []   # empty = deny all (fail-closed)
```

**方針: fail-closed。** `workflow_allowlist` が空の場合、全てのワークフロートリガーリクエストは
`CicdAuthorizationError` で拒否される。これは `repo_allowlist` の挙動と一致する。

特定のワークフローを許可するには:

```toml
workflow_allowlist = [
    "my-org/my-repo/.github/workflows/deploy.yml",
    "my-org/my-repo/.github/workflows/ci.yml",
]
```

`workflow_allowlist` が空の場合、起動時に以下の警告が出力される:
`DENY-ALL detected: cicd.workflow_allowlist is empty. cicd-mcp will reject ALL workflow trigger requests.`

**この変更以前:** 空リストは全ワークフローを許可していた（fail-open）が、これは新規デプロイされたサーバーにおける
設定ミスのリスクであった。

---

## `read_only` フラグ（git-mcp）

```toml
read_only = true   # default: all write tools return [DENIED]
```

`true` の場合: `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` は全て承認の有無に関わらず
`[DENIED]` を返す。書き込みを有効にするには明示的に `false` を設定する。

---

## 認証（`auth_token`）

```toml
# In server config or McpServerConfig
auth_token = ""   # empty = no auth
```

空でない場合: サーバーは `Authorization: Bearer <token>` ヘッダーを要求する。
欠落または不一致 → HTTP 401。
適用対象: 全サーバー（`McpServerConfig.auth_token` によりサーバーごとに設定）。

**ローカル/開発環境の互換性:** `auth_token=""`（Bearer 認証なし）は意図的な
ローカル/開発環境の互換性のための挙動であり、見落としではない。**空の `auth_token` は
本番環境で使用してはならない** — これを拒否する起動時の強制については、
下記の [Security Profile](#security-profile-security_profile) を参照。

---

## セキュリティプロファイル（`security_profile`）

```toml
# In config/agent.toml [mcp_servers] section
security_profile = "local"   # or "production"
```

HTTP MCP サーバーに Bearer トークン認証が必須かどうかを制御する。

| プロファイル | 挙動 |
|---|---|
| `local`（デフォルト） | 認証は任意。HTTP サーバーで `auth_token` が欠落している場合、起動時に warning が出力される。 |
| `production` | 認証が必須。いずれかの HTTP サーバーに `auth_token` がない場合、起動は `RuntimeError` で失敗する。 |

**強制のポイント:** `agent/repl_health.py` の `audit_security_defaults()` は、`security_profile == "production"` かつ HTTP サーバーの `auth_token` が空の場合、起動時に例外を発生させる。また `shell_sandbox_backend == "none"` および空の `tool.allowed_tools` についても警告する。

**リロードの境界:** `/reload` はこのチェックを再実行することはなく、実行中の MCP サーバーに
`auth_token` の変更を適用することもない — トークンの変更は常に再起動が必要として
報告される（[Configuration: Hot-reload eligibility](05_agent_08_01_configuration-loading-agent-config.md#config-file-ownership-and-hot-reload-eligibility) を参照）。
本番環境の認証検証は起動時にのみ実行される; これを弱めたり回避したりできるランタイムパスは存在しない。

**Audit API の分離:** `agent/security_audit_config.py` は、MCP サーバーの config モデル（`mcp_servers.shell.models`, `mcp_servers.git.models`, `mcp_servers.github.models_config`, `mcp_servers.cicd.models`）をインポートする、エージェント層における唯一の許可されたポイントである。4つの狭いスコープの DTO（`ShellAuditConfig`, `GitAuditConfig`, `GitHubAuditConfig`, `CicdAuditConfig`）と、オプションの依存関係（`ImportError` → `None`）および config 読み込み失敗（`Exception` → `RuntimeError`）を処理する4つのローダー関数を公開する。

---

## 出力とリソースの制限

| 上限 | デフォルト | サーバー |
|---|---|---|
| 最大レスポンスバイト数 | 512 KB（`MCP_MAX_RESPONSE_BYTES = 524288`） | 全サーバー（切り詰め） |
| shell 最大出力 | 4096 KB（config） | shell-mcp |
| shell 最大メモリ | 512 MB（`RLIMIT_AS`） | shell-mcp |
| shell 最大タイムアウト | 300秒（config） | shell-mcp |
| git_show 最大文字数 | 8000文字 | git-mcp |
| cicd ログ上限 | 256 KB / 5ジョブ | cicd-mcp |
| file 最大読み取り | 1 MB（config） | file-read-mcp |
| file 最大書き込み | 1 MB（config） | file-write-mcp |
| GitHub per_page | 100（config） | github-mcp |

---

## サンドボックスバックエンド（shell-mcp）

```toml
# Development:
shell_sandbox_backend = "none"    # WARNING at startup; no isolation
# Production:
shell_sandbox_backend = "firejail"  # RuntimeError at startup if binary missing
```

| バックエンド | 使用場面 | 本番環境で必要か | 起動時の挙動 |
|---|---|---|---|
| `firejail` | プロセス分離、制限されたファイルシステム | **必須** | バイナリ欠落時は RuntimeError |
| `none` | 開発専用 — 分離なし | No | WARNING をログ出力; 本番モードでは RuntimeError |

- `"firejail"`: argv の先頭に `["firejail", "--private", "--net=none", "--noroot", "--"]` を付加する
- `"none"`: サンドボックスなし; `RLIMIT_*` のリソース制限のみ適用

**起動時の強制**（plan 20260626-091916 で追加）:
- `backend == "firejail"` かつ `shutil.which("firejail")` が None を返す場合 → 起動時に `RuntimeError`
- `backend != "firejail"` かつ `backend != "none"` の場合 → 起動時に WARNING
- 本番モードで `backend == "none"` の場合 → `RuntimeError`

firejail のインストール: `sudo apt-get install firejail`（Debian/Ubuntu）または `apk add firejail`（Alpine）。
確認: `firejail --version`

**リソース制限**（`preexec_fn` 経由で適用）: `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_NOFILE`,
`RLIMIT_NPROC`, `RLIMIT_FSIZE`

---

## Fail-Open 対 Fail-Closed の要約

| 制御 | ポリシー | 空/未設定時の挙動 |
|---|---|---|
| `allowed_dirs`（file-read/write/delete-mcp） | Fail-closed | 全アクセスを拒否 |
| `allowed_dirs`（mdq-mcp） | Fail-closed | パスを受け取る全ツールを拒否（`MdqAuthorizationError`） |
| `allowed_repos`（github-mcp, fail_closed モード） | Fail-closed | 全書き込みを拒否 |
| `allowed_repos`（github-mcp, fail_open モード） | Fail-open | 全リポジトリを許可 |
| `allowed_repo_paths`（git-mcp） | Fail-closed | 全アクセスを拒否 |
| `repo_allowlist`（cicd-mcp） | Fail-closed | 全リポジトリを拒否 |
| `workflow_allowlist`（cicd-mcp） | **Fail-closed** | 全ワークフローを拒否 |
| `command_allowlist`（shell-mcp） | Fail-closed | 全コマンドを拒否 |
| `path_denylist`（github-mcp） | Fail-open（デフォルトでブロックなし） | 全パスを許可 |
| `protected_branches`（github-mcp） | Fail-open（デフォルトでブロックなし） | 全ブランチを許可 |

### 起動時の Audit

`agent/repl_health.py` の `audit_security_defaults()` はエージェント起動時に実行され、
セキュリティ姿勢の要約をログに出力する。各サーバーの config ファイルを読み込み、以下の設定をチェックする。

| 設定 | サーバー config ファイル | チェック内容 |
|---|---|---|
| `shell_sandbox_backend` | `shell_mcp_server.toml` | `"firejail"` + バイナリ欠落時は RuntimeError; `"firejail"` または `"none"` 以外の場合は WARNING; 本番環境で `"none"` の場合は RuntimeError |
| `command_allowlist` | `shell_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |
| `allowed_repo_paths` | `git_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |
| `workflow_allowlist` | `cicd_mcp_server.toml` | 空の場合（fail-closed）DENY-ALL 警告 |

空の allowlist に対する警告は以下の形式を使用する: `DENY-ALL detected: {setting} is empty. {server} will reject ALL requests from this category. Verify this is intentional or add allowed values to config.`

チェックの最後に、以下の要約行がログに出力される。

```
Security posture summary — fail-closed (deny when empty): <list>; fail-open (allow when empty): <list>
```

Fail-closed 設定が空であることは意図された安全なデフォルトである（アクセスが拒否される）。Fail-open
設定が空であることは、無制限のアクセスを許可してしまうため警告として強調される。

---

## Dry-Run のサポート

`dry_run=True`（副作用のない実行前プレビュー）をサポートするツール:

| サーバー | dry_run をサポートするツール |
|---|---|
| file-write-mcp | `write_file`, `edit_file`, `create_directory`, `move_file` |
| file-delete-mcp | `delete_file`, `delete_directory` |
| shell-mcp | `shell_run` (arg: `dry_run`) |
| git-mcp | `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| cicd-mcp | `trigger_workflow` |

**cicd-mcp の注記:** リポジトリとワークフローの allowlist チェックは、`handle_trigger_workflow` 内の `dry_run` バイパスよりも先に実行される。拒否対象のリクエストは `dry_run=True` であっても常に拒否される。

エージェントレベル: `config/agent.toml` の `approval_dry_run_tools` は、確認プロンプトを表示する前に
承認フローが自動で `dry_run=True` を実行するツールを列挙する。

---

## リスクティア分類

ツールのリスクティア（`config/agent.toml::tool_safety_tiers` から）:

| ティア | 例 | 承認方式 |
|---|---|---|
| `READ_ONLY` | `read_text_file`, `git_status`, `search_web`, `rag_run_pipeline` | 自動承認 |
| `WRITE_SAFE` | `write_file`, `edit_file`, `git_add`, `git_commit` | `y/N` プロンプト |
| `WRITE_DANGEROUS` | `delete_file`, `shell_run`, `github_push_files`, `git_checkout`, `git_pull`, `git_push`, `trigger_workflow` | `yes`（フルワード）の入力が必要 |
| `ADMIN` | （カスタム; デフォルトでは未設定） | `yes` の入力が必要 |

`tool_safety_tiers` に記載のないツールは、デフォルトで `WRITE_DANGEROUS` として扱われる（フェイルセーフ）。

`tool_safety_tiers` のエントリは、実際に登録されたツール名でなければならない（サーバーキーではない）。起動時に双方向の検証が実行される。

- **ティアの欠落:** `tool_safety_tiers` に記載されていない登録済みツールがある場合、本番環境ではエラー（致命的な `RuntimeError`）、local/development では warning となる。
- **未知のキー:** `tool_safety_tiers` 内のキーが登録済みツール名でない場合、本番環境ではエラー（致命的な `RuntimeError`）、local/development では warning となる。

両方のチェックは、strict-key、safety-tier、allowed-tools の全ての検証を1回のパスに統合する `ProductionConfigValidator.validate()` を介して実行される。

---

## AI システムのための注記

1. **GitHub への書き込みアクセスを前提としないこと。** `allowed_repos` はデフォルトで空である（fail-closed）。
    GitHub への書き込みを試みる前に `allowed_repos` が設定されているか確認すること。

2. **シェルコマンドが実行されることを前提としないこと。** `command_allowlist` はデフォルトで空である。
    `shell_run` を試みる前に allowlist を確認すること。

3. **`allowed_repo_paths` が空 = git アクセス拒否。** git-mcp のツールを使用する前に設定すること。

4. **`db_allowlist` が空 = SQLite アクセス拒否。** `rag` と `session` のエントリを設定すること。

5. **`workflow_allowlist` は fail-closed である**（`repo_allowlist` と同様）。空リストは全ての
    ワークフロートリガーを拒否する。`cicd_mcp_server.toml` で許可するワークフローを明示的に列挙すること。

6. **mdq-mcp は本番運用可能である。** FTS5 のインデックス化と検索は機能として実装済み。本番の RAG ワークロードには `rag-pipeline-mcp` を使用すること。指針については下記の [§MDQ vs RAG Boundary](#mdq-vs-rag-boundary) を参照。

7. **破壊的操作の前に `dry_run=True` でプレビューすること。** エージェント内の承認フローは、
    ユーザープロンプトを表示する前に、登録済みツールに対して `dry_run=True` を自動的に注入する。

---

## MDQ 対 RAG の境界

> **正典の場所。** 本セクションは、以前 `04_mcp_07_mdq_rag_boundary.md`（コミット f24efc1 で削除）にあった内容を統合したものである。

### 目的

MDQ（Markdown Context Compression Engine）と RAG（Retrieval Augmented Generation）の間の所有権の境界を明確に定義し、エンジニアが特定のタスクにどちらのシステムを使用すべきか判断できるようにする。

---

### MDQ を使用する場面

以下の場合に MDQ を使用する。

- コンテンツが **Markdown のみ**（`.md`, `.markdown` ファイル）である。
- クエリが **構造を意識した検索**に関するもの: outline、見出し、階層的コンテキスト。
- **Markdown 特有の解析**が必要（セクション抽出、見出しに沿ったチャンク境界）。
- ワークロードが**低〜中程度の量**（数千〜数万件のドキュメント）である。

MDQ は、セマンティック埋め込みの品質よりも構造理解が重要となる Markdown ドキュメントに最適化されている。

**ツール:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`
**データベース:** `mdq.sqlite`（`rag.sqlite` とは別）
**状態:** 本番運用可能

---

### RAG を使用する場面

以下の場合に RAG を使用する。

- コンテンツが **マルチフォーマット**: PDF、HTML、テキスト、コード、Markdown など。
- 埋め込みによる**セマンティック検索**（類似度ベースの検索）が必要。
- 見出しに沿った分割を超える**チャンク化戦略**（再帰的、トークンベースなど）が必要。
- ワークロードが**大量**である、または**精緻化**（リランク、RRF によるハイブリッド検索）が必要。
- メタデータ抽出とバリデーションを伴う**ドキュメント取り込みパイプライン**が必要。

RAG はエージェント層の主要なドキュメント検索システムである。全コンテンツタイプに対する汎用的な検索をサポートする。

**ツール:** `ingest`, `search`, `get_document`, `delete_document`, `list_documents`（rag-pipeline-mcp 経由）
**データベース:** `rag.sqlite`
**状態:** 本番運用可能

---

### データ所有権

| システム | データベース | 所有者 | 管理者 |
|---|---|---|---|
| MDQ | `mdq.sqlite` | MCP 層（`mcp/mdq/`） | mdq-mcp サーバー（ポート 8013） |
| RAG | `rag.sqlite` | MCP 層（`scripts/mcp_servers/rag_pipeline/`） | rag-pipeline-mcp サーバー |

いずれのシステムも他方のデータベースに直接アクセスすることはない。それぞれが独自のスキーマ、インデックス、検索ロジックを保持する。

---

### エージェントのアクセスパターン

エージェント層は、両システムに **MCP ツール呼び出し**のみを通じてアクセスする。

1. **主経路（推奨）:** エージェントは MCP ルーティング（`ToolRouteResolver`）経由でツールを呼び出す。全てのツール呼び出しは MCP サーバーの抽象化層を通過する。
2. **管理者バイパス:** エージェント REPL の `/db` コマンドは、保守作業のために `rag.sqlite` に直接アクセスできる。これは管理者専用であり、通常の運用には含まれない。
3. **直接 DB アクセス（非推奨）:** アプリケーションコードは `mdq.sqlite` や `rag.sqlite` に対して `sqlite3` を直接 import してはならない。常に MCP ツールを使用すること。

---

### ルーティング方針

#### 1. ルーティングのヒューリスティック（分類器）

エージェントは軽量な分類器（`agent/mdq_rag_classifier.py`）を使用して、
ユーザーのクエリに基づき MDQ と RAG のどちらのツールを選ぶかを誘導する。

Markdown の構造に関する用語（例: "heading", "outline", "hierarchy",
"section", ".md", "table of contents"）を含むクエリは MDQ として分類され、それ以外はデフォルトで RAG となる。

分類器は各 LLM ターンの前に、1行のシステムプロンプトヒント（約20〜40トークン）を注入する。
LLM がそれに従わない場合もあり得るため、決定的なルーティングが必要な場合はオーバーライドモードを使用すること。

#### 2. 可用性フォールバック

| 条件 | 挙動 |
|---|---|
| MDQ が選択され、mdq-mcp が利用不可 | WARNING をログ出力; RAG ヒントにフォールバック |
| RAG が選択され、rag-pipeline-mcp が利用不可 | エラーを返す; フォールバックなし |
| オーバーライドモードで、強制指定したサーバーが利用不可 | エラーを返す |

RAG は常に本番環境で優先されるフォールバックである。

---

### 移行基準: MDQ から RAG へ

以下の場合に MDQ から RAG への移行を検討する。

- コンテンツ量が約10万ドキュメントを超える。
- Markdown 以外のコンテンツタイプを Markdown と併せて取り込む必要がある。
- セマンティック類似度検索の品質がボトルネックになる。
- ドキュメント間の重複排除、または重複排除を考慮した検索が必要になる。

自動的な移行パスは存在しない。移行には RAG パイプラインを介した再取り込みが必要である。

---

### 現在の状態

- **MDQ:** 本番運用可能。FTS5 検索とインデックス化を実装済み。
- **RAG:** 本番運用可能。完全な取り込みパイプライン、埋め込みサポート、ハイブリッド検索（RRF）が利用可能。

汎用的なドキュメント検索を伴う本番ワークロードには `rag-pipeline-mcp` を優先すること。
`mdq-mcp` は、埋め込み品質が重要でない Markdown 特有の構造的クエリにのみ使用すること。

---

### 境界の強制

自動化された pytest チェック（`tests/test_mdq_rag_boundary.py`）が、CI 実行ごとに MDQ/RAG の
境界を検証する。エージェント層における、禁止されたクロス DB 参照および許可されない直接 SQLite アクセスを
ソースファイル内でスキャンする。

#### 許可されたアクセスパス

| 層 | DB | 機構 | コンテキスト |
|---|---|---|---|
| `mcp/mdq/` | `mdq.sqlite` | 自身のサービス | 通常運用 |
| `scripts/mcp_servers/rag_pipeline/` | `rag.sqlite` | 自身のサービス | 通常運用 |
| エージェント層 | `session.sqlite` | `SQLiteHelper("session")` | 通常運用 |
| エージェント層 | `workflow.sqlite` | `SQLiteHelper("workflow")` | 通常運用 |
| エージェント層 | `rag.sqlite` | `RagMaintenanceService` 経由の `SQLiteHelper("rag")` | 管理者専用の `/db` コマンド |

#### 禁止されたアクセスパス

| 層 | DB | 理由 |
|---|---|---|
| `mcp/mdq/` | `rag.sqlite` | クロス DB 依存 |
| `scripts/mcp_servers/rag_pipeline/` | `mdq.sqlite` | クロス DB 依存 |
| エージェント層（通常時） | `mdq.sqlite` または `rag.sqlite` | 直接 DB アクセスではなく MCP ツールを使用すること |

#### 誤検知への対応

新しい管理者向け保守ファイルが `rag.sqlite` への直接アクセスを必要とする場合は、そのファイル名を
`tests/test_mdq_rag_boundary.py` の `ALLOWED` セットに追加し、その例外を上記の許可パス表に
記載すること。`ALLOWED` への変更には PR での設計レビューコメントが必要である。

---

### 既知の課題

- MDQ-02: ハイブリッド検索の埋め込み統合（`mode=hybrid`）は未実装 — BM25 とベクトルモードのみ利用可能。

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
   ```
   INFO Security: security_lockdown_enabled=True — deny-all warnings suppressed
   ```

### ランタイムでの deny-all 状態の確認

起動時、`audit_security_defaults()` は各 deny-all 状態をログに記録する。
```
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
| `mcp_watchdog_interval` | `0`（local） / `30.0`（prod） | `0` = 自動再起動なし | 本番環境では `30.0` を使用する |
