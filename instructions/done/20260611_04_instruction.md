# コマンド層改修計画書

## 全体方針

### 事実
- 対象ファイルは `cmd_memory.py`、`cmd_notes.py`、`cmd_session.py`、`cmd_tooling.py`、`formatter.py`、`mixin_base.py`、`registry.py`、`utils.py`、`cmd_config.py`、`cmd_context.py`、`cmd_db.py`、`cmd_debug.py`、`cmd_ingest.py`、`cmd_mcp.py` の 14 ファイルである
- 複数ファイルで command handler と出力処理が密結合している
  - `print()` を直接使用
    - `cmd_memory.py`
    - `cmd_session.py`
    - `cmd_tooling.py`
    - `formatter.py`
    - `registry.py`
    - `cmd_config.py`
    - `cmd_context.py`
    - `cmd_debug.py`
    - `cmd_ingest.py`
    - `cmd_mcp.py`
- 複数ファイルで raw `dict` / `.get()` ベースの曖昧参照が存在する
  - `cmd_tooling.py`
  - `cmd_config.py`
  - `cmd_context.py`
  - `cmd_db.py`
- 例外の握り方が粗い箇所が存在する
  - `cmd_config.py:232,332` に `except Exception`
- 一部の command は service 層の `tuple[bool, str]` 返却や文字列返却に依存する
  - `cmd_session.py:115-116`
  - `cmd_context.py:105-115`
- 後方互換的な緩い入力吸収が存在する
  - `cmd_mcp.py` 系で install 時のエラーを usage message へ変換
  - `cmd_db.py` で `--lang` / `--limit` を緩く解釈
  - `cmd_tooling.py` で invalid JSON を空 dict 表示へ縮退

### 推測
- 現状は REPL 向け利便性を優先した設計であり、fail-fast と strict typing を適用するには command 層と presentation 層の分離が必要になる可能性が高い
- `cmd_config.py`、`cmd_context.py`、`cmd_mcp.py`、`registry.py` が command 層再編の起点になる可能性が高い
- `formatter.py` をそのまま残すと各 mixin の `print()` 依存が残存しやすい可能性が高い

### 改修方針
- 後方互換性は維持しない。暗黙補正、フォールバック、曖昧な usage 補完を削除する
- `assert` を業務ロジックで使用しない。前提条件違反は明示例外を送出する
- `except Exception` を使用しない。捕捉対象を具体例外に限定する
- `dict[str, Any]` を外部境界以外で使用しない。境界通過直後に型変換する
- `str(args.get(...))` のような無条件文字列化を禁止する。入力型を検証し、期待型以外は例外とする
- 変換・型付けは厳密に行う
- `None` と空文字と未設定を同一視しない
- 監査ログ、承認判定、実行結果は専用 DTO を定義する
- LLM 由来 JSON は decode 後に schema 検証する。schema 不一致は即時失敗とする
- 出力は直接 `print` せず、UI/CLI 出力用インターフェースへ集約する
- 不明な tool 名、不明な tier、不明な metadata は fail-open ではなく fail-fast とする

## 実装ルール

### 必須ルール
- command handler は raw text を parse した後、直ちに request DTO へ変換する
- command handler は service からの戻り値文字列をそのまま表示しない。result DTO を renderer に渡す
- `print()` と `input()` は command 層本体から排除し、`agent/commands/output_port.py` へ集約する
- `dict` / `list[dict]` / `tuple[bool, str]` を command 層の主要契約として使わない
- `.get()` を前提にした曖昧参照を禁止する
- usage error と domain error を分離し、専用例外または result type を使う
- config / status / context / db 出力は renderer 専用 DTO へ変換してから整形する
- subcommand dispatch は文字列比較だけでなく command spec DTO と validator を通す

### 新設すべき共通要素
- `agent/commands/models.py`
  - `CommandRequest`
  - `CommandResult`
  - `ValidationErrorResult`
  - `MemoryCommandRequest`
  - `NoteCommandRequest`
  - `SessionCommandRequest`
  - `ToolResultView`
  - `ConfigViewModel`
  - `ContextViewModel`
  - `DbCommandRequest`
  - `McpInstallRequest`
  - `McpInstallRenderModel`
- `agent/commands/enums.py`
  - `CommandKind`
  - `MemoryAction`
  - `SessionAction`
  - `ContextAction`
  - `DbAction`
  - `McpAction`
  - `ToolingAction`
- `agent/commands/exceptions.py`
  - `CommandParseError`
  - `CommandValidationError`
  - `CommandDispatchError`
  - `CommandRenderingError`
  - `UnknownSubcommandError`
  - `UnknownPresetError`
  - `UnknownTierError`
