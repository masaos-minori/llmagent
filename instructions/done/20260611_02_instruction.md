# 改修計画書

## 全体方針

### 事実
- 対象ファイルは `ingest_workflow.py`、`mcp_install.py`、`mcp_status.py`、`session_restore.py`、`session_title.py`、`undo_service.py`、`config_reload.py`、`context_view.py`、`conversation_service.py`、`db_maintenance_service.py`、`export_formatter.py` の 11 ファイルである
- fail-fast 方針に反する実装が存在する
  - `ingest_workflow.py:94,126,141` に `except Exception`
  - `mcp_status.py:100` に `except Exception`
  - `session_title.py:56` に `except Exception`
- 型の厳密性が不足している実装が存在する
  - `config_reload.py` は `dict[str, Any]` を広範囲に使用する (`config_reload.py:41`, `config_reload.py:62`, `config_reload.py:102`, `config_reload.py:167`, `config_reload.py:193`, `config_reload.py:228`, `config_reload.py:249`, `config_reload.py:282`)
  - `context_view.py` は `dict` 戻り値と `LLMMessage` の `.get()` ベース参照を使用する (`context_view.py:20`, `context_view.py:24-26`, `context_view.py:54-94`)
  - `db_maintenance_service.py` は `dict` / `object` 戻り値を使用する (`db_maintenance_service.py:23`, `db_maintenance_service.py:38`, `db_maintenance_service.py:49`, `db_maintenance_service.py:54`, `db_maintenance_service.py:64`, `db_maintenance_service.py:75`)
- 無条件文字列化と直接出力が存在する
  - `context_view.py:59,62` で `str(m.get(...))` を使用する
  - `export_formatter.py:29` で `str(msg.get("content") or "")` を使用する
  - `mcp_install.py` は `print` と `input` を直接使用する (`mcp_install.py:52-77`, `mcp_install.py:124-163`)
  - `export_formatter.py:50,54,59` は `print` を直接使用する
- 後方互換的な継続動作が存在する
  - `session_title.py` は失敗時に入力文字列先頭 50 文字へフォールバックする (`session_title.py:34-58`)
  - `mcp_status.py` は未知 tier を `READ_ONLY` 扱いで継続する (`mcp_status.py:117-122`)
  - `context_view.py` は token 数を `total_chars // 4` で代替する (`context_view.py:69-75`)

### 推測
- これらの service は command 層や context 層への橋渡し責務を持つため、DTO 化と例外体系の整備を先行しない限り、個別修正が呼び出し側に波及する可能性が高い
- `config_reload.py`、`ingest_workflow.py`、`context_view.py` が型付けと fail-fast の修正起点になる可能性が高い

### 改修方針
- 対象は High / Medium のみとする。Low は今回の計画対象外とする
- 後方互換性は維持しない。フォールバック、暗黙補正、失敗時継続を削除する
- `assert` を業務ロジックで使用しない。前提条件違反は明示例外を送出する
- `except Exception` を使用しない。捕捉対象を具体例外に限定する
- `dict[str, Any]` を外部境界以外で使用しない。境界通過直後に型変換する
- `str(args.get(...))`、`str(msg.get(...))` のような無条件文字列化を禁止する。入力型を検証し、期待型以外は例外とする
- 変換・型付けは厳密に行う
- `None` と空文字と未設定を同一視しない
- 監査ログ、承認判定、実行結果に相当する service 戻り値は専用 DTO を定義する
- LLM 由来 JSON は decode 後に schema 検証する。schema 不一致は即時失敗とする
- 出力は直接 `print` せず、UI/CLI 出力用インターフェースへ集約する
- 不明な tool 名、不明な tier、不明な metadata は fail-open ではなく fail-fast とする

## 実装ルール

### 必須ルール
- `assert` を業務ロジックで使用しない
- `except Exception` を使用しない
- `dict[str, Any]` を service 内部の主要データモデルとして使用しない
- `.get()` ベースの曖昧参照を DTO access に置換する
- `str(...)` による無条件文字列化を禁止する
- `tuple[bool, str]`、`dict`、`object` を戻り値として使わず DTO または具体例外へ統一する
- 直接 `print` / `input` を使用しない
- デフォルト値補完で異常を隠蔽しない

### 新設すべき共通要素
- `agent/services/models.py`
  - `IngestOutcome`
  - `InstallAnswer`
  - `InstallRenderPlan`
  - `McpProbeResult`
  - `SessionRestoreResult`
  - `SessionTitleResult`
  - `UndoResult`
  - `ConfigReloadRequest`
  - `ConfigReloadOutcome`
  - `ContextStateView`
  - `ConversationActionResult`
  - `DbStats`
  - `DbHealth`
  - `ExportRequest`
  - `ExportResult`
