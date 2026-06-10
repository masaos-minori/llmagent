# Command 層 改修指示書

## 1. 全体方針

### 1-1. 改修方針

* command 層は 入力受付・引数解析・service 呼び出し・結果表示の委譲 のみを担当すること。
  `cmd_context.py` は context 収集を service に委譲しつつ `/clear` と `/system` では直接状態変更をしており、`cmd_db.py` は service 呼び出しと表示・例外処理を同居させているため、この混在を解消する。
* 後方互換性は維持しない。
  旧 usage 形式の温存、曖昧な入力許容、fallback 的分岐、broad exception による握りつぶしは削除する。`cmd_db.py` では複数の subcommand が `sqlite3.Error` / `Exception` を個別に拾って CLI 表示へ逃がしているが、この方式は廃止する。
* 出力はすべて formatter / presenter に寄せること。
  `cmd_context.py` の token line 表示や `cmd_db.py` の stats / health / usage 出力、`cmd_ingest.py` の ingest / RAG / compact 結果表示は command 内で組み立てない。

### 1-2. 実装ルール

* `args.split()` ベースの ad-hoc 解析を禁止する。
* `print()` に業務ロジックを混ぜない。
* `ctx` への直接状態変更を禁止する。
* `except Exception` による握りつぶしを禁止する。
* 成功 / 失敗 / validation error / no data の表示形式を共通化する。
* subcommand を持つ command は、辞書 dispatch ではなく subcommand spec で定義する。
  `cmd_db.py` の hand-written dispatch と `cmd_ingest.py` の個別引数解釈は、この方針で置き換える。

## 2. ファイルごとの修正内容

## 2-1. `registry.py`

### High

* `_COMMANDS` を実質的な唯一のコマンド仕様定義に昇格させること。
* command 名、sync/async、handler、help だけでなく、引数仕様・subcommand 仕様・formatter 仕様まで保持できる構造へ変更すること。
* registry は dispatch 専用に限定し、usage 生成・個別 help 整形・表示ロジックを持たせないこと。

### Medium

* `/help` は `_COMMANDS` から自動生成し、各ファイルに分散した usage 文言を将来的に削除できる構造へ変える。
* built-in command と plugin command を同一 spec 形式で扱えるようにする。
* exact-match / prefix-match の二分法を見直し、subcommand command を第一級で表現できるようにする。

## 2-2. `mixin_base.py`

### High

* `MixinBase` は 最小共通基盤に限定し、業務ロジックを保持しないこと。
* session stats reset のような処理は service に集約し、base class には状態操作ロジックを持たせないこと。

### Medium

* 共通化する責務は「context access」「formatter 呼び出し」「validation wrapper」などに限定する。
* mixin 継承前提の肥大化を防ぐため、将来的に composition に移行可能な薄い基盤へ寄せる。

## 2-3. `utils.py`

### High

* `parse_flag_int()` / `parse_flag_str()` を廃止し、正式な引数解析 API に置き換えること。
* parser は以下を厳密に扱うこと:
  * 必須引数不足
  * 不正型
  * 重複 flag
  * 未知 flag
  * 値なし flag
* 解析失敗は `None` ではなく、ValidationError または structured parse error を返すこと。

### Medium

* positional / optional / quoted string / subcommand を扱える parser schema を定義する。
* parser spec から usage を自動生成できるようにする。

## 2-4. `cmd_context.py`

### High

* `_cmd_clear()` を command 内の `ctx.conv.history` 直接操作から切り離し、ConversationLifecycleService に移すこと。
  現状は history を直接切り詰め、`new` 指定時に新 session 開始も mixin で実行しているため、この副作用は service 側へ集約する。
* `_cmd_system()` から `ctx.conv.system_prompt_name` / `system_prompt_content` / `history[0]` の直接更新を排除し、SystemPromptService に委譲すること。
* `_cmd_history()` の `int(args.strip())` ベースの簡易解析をやめ、共通 parser に統一すること。
* `_print_token_line()` を formatter へ移すこと。

### Medium

* `collect_context_state()` の戻り値 `dict` を typed DTO に変更する。
  token count、limit、breakdown、system preview などを field 化し、formatter で表示を組み立てる。
* token source label の判定 (`LLM usage` / `/tokenize (next turn)` / `chars/4`) を formatter または enum ベース変換に移す。
* `/context` の breakdown 表示を共通 table formatter に統一する。

## 2-5. `cmd_db.py`

### High