- `agent/commands/output_port.py`
  - `OutputPort`
  - `TableRenderer`
  - `TextRenderer`
  - `JsonRenderer`

## ファイルごとの修正内容

### `cmd_config.py`

#### 事実
- `_collect_stats()` が `dict[str, Any]` を返す (`cmd_config.py:31-62`)
- `_cmd_stats()` と複数 `_print_*` が直接 `print()` を行う (`cmd_config.py` 全体)
- `_cmd_config()` と `_cmd_reload()` に `except Exception` が存在する (`cmd_config.py:232,332`)
- `_cmd_reload()` は `ConfigLoader` と raw dict に依存する

#### 修正内容
- High
  - `_collect_stats()` の戻り値を `StatsViewModel` DTO に変更する
  - `except Exception` を廃止し、`ConfigLoadError`、`CommandValidationError`、`ConfigReloadValidationError` 等の具体例外へ分解する
  - `_cmd_reload()` の raw config 適用を `ReloadCommandRequest` DTO + validator 経由へ変更する
  - 直接 `print()` を廃止し、renderer へ委譲する
- Medium
  - `_print_*` 群を `config_renderer.py` へ分離し、mixin から整形責務を除去する
  - `/set` の runtime override も request DTO 化し、値域検証を統一する
- Low
  - ヘルプ文言と出力ラベルの統一整理

### `cmd_context.py`

#### 事実
- `_cmd_context()` は service から受けた state dict をそのまま表示する
- `_cmd_clear()`、`_cmd_undo()` は service 戻り値の `tuple[bool, str]` / 文字列に依存する (`cmd_context.py:103-115`)
- `_cmd_history()` は `msg.get("content")` を直接参照する (`cmd_context.py:132-137`)
- `_cmd_system()` は `ValueError` を usage message に変換する (`cmd_context.py:149-153`)

#### 修正内容
- High
  - context state を `ContextViewModel` DTO に統一し、raw dict 依存を削除する
  - `_cmd_clear()`、`_cmd_undo()`、`_cmd_system()` の service 契約を result DTO / 具体例外へ変更する
  - `msg.get("content")` を禁止し、message DTO から参照する
  - 直接 `print()` を廃止する
- Medium
  - history preview 生成を renderer に分離する
  - `ContextAction` Enum と request DTO を導入し、subcommand ごとの分岐責務を縮小する
- Low
  - context 出力順序と表示ラベルの再整理

### `cmd_mcp.py`

#### 事実
- `_print_mcp_install_next_steps()` で大量の `print()` を使用する (`cmd_mcp.py:46-85`)
- `_cmd_mcp_status()` と `_cmd_mcp_install()` が presentation と control flow を混在させる
- install 処理で `ValueError`、`FileExistsError`、`OSError` を catch して usage / 失敗表示を行う (`cmd_mcp.py:110-126`)
- `_format_mcp_table()` が status DTO ではなく表示文字列前提で表を構築する

#### 修正内容
- High
  - `print()` を全廃し、`McpInstallRenderModel` / `McpStatusRenderModel` を renderer へ渡す方式へ変更する
  - install command の入力を `McpInstallRequest` DTO として厳密検証する
  - 例外を usage 系と domain 系に分離し、catch を具体例外のみに限定する
  - `_format_mcp_table()` を raw string formatter ではなく typed renderer へ移行する
- Medium
  - `_cmd_mcp_status()` と `_cmd_mcp_install()` を command dispatcher と renderer 呼び出しに分割する
  - next steps 文字列群をテンプレート化し、command 本体から除去する
- Low
  - `/mcp` help 文面の整理

### `registry.py`

#### 事実
- `_cmd_help()` で直接 `print()` を使用する (`registry.py:239-246`)
- `dispatch()` は command spec と plugin dispatch を兼務する
- `CommandDef` / `SubcommandSpec` はあるが、request DTO・result DTO ではない

#### 修正内容
- High
  - `dispatch()` の入力を `CommandRequest` DTO に統一する
  - `_cmd_help()` の直接 `print()` を廃止する
  - unknown command / unknown plugin を `CommandDispatchError` によって fail-fast させる
- Medium
  - registry の責務を `parse` / `resolve` / `execute` / `render` に分割する
  - `CommandDef` と `SubcommandSpec` を validator 連携可能な immutable DTO に置換する
- Low
  - help 出力の整形ロジック共通化

### `cmd_memory.py`