- `agent/services/enums.py`
  - `IngestStage`
  - `McpAvailability`
  - `McpTier`
  - `ConversationActionType`
  - `ExportFormat`
- `agent/services/exceptions.py`
  - `IngestStageError`
  - `McpProbeError`
  - `SessionTitleGenerationError`
  - `ConfigReloadValidationError`
  - `ContextStateBuildError`
  - `ExportWriteError`
  - `ConversationStateError`
  - `DbMaintenanceError`
- `agent/services/io_ports.py`
  - `InstallIOPort`
  - `ExportOutputPort`
  - `StatusRenderPort`

## ファイルごとの修正内容

### `config_reload.py`

#### 事実
- `apply_config_dict()` と複数 private helper が `dict[str, Any]` を直接受ける (`config_reload.py:41`, `config_reload.py:62`, `config_reload.py:102`, `config_reload.py:167`, `config_reload.py:193`, `config_reload.py:228`, `config_reload.py:249`, `config_reload.py:282`)
- `masked_fields` などを schema 検証なしで適用している (`config_reload.py:48-52`)
- 戻り値は `ConfigReloadResult` であるが、入力は raw dict のままである

#### 修正内容
- High
  - `new_cfg: dict[str, Any]` を廃止し、`ConfigReloadRequest` DTO へ変換してから適用する
  - reload 対象フィールドごとに schema 検証を導入し、型不一致は `ConfigReloadValidationError` で即時失敗させる
  - `.get()` と存在確認前提の暗黙補正を削除し、未設定と空値を区別する
- Medium
  - `ConfigReloadResult` を `ConfigReloadOutcome` DTO へ改名し、`applied` / `needs_restart` / `skipped` の意味と型を固定する
  - helper 群をカテゴリ別 validator / applier へ再編し、責務境界を明確化する
- Low
  - 対象外

### `ingest_workflow.py`

#### 事実
- `_crawl()`、`_split_and_ingest()` の各段で `except Exception` を使用している (`ingest_workflow.py:94,126,141`)
- `IngestResult.stage` は生文字列である (`ingest_workflow.py:23`)
- エラー詳細を `str(e)` で文字列化して result に詰めている (`ingest_workflow.py:97,129,144`)

#### 修正内容
- High
  - `except Exception` を廃止し、crawler / splitter / ingester / `OSError` / import failure を具体例外で分解する
  - `IngestResult.stage` を `IngestStage` Enum に置換する
  - `error: str | None` を `error_code` と `error_detail` を持つ DTO または具体例外へ変更する
  - file path 判定や local file 読み込み失敗を `Path` validation と stage 例外へ分離する
- Medium
  - `messages: list[str]` を進行ログ DTO に置換し、表示と内部状態を分離する
  - `snippets_only` 分岐における config 変更点を専用 request DTO に切り出す
- Low
  - 対象外

### `context_view.py`

#### 事実
- `budget_breakdown()` は `LLMMessage` の `.get()` と生 dict 集計に依存する (`context_view.py:20-37`)
- `collect_context_state()` は `dict` を返し、`str(m.get("content") or "")` で文字列化する (`context_view.py:54-94`)
- token 数の代替として `total_chars // 4` を使用する (`context_view.py:69-75`)
- `git_helper.get_repo_info()` の `None` 返却を前提にしている (`context_view.py:76-92`)

#### 修正内容
- High
  - 戻り値を `ContextStateView` DTO に変更する
  - `LLMMessage` 依存を用途別 message DTO に置換し、`.get()` と無条件文字列化を廃止する
  - `total_chars // 4` フォールバックを削除し、token 不明時は `None` と推定不可状態を DTO で表現する
  - `git_info` を `RepoInfo` DTO または具体例外で扱い、`unavailable` 文字列埋め込みを廃止する
- Medium
  - `budget_breakdown()` のカテゴリ集計を enum ベースへ置換する
  - memory status も DTO 化し、文字列整形は presentation 層に移す
- Low
  - 対象外

### `session_title.py`

#### 事実
- LLM 呼び出し失敗時に `except Exception` で握りつぶして入力先頭 50 文字へフォールバックする (`session_title.py:34-58`)
- `resp.json().get("choices", [])` と多段 `.get()` を使用する (`session_title.py:46-49`)

#### 修正内容
- High
  - `except Exception` を廃止し、HTTP error / JSON decode error / response schema mismatch を具体例外へ分解する
  - フォールバックタイトル生成を削除し、失敗は `SessionTitleGenerationError` として扱う
  - response body を DTO に変換し、schema 不一致時は即時失敗とする