* `_cmd_db()` の辞書 dispatch を廃止し、subcommand spec 定義に置き換えること。
  `stats / urls / clean / rebuild-fts / health / checkpoint / vacuum / purge / recover` を spec と parser に基づいて扱う。
* `_db_stats()` / `_db_rebuild_fts()` / `_db_health()` / `_db_checkpoint()` / `_db_vacuum()` / `_db_purge()` / `_db_recover()` にある `except sqlite3.Error` / `except Exception` を全面削除すること。
  例外分類は service 層に寄せ、command 側では structured result のみを扱う。
* `_db_clean()` の delete 処理を DbDocumentCommandService へ切り出し、成功 / not found / validation error を result object として返すようにする。
* `/db urls` の `--lang` / `--limit` 解析を共通 parser へ移す。

### Medium

* `/db` を以下の責務に分割できる構造へ寄せること:
  * query 系(stats / urls / health)
  * maintenance 系(checkpoint / vacuum / purge / recover / rebuild-fts)
  * destructive 系(clean / recover)
* `/db recover` や `/db purge` のような破壊的処理は、dry-run 可能な request / result DTO を持たせる。
* stats / urls / health の表示を formatter に寄せる。
  現状は command 側が直接テーブル/行出力を組み立てている。

## 2-6. `cmd_memory.py`

### High

* `_cmd_memory()` の dispatch を subcommand spec ベースに書き換えること。
* state-changing command(pin / unpin / delete / prune)は、command 内で store に近い処理を行わず、MemoryCommandService / MemoryMutationUseCase に集約すること。
* dry-run を持つ prune / delete 系は、実行結果 DTO と 監査ログ DTO を返す構造にすること。
* broad exception を削除し、失敗は分類済み結果または明示的例外で返すこと。

### Medium

* `MemoryOpResult` を command 内部 DTO ではなく、service レイヤの正式結果 DTO として整理する。
* list / search / show / pin / unpin / delete / prune の表示組み立てを formatter に切り出す。
* command 層での JSON 文字列化やロギング制御を減らし、presenter / audit service に寄せる。

## 2-7. `cmd_notes.py`

### High

* `_cmd_note()` の `if/elif` ベース dispatch を subcommand spec に置き換えること。
* `_note_add()` / `_note_delete()` の `print()` 直書き + session 直接呼び出しを service result ベースへ変更すること。
* `arg.isdigit()` 依存の簡易 validation を parser ベースへ置換すること。

### Medium

* `_format_notes_table()` を formatter モジュールへ移す。
* note add/list/delete の結果を共通 result 出力へ統一する。
* “Failed to add note." のような曖昧な失敗表現を廃止し、失敗カテゴリを返す構造にする。

## 2-8. `cmd_session.py`

### High

* `_session_load_safe()` / `_session_delete()` の「手書き int 変換 + print」を廃止し、parser + service result に置き換えること。
* `_cmd_session()` の `if/elif` dispatcher を subcommand spec へ置換すること。
* current session 削除禁止ロジックは command ではなく、SessionCommandService で判定させること。
* `set_title()` や `delete_session()` など session 操作は service 経由へ統一すること。

### Medium

* `_load_session()` の restore 結果メッセージは formatter で生成する。
* session list / load / rename / delete の request DTO / result DTO を揃える。
* タイトル自動生成の依存関係を DI 可能な形へ整理する。

## 2-9. `cmd_tooling.py`

### High

* `/tool` と `/plan` を同居させる構造を見直し、必要なら責務分割すること。
* `ctx.tool_result_store` への直接依存を避け、ToolResultQueryService 経由へ変更すること。
* `_tool_list()` / `_tool_show()` の出力組み立てを formatter へ移すこと。
* 一覧表示では full payload を前提とせず、summary 中心へ寄せること。

### Medium

* `/plan` は単純な boolean toggle ではなく、現在値・変更結果・有効範囲を返す result にする。
* JSON/raw 表示が必要な場合は formatter option として扱う。

## 2-10. `cmd_config.py`

### High

* `_cmd_config` / `_cmd_set` / `_cmd_reload` の責務を service に分離すること。
* 個別 setter(例: temperature, max\_tokens など)は command 内に持たず、RuntimeConfigService に集約すること。
* reload 時の broad exception を廃止し、失敗理由を分類した result に置き換えること。
* 設定表示と設定変更の command を内部的に明確に分離すること。

### Medium

* `_print_*` 系メソッド群を formatter 化する。
* config 表示用 DTO を定義する。
* 可変設定 / 起動時固定設定 / 再起動要設定を区別して出力できるようにする。