#### 事実
- `_cmd_memory()` と各 subcommand が直接 `print()` を行う (`cmd_memory.py` 全体)
- subcommand dispatch は `dispatch.get(sub)` による文字列依存である (`cmd_memory.py:76-89`)
- `MemoryOpResult.action` は生文字列である (`cmd_memory.py:39-44`)
- `_emit_memory_audit()` は `orjson.dumps()` で直接 event を作る (`cmd_memory.py:223-239`)

#### 修正内容
- High
  - Memory command 入力を `MemoryCommandRequest` DTO に統一する
  - `print()` を全廃し、memory renderer に委譲する
  - `MemoryOpResult.action` を Enum 化し、audit payload も専用 DTO へ変更する
  - unknown subcommand を `UnknownSubcommandError` で fail-fast させる
- Medium
  - prune / delete / pin / unpin を command handler から service adapter へ分離する
  - list / search / show の表示モデルを DTO 化し、table / detail renderer を分離する
- Low
  - help 文面と列幅の整理

### `cmd_db.py`

#### 事実
- `_db_list_urls()` で `parsed.flags.get()` と `str(...)` / `isdigit()` による緩い型変換を行う (`cmd_db.py:91-96`)
- `_db_purge()` も raw flags を直接扱う (`cmd_db.py:146-149`)
- command 層は db service の raw dict 戻り値前提で表示を行う

#### 修正内容
- High
  - DB command 入力を `DbCommandRequest` DTO に変更する
  - `parsed.flags.get()` + `str(...)` による曖昧変換を廃止し、validator で厳密変換する
  - service からの dict 戻り値依存を DTO に置換する
- Medium
  - `_db_stats()`、`_db_health()`、`_db_checkpoint()` などの表示を renderer 分離する
  - `_db_clean()` と `_db_purge()` の request validation を共通化する
- Low
  - サブコマンド help 文面の整理

### `cmd_ingest.py`

#### 事実
- `_cmd_ingest()`、`_cmd_rag()`、`_cmd_compact()` が直接 `print()` を行う (`cmd_ingest.py` 全体)
- service 戻り値の messages を command が逐次表示する構造である
- 一部 `.get()` ベース参照がある

#### 修正内容
- High
  - ingest command の request / result を DTO 化し、messages の生表示を止める
  - `print()` を廃止し、progress renderer または event sink 経由へ移行する
  - ingest failure は service 例外と result DTO により分離する
- Medium
  - `/rag`、`/compact` の分岐を専用 action DTO へ分離する
  - stage 表示を command 本体から除去し、renderer に寄せる
- Low
  - help 出力と stage ラベル文言の整理

### `cmd_tooling.py`

#### 事実
- `print()` を多用する (`cmd_tooling.py` 全体)
- `result.get("summary")`、`result.get("args_masked")` のような dict 参照がある (`cmd_tooling.py:32-33,47,50,55`)
- `orjson.loads(result.get("args_masked") or "{}")` で invalid JSON を空 dict へ縮退する (`cmd_tooling.py:50-52`)

#### 修正内容
- High
  - tool result 表示を `ToolResultView` DTO に統一する
  - invalid JSON を `{}` へ縮退させず、schema 不一致として即時失敗させる
  - `print()` を廃止し、renderer へ移行する
- Medium
  - `/tool list` と `/tool show` の列定義・detail 表示を renderer に分離する
  - `/plan` 表示も DTO 化し、blocked tool 一覧を typed list とする
- Low
  - 出力ラベル整理

### `cmd_session.py`

#### 事実
- `_load_session()` は `restore_session()` の戻り値からメッセージだけを取り出して `print()` する (`cmd_session.py:115-116`)
- service 戻り値が `tuple[bool, str]` 前提である

#### 修正内容
- High
  - session command の service 契約を `SessionCommandResult` DTO に変更する
  - `print()` を廃止し、renderer に委譲する
  - load / delete / title 生成を result DTO と具体例外で扱う
- Medium
  - `_session_load_safe()` と `_load_session()` の責務重複を整理する
  - session subcommand の parse 結果を DTO 化する
- Low
  - help 文面統一

### `cmd_debug.py`

#### 事実
- 直接 `print()` を使用する (`cmd_debug.py` 全体)
- `OSError` を catch してその場で表示する (`cmd_debug.py:37-39`)

#### 修正内容
- High
  - debug 出力を DTO + renderer 化する
  - `OSError` を command 内で文字列化せず、具体例外または error result に変換する
- Medium
  - debug 情報の収集と表示を分離する
- Low
  - debug ラベル整形の整理

### `cmd_notes.py`

#### 事実
- command から session API を直接呼ぶ
- `_note_list()` は row 配列をその場で構築する
- `dispatch.get(parsed.subcommand or "")` による文字列依存 dispatch である (`cmd_notes.py:76`)

