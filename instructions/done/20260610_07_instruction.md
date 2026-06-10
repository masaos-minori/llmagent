# GitHub MCP 改修計画書

## 全体方針

- 本改修では **後方互換性を維持しない**。旧挙動の温存、暗黙の fail-open / fail-soft、設定ロード失敗時の救済、緩い入力変換、warning のみで継続する実装は削除する。
- すべてのレイヤで **fail-fast** を徹底する。設定不備、許可判定失敗、GitHub API 失敗、監査失敗、モデル不整合、エンドポイント不整合は明示的な例外または結果型として扱う。
- 変換・型付けは厳密に行う。`Any`、生 `dict`、暗黙の設定辞書、 loosely typed tool args、曖昧な文字列表現を減らし、専用モデル/結果型/Protocol を導入する。
- `except Exception` は原則使用しない。想定する失敗型のみを個別に捕捉し、それ以外はそのまま送出する。
- `service.py` / `models.py` / `server.py` / `tools.py` の責務境界を明確化する。
  - `models.py`: API 契約・設定モデル・検証
  - `service.py`: GitHub 業務ロジック・許可判定・フォーマット補助
  - `server.py`: FastAPI ルーティング・HTTP 変換・依存注入
  - `tools.py`: MCP ツール定義の静的スキーマ
- 設定・認可・監査・GitHub API 呼び出し・フォーマット・HTTP 変換を分離し、サーバ層が service を直接広く知りすぎない構造へ移行する。

## 実装ルール

- `_get_cfg()` のような module-level config cache と `{}` fallback を使用しない。設定ロードは起動時に一度正規化し、以後は型付き設定オブジェクトを注入する。
- `HTTPException` は transport 層（FastAPI）に限定して使い、service 層では domain/service 例外へ置き換える。
- `GITHUB_TOKEN` や許可リポジトリ・許可パス・危険ブランチなどの設定は環境変数/辞書を直接参照せず、型付き設定モデルを通して参照する。
- GitHub API 応答から内部モデルへの変換は mapper を通して行い、service 内で ad-hoc な dict 生成をしない。
- formatter（Markdown 整形や dry-run preview）は service 本体から分離し、表示責務と API 呼び出し責務を混在させない。
- `tools.py` のスキーマは手書き巨大配列のまま持たず、モデル定義または宣言的 spec から生成する。
- FastAPI ルートは request model → service call → response model の 3 段階に統一し、route 関数内で業務ロジックやフォーマットを持たない。
- 監査は必須操作として扱い、監査失敗を warning のみにしない。

## ファイルごとの修正内容

### 1. `service.py`

#### High
- `GitHubService` が持っている責務（設定参照、許可判定、GitHub API 呼び出し、監査、dry-run preview、Markdown 整形、dispatch table 生成）を分解する。
- `_assert_allowed_repo()`, `_assert_allowed_path()`, `_assert_allowed_branch()` の設定取得を `_get_cfg()` 依存から外し、型付き設定オブジェクトに置き換える。
- `_get_cfg()` 前提の fail-open / fail-closed 混在を整理し、repo/path/branch 制約はすべて fail-fast に統一する。
- `HTTPException` を service 層から除去し、service 専用例外（authorization denied / validation failed / upstream failure / not found / conflict など）へ置き換える。
- `_run_github()` と `_handle_github_error()` のエラー変換を再設計し、`GithubException` の status/code ごとに分類する。未知例外を generic な HTTP error に丸めない。
- `create_or_update_file`, `push_files`, `delete_repo_file`, `merge_pull_request` など書き込み系操作の dry-run / audit / path/branch policy を一貫化する。
- `_write_github_audit_log()` を service 本体から分離し、監査失敗を warning で無視しない構造にする。
- `get_dispatch_table()` による動的 dispatch をやめ、明示的 command/service mapping へ変更する。

#### Medium
- `_issue_to_info()`, `_pr_to_info()` などの変換を mapper 層へ切り出す。
- `fmt_*` 系メソッド群を formatter モジュールへ分離する。
- `_dry_run_preview()` を formatter/policy 層へ移し、service が preview 文面を生成しないようにする。
- `Github` クライアント生成、per_page clamp、repo 取得、branch 解決などを helper/component に分割する。

#### Low
- 命名の一貫性（`fmt_delete_file` と request/response 名など）を整理する。
- ログメッセージの粒度と文面を統一する。

---

### 2. `tools.py`

#### High
- `_MCP_TOOLS` の巨大な手書きリストを廃止し、モデルまたは宣言的 spec から生成する。
- request model と `inputSchema` の二重定義を放置しない。`models.py` の request モデルから schema を生成する仕組みに統一する。
- ツール定義と server route / dispatch / service メソッド名の整合性を自動検証できるようにする。