- Medium
  - `generate()` の戻り値を `None` ではなく `SessionTitleResult` DTO に変更する
  - prompt / request parameter を専用 request DTO に切り出す
- Low
  - 対象外

### `mcp_status.py`

#### 事実
- `_get_http_status()` で `except Exception` を使用する (`mcp_status.py:97-101`)
- `McpServerStatus` は `transport`、`startup_mode`、`availability`、`health` を生文字列で持つ (`mcp_status.py:37-48`)
- `_tier_label_for_server()` は未知 tier を `READ_ONLY` 扱いする (`mcp_status.py:117-122`)

#### 修正内容
- High
  - `except Exception` を廃止し、`httpx.RequestError` と `httpx.HTTPStatusError` 等に分解する
  - `McpServerStatus` の文字列属性を enum / DTO に置換する
  - `_tier_label_for_server()` で未知 tier を許容せず、`UnknownTierError` で停止する
  - `cfg.url` 未設定や `cfg.cmd` 空を status 文字列で吸収せず設定異常として例外化する
- Medium
  - probe 結果と表示文言を分離し、`McpProbeResult` DTO と renderer を分ける
- Low
  - 対象外

### `export_formatter.py`

#### 事実
- `render_history_md()` は `LLMMessage` の `.get()` と `str(msg.get("content") or "")` を使用する (`export_formatter.py:19-37`)
- `write_export()` は `print` に直接出力する (`export_formatter.py:47-59`)
- `fmt` は生文字列である (`export_formatter.py:40-44`)

#### 修正内容
- High
  - `LLMMessage` を用途別 DTO に置換し、無条件文字列化を廃止する
  - `write_export()` の直接 `print` を廃止し、`ExportOutputPort` へ委譲する
  - `fmt` を `ExportFormat` Enum に置換する
  - `OSError` を `ExportWriteError` へ変換し、呼び出し側へ伝播する
- Medium
  - `render_export()` と `write_export()` の責務を分割し、render result と write result を DTO で返す
- Low
  - 対象外

### `mcp_install.py`

#### 事実
- `CliInstallQA` が `input()` と `print()` を直接使用する (`mcp_install.py:52-77`)
- `print_next_steps()` が複数の `print` 出力に依存する (`mcp_install.py:124-163`)
- `ask_role()` は未知入力を `generic` に丸める (`mcp_install.py:64-68`)

#### 修正内容
- High
  - `input()` / `print()` を service から除去し、`InstallIOPort` に抽象化する
  - `ask_role()` の未知入力丸めを削除し、role 値は enum 検証で reject する
  - wizard 入力を `InstallAnswer` DTO にまとめ、`server_name`、port、role、confd 指定を一括検証する
- Medium
  - `print_next_steps()` を renderer 化し、文字列出力計画 `InstallRenderPlan` を返す設計へ変更する
  - `ScaffoldResult` に created_files / snippet を raw 文字列のまま持たせず、表示用 DTO と内部 DTO を分離する
- Low
  - 対象外

### `session_restore.py`

#### 事実
- 戻り値が `tuple[bool, str]` である (`session_restore.py:19-29`)
- `messages` 未取得時はメッセージ文字列で not found を返す (`session_restore.py:24-25`)
- `ctx.conv.history` を直接再構築している (`session_restore.py:26-29`)

#### 修正内容
- High
  - 戻り値を `SessionRestoreResult` DTO に変更し、成功可否と message を分離する
  - session 不在や空メッセージを `SessionNotFoundError` 等の具体例外へ変更する
- Medium
  - history 再構築処理を `ConversationHistoryBuilder` 相当へ分離し、service の責務を session 切替に限定する
- Low
  - 対象外

### `undo_service.py`

#### 事実
- 戻り値が `tuple[bool, str]` である (`undo_service.py:19-46`)
- `ctx.conv.history[cut_idx - 1].get("_memory_injected")` のような dict 参照を行う (`undo_service.py:39`)

#### 修正内容
- High
  - 戻り値を `UndoResult` DTO に変更する
  - `_memory_injected` を生 dict フラグに依存せず、message metadata DTO へ移す
- Medium
  - history 操作を helper に分離し、削除対象算出ロジックを unit test 可能な純粋関数へ切り出す
- Low
  - 対象外

### `conversation_service.py`

#### 事実
- `clear_conversation()` と `switch_system_prompt()` は文字列を返す (`conversation_service.py:21-33`, `conversation_service.py:36-55`)
- `switch_system_prompt()` は `ctx.conv.history[0]` の dict を直接更新する (`conversation_service.py:48-53`)

