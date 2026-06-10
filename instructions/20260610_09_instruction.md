# MCP サーバ群 fail-fast 化・型強化・責務分離 改修計画書

## 全体方針

- 本改修では **後方互換性を維持しない**。旧 API、旧挙動、fail-soft なフォールバック、曖昧な入力許容、warning のみで継続する設計は削除する。
- すべてのレイヤで **fail-fast** を徹底する。設定ロード失敗、権限チェック失敗、外部 API 失敗、型変換失敗は即座に検知し、明示的な例外として扱う。
- 変換・型付けは厳密に行う。`Any`、曖昧な `dict`、エラーを文字列 `[ERROR]...` として返す設計を廃止し、専用例外クラスへ置き換える。
- `except Exception` は原則使用しない。想定される例外型のみを個別に捕捉し、それ以外はそのまま送出する。
- `service.py` から `HTTPException` を除去し、domain 例外 (GitHub MCP と同様のパターン) に統一する。`server.py` の exception handler が HTTP 変換を担う。
- `_get_cfg()` module-level cache + `except Exception` + `{}` fallback を全モジュールから廃止し、設定ロードを起動時一度に正規化して型付き config object を注入する。

---

## 実装ルール

- `_get_cfg()` のような module-level config cache と `{}` fallback を使用しない。設定は `GitHubConfig.load()` パターンに倣い、起動時に一度ロードして型付きオブジェクトとして注入する。
- `HTTPException` は transport 層 (`server.py`) に限定し、service 層では domain 例外 (`XXXAuthorizationError`, `XXXValidationError`, `XXXNotFoundError`, `XXXUpstreamError` など) を使用する。
- エラーを `[ERROR] ...` 形式の文字列で返す設計を廃止し、呼び出し元に伝わる例外として扱う。
- `except Exception as e` の代わりに想定例外型を個別捕捉する。ConfigLoader の失敗は `FileNotFoundError | OSError`、JSON パース失敗は `orjson.JSONDecodeError`、HTTP 失敗は `httpx.HTTPStatusError | httpx.RequestError` を指定する。
- service 層の policy / allowlist チェックは domain 例外を投げ、server.py の exception handler が HTTP response に変換する。
- git/service.py の `return f"[ERROR] ..."` パターンは `GitServiceError(RuntimeError)` を投げる形に変更し、呼び出し元 (server.py) で捕捉して適切な HTTP response に変換する。

---

## ファイルごとの修正内容

### 共通パターン — 全 `models.py` (8 ファイル)

対象: `cicd/models.py`, `file/delete_models.py`, `file/read_models.py`, `file/write_models.py`, `git/models.py`, `rag_pipeline/models.py`, `shell/models.py`, `sqlite/models.py`

#### High
- `_get_cfg()` の `except Exception` + `{}` fallback を廃止する。代わりに `FileNotFoundError | OSError` を個別に捕捉し、失敗時は即例外を送出する。または `_get_cfg()` ごと廃止して型付き config dataclass (`CicdConfig`, `ShellConfig`, `GitConfig`, `SqliteConfig` 等) の `load()` classmethod に置き換える。
- module-level で `_get_cfg()` を呼ぶ定数定義 (`DEFAULT_MAX_RESULTS = _get_cfg().get(...)` など) を廃止し、ハードコード定数または config dataclass のデフォルト値とする。

#### Medium
- 型付き config dataclass を各 models.py に追加し、GitHub MCP と同パターン (`from_dict(d)` / `load()`) で構築できるようにする。

---

### `cicd/service.py` (488 行)

#### High
- `from fastapi import HTTPException` を除去する。`HTTPException` の発生箇所 (line 115, 124, 133, 137, 139, 141, 366, 374, 387, 398) をすべて domain 例外に置き換える:
  - `HTTPException(403)` → `CicdAuthorizationError(RuntimeError)`
  - `HTTPException(404)` → `CicdNotFoundError(RuntimeError)`
  - `HTTPException(422)` → `CicdValidationError(ValueError)`
  - `HTTPException(400)` → `CicdValidationError(ValueError)`
- `_handle_response()` 内の `except Exception` (line 122, 129) を廃止し `orjson.JSONDecodeError | UnicodeDecodeError` を個別捕捉する。
- `except Exception as e` (line 322) を廃止し `httpx.HTTPStatusError | httpx.RequestError | orjson.JSONDecodeError` を個別捕捉する。
- `_get_cfg()` 参照を廃止し、constructor injection に切り替える (`cfg: CicdConfig` を `__init__` で受け取る)。
- `CicdService.__init__` が `cfg: dict[str, Any]` を受け取る箇所 (line 346) を型付き `CicdConfig` に変更する。

#### Medium
- `_format_job_header(job: dict[str, Any])` の `dict[str, Any]` を専用 TypedDict に変更する。

#### Low
- logging メッセージの粒度と文面を統一する。

---