#### 修正内容
- High
  - note command を request DTO + result DTO 化する
  - unknown subcommand を `UnknownSubcommandError` に変更する
- Medium
  - row 配列生成を renderer に移す
  - note add / delete の validation を共通化する
- Low
  - note list の truncation ルール整理

### `formatter.py`

#### 事実
- `print_success()`、`print_error()`、`print_table()` などが直接 `print()` を実行する (`formatter.py` 全体)
- table / kv / text 出力の表現が標準出力に固定されている

#### 修正内容
- High
  - `print_*` API を廃止し、`OutputPort` インターフェースへ置換する
  - command 層から標準出力固定の依存を除去する
- Medium
  - table / kv / text を renderer strategy として分離する
- Low
  - 色付けや装飾などの拡張ポイント整理

### `utils.py`

#### 事実
- `parse_flag_int()` が `ValueError` を catch して `None` を返す (`utils.py:70-78`)
- `return None` による parse failure の曖昧表現がある

#### 修正内容
- High
  - parse failure を `None` 返却で吸収せず、`CommandParseError` / `CommandValidationError` として返す
  - `ParsedArgs` の flags を raw dict のまま持たず、typed parse result へ変更する
- Medium
  - `parse_command_args()` を tokenizer と semantic parser に分割する
- Low
  - flag alias 整理

### `cmd_memory.py`

#### 事実
- audit event を command 層が直接構築する (`cmd_memory.py:223-239`)

#### 修正内容
- High
  - audit event 構築を service / audit adapter へ移譲する
- Medium
  - なし
- Low
  - 対象外

### `mixin_base.py`

#### 事実
- `reset_session_stats()` を mixin 外の共通関数として提供する
- 重大な `except Exception`、`print()`、raw dict 契約は確認していない

#### 修正内容
- High
  - 該当なし
- Medium
  - command shared utility と mixin base の責務を分離し、state mutation helper を services 側へ寄せる
- Low
  - docstring 整理

## 作業ステップ

1. command 契約の定義
   - `agent/commands/models.py`
   - `agent/commands/enums.py`
   - `agent/commands/exceptions.py`
   - `agent/commands/output_port.py`
2. 出力責務の分離
   - `formatter.py` を `OutputPort` 実装へ置換
   - `cmd_memory.py`
   - `cmd_tooling.py`
   - `cmd_config.py`
   - `cmd_context.py`
   - `cmd_debug.py`
   - `cmd_ingest.py`
   - `cmd_mcp.py`
3. raw dict / tuple 契約の排除
   - `cmd_config.py`
   - `cmd_context.py`
   - `cmd_session.py`
   - `cmd_db.py`
   - `cmd_tooling.py`
4. parse / validation の strict 化
   - `utils.py`
   - `cmd_notes.py`
   - `cmd_db.py`
   - `cmd_mcp.py`
5. registry の再編
   - `registry.py` を parse / resolve / execute / render に分割
6. command と service の境界見直し
   - memory / session / context / db / mcp / ingest の各 command で result DTO を導入
7. audit と domain error の責務整理
   - `cmd_memory.py` の audit event 構築移譲
   - `cmd_config.py` の reload error 分離
8. テスト更新
   - unknown subcommand
   - invalid flag value
   - invalid JSON in tool result store
   - unknown preset
   - unknown tier
   - mcp install validation failure
9. 静的検査
   - `mypy --strict`
   - `ruff check`
   - `pytest`

## 完了条件

### 必須
- 対象 14 ファイルから業務ロジック上の `assert` が排除されている
- 対象 14 ファイルから `except Exception` が排除されている
- command 層の主要契約から `dict[str, Any]`、raw `dict`、`tuple[bool, str]` が除去されている
- `str(args.get(...))`、`str(msg.get(...))` のような無条件文字列化が除去されている
- `formatter.py` を含む command 出力が直接 `print()` に依存しない
- unknown subcommand / unknown preset / unknown tier / invalid JSON / invalid flag が fail-fast で扱われる
- command 層での audit event 直接構築が除去される
- 後方互換のための暗黙補正とフォールバックが削除される

### 検証
- `mypy --strict` が通過している
- `ruff check` が通過している
- `pytest` が通過している
- 異常系テストが追加されている
  - invalid flag
  - unknown subcommand
  - unknown preset
  - unknown tier
  - tool result invalid JSON
  - mcp install invalid request
  - config reload error

### 不明
- service 層側が現在どこまで raw dict / tuple 戻り値に依存しているかは不明
- plugin command が registry のどの契約に依存するかは添付範囲からは一部不明
- memory / db / mcp の下位 service が送出する具体例外型は添付範囲外のため不明