## 2-11. `cmd_debug.py`

### High

* `_cmd_debug()` の各分岐を、diagnostic spec + query service 方式へ変更すること。
* 例外時に logger へ出して終わるのではなく、structured diagnostic result を返すこと。
* 内部状態収集は command 層から分離し、DebugInfoService を新設して集約すること。

### Medium

* debug 出力のフォーマットを共通化する。
* 機密値・トークン・秘密情報がそのまま出ないようにフィルタ層を入れる。

## 2-12. `cmd_ingest.py`

### High

* `_cmd_export()` の `fmt` / `outfile` 解釈を parser + request DTO に置き換えること。
  現状は `md/json` と filename を同一ループで手作業判定しているため、仕様が曖昧になりやすい。
* `_cmd_ingest()` の `target / lang / --snippets-only` 解析を parser へ移し、`print()` を用いた進行表示・失敗表示を formatter 経由にすること。
* `_cmd_rag()` の `search` subcommand / `--debug` / query の解釈を command 専用 parser へ置き換えること。
  また、config 読み込み失敗時の fallback `{}` を削除し、fail-fast にすること。
* `_cmd_compact()` の `ctx.conv.history` 直接代入をやめ、HistoryCompressionService に委譲すること。

### Medium

* export / ingest / rag / compact を 1 mixin に同居させる妥当性を見直すこと。
* ingest / rag は progress / summary / error を持つ result DTO を返すこと。
* stage timing (`--debug`) の表示を formatter で統一する。

## 2-13. `cmd_mcp.py`

### High

* MCP command は status / list / check / install の subcommand spec を明示化し、手書き usage を持たせないこと。
* install/scaffold 系の副作用処理は、command から切り離して McpInstallService に集約すること。
* query 系(status/list/check)と mutation 系(install/update 等)を分離すること。

### Medium

* テーブル表示や next steps 表示は formatter / presenter に移す。
* MCP server 状態取得、tool list 取得、接続確認を個別の query service に分離する。

## 3. 作業ステップ

### Step 1. 共通基盤の先行改修

1. `registry.py` を改修し、command spec / subcommand spec / async/sync dispatch の土台を作る。
2. `utils.py` を parser module として再設計する。
3. `mixin_base.py` を薄い共通基盤に整理する。

### Step 2. 輸出と結果型の統一

4. command 共通の result DTO / error DTO / formatter interface を定義する。
5. usage / validation error / success / no data の共通 formatter を実装する。

### Step 3. 状態変更系 command の service 化

6. `cmd_context.py` の `/clear` `/system` を service 化する。
7. `cmd_session.py` の load / rename / delete を service 化する。
8. `cmd_memory.py` の pin / unpin / delete / prune を service 化する。
9. `cmd_db.py` の purge / clean / recover など破壊的処理を service 化する。
10. `cmd_ingest.py` の compact / ingest / export / rag を service + request DTO 化する。

### Step 4. 表示ロジックの排出

11. `cmd_context.py`, `cmd_db.py`, `cmd_notes.py`, `cmd_tooling.py`, `cmd_config.py`, `cmd_ingest.py`, `cmd_mcp.py` から表示整形処理を formatter に移す。

### Step 5. 例外処理の正規化

12. command 層の broad exception をすべて削除する。
13. service 層で validation / domain / infra error を分類し、command には最終結果のみ返す。

### Step 6. command 別の仕上げ

14. `cmd_tooling.py`, `cmd_debug.py`, `cmd_mcp.py`, `cmd_config.py` の責務分離を完了する。
15. 各 usage を registry 主導に置き換える。
16. 各 command のユニットテスト / parser テスト / formatter テストを追加する。

## 4. 完了条件

以下をすべて満たしたら完了とする。

* command 層が 入力受付・service 呼び出し・formatter 委譲 のみになっている。
* `ctx` の直接状態変更が command 層から排除されている。
  特に `cmd_context.py` と `cmd_ingest.py` にある history / system prompt / compact の直接操作が消えている。
* `cmd_db.py` に存在する broad exception ベースの CLI 表示がなくなっている。
* subcommand を持つ command がすべて spec + parser ベースで動作している。
* usage が registry / parser schema から自動生成されている。
* success / failure / validation error / no data の表示が共通フォーマットに統一されている。
* 破壊的操作が request/result DTO と audit log を持つ。
* 後方互換のための曖昧処理・fallback・温情的分岐が残っていない。