### `shell/service.py` (422 行)

#### High
- `from fastapi import HTTPException` を除去する。`HTTPException` の発生箇所 (line 154, 159, 163, 204, 211) をすべて domain 例外に置き換える:
  - `HTTPException(403)` → `ShellAuthorizationError(RuntimeError)`
  - `HTTPException(400)` → `ShellValidationError(ValueError)`
- `ShellPolicy` の `_get_cfg()` 依存を廃止する。`ShellService.__init__` で `ShellConfig` を注入する。

#### Medium
- `ShellConfig` dataclass を `shell/models.py` に定義し、許可コマンド・許可パス・タイムアウト等を型付きフィールドで管理する。
- `shell/models.py` の `_get_cfg()` を廃止し `ShellConfig.load()` に統一する。

#### Low
- 環境変数フィルタ (`_SAFE_ENV_KEYS`) の管理を config dataclass に統合する。

---

### `file/read_service.py` (539 行)

#### High
- `from fastapi import HTTPException` を除去する。`HTTPException` の発生箇所 (line 206, 227, 232, 246, 249, 356, 377, 386) をすべて domain 例外に置き換える:
  - `HTTPException(403)` → `FileAuthorizationError(RuntimeError)`
  - `HTTPException(400)` → `FileValidationError(ValueError)`
- `except HTTPException as e` (line 276) を廃止し、`FileAuthorizationError | FileValidationError` を個別捕捉する。
- `_get_cfg()` 参照 (line 524) を廃止し、constructor injection に変更する。

#### Medium
- `file/read_models.py` の `_get_cfg()` を廃止し `FileReadConfig.load()` に統一する。

---

### `file/write_service.py` (287 行)

#### High
- `HTTPException` の発生箇所を domain 例外 (`FileAuthorizationError`, `FileValidationError`) に置き換える。
- `_get_cfg()` 参照を廃止し `FileWriteConfig` injection に変更する。

#### Medium
- `file/write_models.py` の `_get_cfg()` を廃止し `FileWriteConfig.load()` に統一する。

---

### `file/delete_service.py` (227 行)

#### Medium
- `file/delete_models.py` の `_get_cfg()` を廃止し `FileDeleteConfig.load()` に統一する。

#### Low
- `HTTPException` の使用有無を確認し、あれば domain 例外に置き換える。

---

### `git/service.py` (345 行)

#### High
- `return f"[ERROR] git_status: {e}"` 形式 (line 114, 141, 160, 178, 192, 218, 235, 240, 268) を廃止する。すべての箇所で `raise GitServiceError(f"git_{op} failed: {e}") from e` を発生させる。
- `git/server.py` に `@app.exception_handler(GitServiceError)` を追加し、HTTP 502 に変換する。
- `git/models.py` の `_get_cfg()` の `except Exception` を `FileNotFoundError | OSError` に限定する。または `_get_cfg()` ごと廃止して `GitConfig.load()` に統一する。

#### Medium
- `GitServiceError(RuntimeError)` を `git/models.py` に定義する。
- `_GIT_ERRORS = (git.exc.GitError, OSError, ValueError)` を使っているが、これを `GitServiceError` に wrap してから再送出するパターンに統一する。

#### Low
- `git/models.py` の config 関数名 `load_git_config()` を他ファイルの `_get_cfg()` と一貫させる、または `GitConfig.load()` に統一する。

---

### `web_search/server.py` (391 行)

#### High
- `_get_cfg()` の `except Exception` + `{}` fallback (line 40-47) を廃止する。`FileNotFoundError | OSError` のみ捕捉し、失敗時は起動時例外として扱う。
- module-level で `_get_cfg()` を呼ぶ定数 (line 55-56) を廃止する。
- `_try_provider()` 内の `except Exception as e` (line 258) を廃止し `httpx.HTTPStatusError | httpx.RequestError | asyncio.TimeoutError | orjson.JSONDecodeError` を個別捕捉する。
- プロバイダ全失敗時の `raise HTTPException(status_code=502, ...)` は domain 例外 (`SearchUpstreamError(RuntimeError)`) を使い exception handler で変換する。

#### Medium
- `_get_cfg()` を `WebSearchConfig` dataclass に置き換える。
- `DEFAULT_MAX_RESULTS` / `MAX_RESULTS_LIMIT` を `WebSearchConfig` のフィールドとして管理する。

---

### `sqlite/service.py` (151 行)

#### High
- `sqlite/models.py` の `_get_cfg()` を廃止し `SqliteConfig.load()` に統一する。
- service 内の `cfg = _get_cfg()` (line 134) を constructor injection に変更する。

#### Medium
- 型定義が `dict[str, Any]` になっている箇所を `SqliteConfig` フィールドで管理する。

---

### `rag_pipeline/service.py` (205 行)