#### Medium
- 説明文、required、型、optional 引数の書式を統一する。
- read-only / write / destructive / pull request / issue / code search などのカテゴリごとに定義を分割する。
- tool 定義に audit/policy/approval metadata を持たせる余地を作る。

#### Low
- 説明文の重複を削減し、簡潔にする。

---

### 3. `models.py`

#### High
- `_get_cfg()` の module-level cache と `except Exception` + `{}` fallback を廃止する。設定ロードは起動時に一度行い、これらのモデルへ必要な制約値を注入する。
- `Any` を使う設定ロード/変換契約を厳密化する。
- request/response モデル全体の validation を再設計し、owner/repo/path/branch/query/per_page などのフィールド制約を強化する。
- Pydantic モデルに埋め込まれていない cross-field rule（例: branch 必須条件、sha 必須条件、複数ファイル更新時の制約）を service 任せにせず、必要に応じて model validator へ追加する。
- response モデルを単なる transport DTO ではなく、内部 domain model と transport model に分離する。

#### Medium
- 共有ベースモデル（owner/repo 共通、pagination 共通、branch 共通）を導入し、定義重複を削減する。
- `DEFAULT_PER_PAGE` や `max_per_page` などの設定依存値をモデル定義から分離する。
- request model 群と response model 群をカテゴリ別に分ける。

#### Low
- docstring と Field description の表現を統一する。

---

### 4. `server.py`

#### High
- 24 個近い route 関数が同型の処理（request 受け取り → service 呼び出し → formatter → response）を繰り返しているため、route 登録を declarative に再構成する。
- route 関数内で logger/warning による補助的失敗処理を持たない。service 失敗は統一例外ハンドラで HTTP response へ変換する。
- `_dispatch_github_tool()` と `GithubMCPServer.dispatch()` の責務を整理し、FastAPI transport と MCP dispatch を共通 command registry に寄せる。
- `list_tools()` が `tools.py` と静的に同期している前提をやめ、tool registry から動的に取得する。
- `call_tool()` が tool 名文字列を直接 dispatch する構造を、request model validation + command lookup + response model へ統一する。

#### Medium
- `health()` を起動確認だけでなく設定・GitHub client・認可ポリシー初期化の状態を返せるようにする。
- FastAPI dependency injection を導入し、service singleton 直接参照をやめる。
- route と MCP server class の重複責務を整理し、HTTP 版 / MCP dispatch 版の共通ロジックを抽出する。

#### Low
- endpoint 名と関数名の一貫性を整理する。
- logger の文面と粒度を統一する。

## 作業ステップ

1. **型と設定契約の固定**
   - `models.py` を見直し、request/response/domain model を整理する。
   - 設定ロードをサービス外へ移し、型付き config object を定義する。

2. **認可・監査・GitHub API エラーの分離**
   - `service.py` から `HTTPException` を除去し、domain/service 例外へ置換する。
   - 許可判定、監査、GitHub API 呼び出し、formatter を分離する。

3. **formatter と mapper の抽出**
   - `fmt_*` 系、`_issue_to_info()`, `_pr_to_info()`, dry-run preview を独立コンポーネントに移す。

4. **tool 定義の単一化**
   - `tools.py` を request model 由来の schema 生成へ切り替える。
   - tool 定義と server/service の整合チェックを自動化する。

5. **server 層の再構成**
   - `server.py` の route 群を declarative registration に切り替える。
   - 統一例外ハンドラ、依存注入、共通 dispatch を導入する。

6. **異常系テスト追加**
   - 設定ロード失敗
   - 無許可 repo/path/branch
   - GitHub API 404/403/409/422
   - dry-run と実行の差分
   - auditing failure
   - schema と request model の不一致
   - route と tool registry の不一致

## 完了条件

- `except Exception` に依存する fail-soft な経路が `models.py` / `service.py` / `server.py` から除去されている。
- `_get_cfg()` による辞書設定参照がサービス実装・モデル定義から排除され、型付き設定注入へ置き換わっている。
- service 層が `HTTPException` を投げず、domain/service 例外を返す構造になっている。
- `tools.py` の schema と `models.py` の request model が単一ソースから生成・検証されている。
- `server.py` の route 実装が thin transport layer になり、業務ロジック・フォーマット・監査・認可を持っていない。
- formatter / mapper / audit / policy / GitHub client adapter の責務境界が明確になっている。
- 書き込み系 GitHub 操作が dry-run / approval / audit / policy を一貫した経路で処理する。
- fail-fast により、設定不備・認可違反・GitHub API 失敗・モデル不整合が warning や暗黙 fallback に丸められず、明示的失敗として扱われる。