#### 修正内容
- High
  - 戻り値を `ConversationActionResult` DTO に変更する
  - system prompt 名不正時は `ValueError` ではなく専用例外へ変更する
  - history 先頭メッセージの直接 dict 更新を DTO ベース更新へ置き換える
- Medium
  - clear / switch の action type を Enum 化し、表示文言生成を command 層へ移す
- Low
  - 対象外

### `db_maintenance_service.py`

#### 事実
- `stats()`、`health()`、`checkpoint()`、`purge()` は `dict` を返す (`db_maintenance_service.py:23-36`, `db_maintenance_service.py:49-57`, `db_maintenance_service.py:64-73`)
- `recover()` は `object` を返す (`db_maintenance_service.py:75-77`)
- `purge()` は `cfg_kwargs: dict[str, int]` を都度構築する (`db_maintenance_service.py:64-73`)

#### 修正内容
- High
  - `stats()`、`health()`、`checkpoint()`、`purge()`、`recover()` の戻り値を DTO に変更する
  - `recover()` の `object` 戻り値を廃止し、成功結果 DTO または具体例外へ統一する
  - `RetentionConfig` 生成前に request DTO を検証し、不正値を即時失敗させる
- Medium
  - `list_urls()` の `NotImplementedError` 提供形を見直し、未実装 API を service public API から除外する
- Low
  - 対象外

### `session_restore.py`

#### 事実
- 成功・失敗を `tuple[bool, str]` で表現している (`session_restore.py:19-29`)

#### 修正内容
- High
  - `SessionRestoreResult` DTO 化
- Medium
  - なし
- Low
  - 対象外

### `db_maintenance_service.py`

#### 事実
- 戻り値の大半が生 dict または object である (`db_maintenance_service.py:23-77`)

#### 修正内容
- High
  - DTO 化と例外体系整理
- Medium
  - public API 整理
- Low
  - 対象外

## 作業ステップ

1. 共通 DTO / Enum / 例外の新設
   - `agent/services/models.py`
   - `agent/services/enums.py`
   - `agent/services/exceptions.py`
   - `agent/services/io_ports.py`
2. message / history 依存の strict 化
   - `context_view.py`
   - `export_formatter.py`
   - `conversation_service.py`
   - `undo_service.py`
3. raw dict 入力の排除
   - `config_reload.py`
   - `db_maintenance_service.py`
4. 例外体系の fail-fast 化
   - `ingest_workflow.py`
   - `mcp_status.py`
   - `session_title.py`
5. I/O 依存の分離
   - `mcp_install.py`
   - `export_formatter.py`
6. tuple / dict 戻り値の DTO 化
   - `session_restore.py`
   - `undo_service.py`
   - `conversation_service.py`
   - `db_maintenance_service.py`
7. context 情報と status 情報の renderer 分離
   - `context_view.py`
   - `mcp_status.py`
8. 呼び出し側修正
   - command 層で DTO と具体例外へ追従
9. テスト更新
   - invalid role
   - invalid tier
   - invalid reload config
   - ingest stage failure
   - title generation response schema mismatch
   - export write failure
10. 静的検査
   - `mypy --strict`
   - `ruff check`
   - `pytest`

## 完了条件

### 必須
- 対象 11 ファイルから `except Exception` が除去されている
- `dict[str, Any]` が service 内部主要モデルから除去されている
- `str(args.get(...))`、`str(msg.get(...))`、`str(e)` のような無条件文字列化が除去されている
- `tuple[bool, str]`、`dict`、`object` 戻り値が DTO または具体例外へ置換されている
- `mcp_install.py` と `export_formatter.py` から直接 `print` / `input` が除去されている
- `context_view.py` の token 推定 fallback が削除されている
- `session_title.py` のタイトル生成 fallback が削除されている
- `mcp_status.py` の未知 tier 許容が削除されている

### 検証
- `mypy --strict` が通過している
- `ruff check` が通過している
- `pytest` が通過している
- 異常系テストが追加されている
  - invalid reload config
  - unknown tier
  - title generation HTTP error
  - title generation invalid schema
  - ingest crawl / split / ingest failure
  - export write error
  - invalid install role

### 不明
- command 層が現在どこまで `tuple[bool, str]` や raw dict 返却に依存しているかは不明
- `rag.ingestion.*` 実装が送出する具体例外型は添付範囲外のため不明
- `ctx.session`、`ctx.services.hist_mgr`、`ctx.services.memory` の戻り値契約の厳密性は添付範囲外のため不明