#### High
- module-level config override (`agent_rag._cfg = cfg` 等) を `rag_pipeline/models.py` の `_get_cfg()` 廃止と合わせて整理する。`RagPipeline.__init__` が既に `GitHubConfig.load()` パターンで設定を受け取る (実装済み) ため、同様の injection に統一する。
- `rag_pipeline/models.py` の `_get_cfg()` の `except Exception` + `{}` fallback を廃止する。

#### Medium
- `RagPipelineMCPService.start()` 内の設定ロードを `RagPipelineConfig.load()` に統一し、module-level state mutation を廃止する。

---

### `mdq/indexer.py`, `mdq/service.py`

#### Medium
- `mdq/indexer.py`: 存在しないパスを `logger.warning` して `continue` する処理を `FileNotFoundError` を送出する形に変更する。呼び出し元で存在確認を事前に行う。
- `mdq/service.py`: `self._pipeline: Any | None` の `Any` を具体的な型に変更する。循環 import 回避なら `TYPE_CHECKING` ガードを使用する。

#### Low
- `mdq/parser.py`: 既に `FileNotFoundError` を明示的に発生させているため変更不要。

---

### `mcp/server.py` (基盤層)

#### Medium
- line 180 の `except Exception as e`: stdio transport 層の最後の砦として意図的な設計だが、`SystemExit | KeyboardInterrupt` は再送出するよう明示する。`BaseException` サブクラスの分類を行い、意図しない catch を防ぐ。

---

## 作業ステップ

### Step 1: 共通 domain 例外クラスとConfig dataclass の定義
各 MCP サーバの `models.py` に型付き config dataclass と domain 例外クラスを追加する。
- `CicdConfig`, `CicdAuthorizationError`, `CicdNotFoundError`, `CicdValidationError`, `CicdUpstreamError`
- `ShellConfig`, `ShellAuthorizationError`, `ShellValidationError`
- `FileReadConfig` / `FileWriteConfig` / `FileDeleteConfig` / `FileAuthorizationError` / `FileValidationError` (file/ 共通)
- `GitConfig`, `GitServiceError`
- `WebSearchConfig`, `SearchUpstreamError`
- `SqliteConfig`
- `RagPipelineConfig`

**完了条件:** 各 `models.py` に dataclass と例外クラスが定義され `uv run mypy scripts/mcp/` が通る。

### Step 2: `_get_cfg()` の廃止と config injection 化
各 `models.py` の `_get_cfg()` を廃止し、service コンストラクタで `XxxConfig` を受け取る形に変更する。Lazy singleton (`_LazyXxxService`) を `XxxConfig.load()` で初期化するよう更新する。

**完了条件:** `grep -r "_get_cfg" scripts/mcp/` の結果が 0 件。

### Step 3: `service.py` からの `HTTPException` 除去
各 service.py の `HTTPException` を domain 例外に置き換え、対応する `server.py` に `@app.exception_handler` を追加する。

対象: `cicd/service.py`, `shell/service.py`, `file/read_service.py`, `file/write_service.py`, `web_search/server.py`

**完了条件:** `grep -r "from fastapi import HTTPException" scripts/mcp/` が各 `server.py` のみを返す。

### Step 4: `git/service.py` の `[ERROR]` 文字列返却廃止
`return f"[ERROR] ..."` をすべて `raise GitServiceError(...)` に変更し、`git/server.py` に exception handler を追加する。

**完了条件:** `grep "\[ERROR\]" scripts/mcp/git/service.py` の結果が 0 件。

### Step 5: `except Exception` の個別例外型への置き換え
残存する `except Exception` を想定する具体的な例外型に個別置換する。

**完了条件:** `grep -r "except Exception" scripts/mcp/` の結果が 0 件 (または `mcp/server.py` の stdio 最終捕捉のみ)。

### Step 6: 異常系テスト追加と全スイート確認
各 Step の変更に対する異常系テスト (config ロード失敗、権限チェック失敗、API 失敗) を追加する。

**完了条件:** `uv run pytest -v` 全テスト pass。

---

## 完了条件

- `grep -r "except Exception" scripts/mcp/` の結果が 0 件 (または `mcp/server.py` stdio 最終捕捉層のみ)。
- `grep -r "from fastapi import HTTPException" scripts/mcp/` が各 `server.py` のみを返す (service 層での import なし)。
- `grep -r "_get_cfg" scripts/mcp/` の結果が 0 件。
- `grep "\[ERROR\]" scripts/mcp/git/service.py` の結果が 0 件。
- `uv run ruff check scripts/mcp/` 0 errors。
- `uv run mypy scripts/mcp/` no new errors。
- `uv run pytest -v` 全テスト pass (既存テストの regression なし)。
- 各 MCP サーバの config ロード失敗が `{}` fallback ではなく即例外として起動時に検知される。
- service 層が `HTTPException` を投げず、domain 例外を返す構造になっている。
- git 操作の失敗が `[ERROR]` 文字列ではなく `GitServiceError` 例外として伝播する。
