# 実装順 TODO

対象: `agent/commands` 配下コマンド実装群

## 0. 実装方針

- 最優先方針は、後方互換性維持のために残っている facade 依存・遅延同期・手書き dispatch の重複を削除し、コマンド層を CLI 表示アダプタに縮退させること である。特に `cmd_memory.py` の `MemoryLayer` 依存と、`cmd_context.py` の system prompt 遅延同期は優先的な削除対象である。
- 実装順は、dispatch / 引数解析の正常化 → 後方互換機能の除去 → 業務ロジックの service 移管 → 出力整形共通化 の順とする。これにより、後続改修が局所実装へ再汚染されることを防ぐ。

## TODO 5. `cmd_context.py` の undo / context 集約ロジックを service 化する

### 目的

- `_cmd_undo()` は `ctx.conv.history` を直接切り詰め、`_memory_injected` フラグを直接解釈している。また `_collect_context_state()` は chars 数・token 見積・memory 状態・git 情報まで広く集約しており、コマンド層の責務を超えている。

### 実施内容

- `_cmd_undo()` の rollback 処理を history manager または dedicated undo service へ移す。
- `_memory_injected` を直接見る履歴走査を service 側へ閉じ込める。
- `_collect_context_state()` と `_budget_breakdown()` を context view service / message analyzer に切り出す。

### 完了条件

- `cmd_context.py` が `ctx.conv.history` を複雑に直接加工しなくなる。
- context 表示用データ収集が command ローカル責務でなくなる。



## TODO 6. `cmd_session.py` のセッション復元・タイトル生成を service へ移す

### 目的

- `_generate_session_title()` は HTTP 呼出と prompt 組立を持ち、`_load_session()` は履歴復元・session 切替・統計リセットまで担っている。いずれもコマンド層ではなくセッション管理 service の責務である。

### 実施内容

- `_generate_session_title()` を session title service へ移し、prompt・fallback・HTTP 呼出を隠蔽する。
- `_load_session()` の中核ロジックを session restore service に移し、
  * session 切替
  * history 再構築
  * stats reset
    を一括実行する API にする。
- `_cmd_session()` の分岐は parser + service 呼出に縮小する。

### 完了条件

- `cmd_session.py` が session 内部状態を直接再構成しなくなる。
- タイトル生成と session restore が独立テスト可能になる。



## TODO 7. `cmd_db.py` の DB 操作を maintenance service へ集約する

### 目的

- `cmd_db.py` は stats、URL 一覧、clean、rebuild-fts、health、checkpoint、vacuum、purge、recover を直接束ねており、`SQLiteHelper` と `db.maintenance` へコマンドから直接依存している。これは CLI 層に DB 詳細が漏れている状態である。

### 実施内容

- `cmd_db.py` から `SQLiteHelper` 直接利用を減らし、統一 maintenance service 経由へ変更する。
- `_db_stats()`、`_db_rebuild_fts()`、`_db_health()`、`_db_checkpoint()`、`_db_vacuum()`、`_db_purge()`、`_db_recover()` を service 呼出の薄いラッパへ縮小する。
- `_db_clean()` の URL 文字列削除は見直し、文書 ID ベースまたは対象確認付き API に移行する。
- `_db_recover()` は高リスク操作として dry-run / confirm を service 仕様へ組み込む。

### 完了条件

- コマンド層が `rag` / `session` DB の役割差を直接知らなくて済む。
- DB maintenance の成否判定と保護ロジックが service 側で完結する。



## TODO 8. `cmd_config.py` を「表示」と「更新」に分割する

### 目的

- `cmd_config.py` には config 表示、stats 表示、runtime set、reload 適用が同居しており責務が過密である。また `_print_rag_config()` は `SQLiteHelper` の private 状態参照まで行っている。

### 実施内容

- `cmd_config.py` を少なくとも
  * config / stats view
  * config mutation / reload
    に分割する。
- `_print_rag_config()` から `SQLiteHelper._ensure_config()` と private 属性参照を除去し、DB path 表示は public API 経由にする。
- `_cmd_reload()` は `ConfigLoader` + `ConfigReloadService` の直列実行をやめ、単一 service API に一本化する。
- `_collect_stats()` と `_cmd_stats()` の表示責務を formatter に分離する。
- `_cmd_set()` は settable parameter の宣言定義化に置換する。

### 完了条件

- config 照会と変更が別責務になる。
- private helper / private 属性への依存が除去される。



## TODO 9. `mixin_base.py` の `_ctx` 暗黙依存を縮小する

### 目的

- `MixinBase` は `_ctx: AgentContext` を暗黙共有し、すべての mixin が同じ内部構造に直接アクセスする前提になっている。これが依存関係を不透明にしている。

### 実施内容

- command handler に必要な service / facade を明示注入する形へ移行する。
- `_reset_session_stats()` を stats service 経由の初期化 API に置換する。
- annotation base と shared helper の役割を分離する。

### 完了条件

- mixin / command object が `ctx` 全体を常に知る必要がなくなる。
- stats reset 項目が service 一元管理になる。



## TODO 10. `cmd_ingest.py` を export / ingest / compact に分離する

### 目的

- `_IngestMixin` には `/export`, `/ingest`, `/compact` が同居しており、履歴出力・外部取り込み・履歴圧縮という異なる責務をまとめている。

### 実施内容

- `_cmd_export()` を export command へ、`_cmd_ingest()` を ingest command へ、`_cmd_compact()` を compact command へ分離する。
- `_cmd_ingest()` は共通 parser 経由で validation を行うよう変更する。
- `_cmd_compact()` が `compress_turns * 2` など内部ルールを知っている状態をやめ、history manager の public API に隠蔽する。
- `TYPE_CHECKING: pass` の不要コードを削除する。

### 完了条件

- `_IngestMixin` の多責務が解消される。
- compact 判定ロジックがコマンド層から消える。



## TODO 11. `cmd_mcp.py` を status と install wizard で分離する

### 目的

- `cmd_mcp.py` は status table 表示と install wizard を同居させており、単なる状態照会コマンドと対話型セットアップが混在している。

### 実施内容

- `/mcp status` と `/mcp install` を別 command object とする。
- interactive wizard は専用 controller に切り出し、コマンド層は開始要求のみ行う。
- `validate_server_name` の関数内 import を整理し、重依存の扱いを composition root または service 初期化へ寄せる。
- `_cmd_mcp()` の default が status 実行になる挙動をやめ、usage 表示または help 表示へ変更する。

### 完了条件

- status 照会と install wizard の責務が分離される。
- 誤入力時に意図しない status 実行が起きなくなる。



## TODO 12. `cmd_tooling.py` を tool inspection と plan mode 制御で分離する

### 目的

- `_ToolingMixin` は `/tool` の結果参照と `/plan` の安全制御フラグ切替を同居させている。責務が異なるうえ、`plan_mode` は安全ポリシーに絡むため単純フラグ反転から脱却すべきである。

### 実施内容

- `/tool` 系と `/plan` を別 command object に分離する。
- `_cmd_plan()` の `ctx.conv.plan_mode` 直接 toggle を、policy / execution control service 管理へ移す。
- `_tool_show()` の JSON decode と表示整形を formatter に移す。

### 完了条件

- plan mode 管理が安全制御の service 責務になる。
- `cmd_tooling.py` の関心分離が改善される。



## TODO 13. `utils.py` の export / write 処理を service + formatter に分離する

### 目的

- `utils.py` の `render_history_md()`, `render_export()`, `write_export()` は履歴表現・出力形式切替・I/O・成功表示をまとめており、再利用性と拡張性が低い。

### 実施内容

- 履歴レンダリングを export formatter に切り出す。
- ファイル保存は I/O service に移し、`write_export()` は削除または薄い委譲にする。
- `fmt` の妥当性判定を parser 側で厳格にし、`json` 以外を黙って Markdown 扱いする挙動を改める。

### 完了条件

- export の表現と保存と表示が分離される。
- 出力形式拡張時の改修箇所が限定される。



## TODO 14. `cmd_notes.py` を notes service + formatter に分離する

### 目的

- `_note_add()`, `_note_list()`, `_note_delete()` は `ctx.session.*` を直接呼び、usage 表示と一覧整形まで兼務している。これは command-service 分離の観点で整理対象である。

### 実施内容

- note の追加・一覧・削除を notes service に移す。
- 一覧表示の列幅や preview 切詰めは formatter に移す。
- parser 共通化に合わせて `_cmd_note()` の手書き分岐を簡素化する。

### 完了条件

- `cmd_notes.py` が `ctx.session` に直接密着しなくなる。
- note 表示仕様の差し替えが容易になる。



## TODO 15. `cmd_debug.py` をログ制御と監視表示に分離する

### 目的

- `cmd_debug.py` は audit log tail、logger level 切替、`ctx.conv.debug_mode` toggle を同時に扱っている。用途が異なるため分割すべきである。

### 実施内容

- audit log 表示を monitoring / audit command へ分離する。
- logger level 切替を logging control service 化する。
- `agent_repl` / `orchestrator` の logger 名直書きを集中管理へ移す。
- audit tail 件数 `20` を設定化する。

### 完了条件

- `/debug` が多目的コマンドでなくなる。
- ログ制御対象と監査表示対象が明示化される。



# 推奨実装順

5. TODO 5: `cmd_context.py` undo / context service 化。履歴直接操作をやめる。
6. TODO 6: `cmd_session.py` の session restore / title generation service 化。 session 中核ロジックを command から外す。
7. TODO 7: `cmd_db.py` maintenance service 化。 DB 詳細を CLI 層から隠す。
8. TODO 8: `cmd_config.py` の view / mutation 分離。 private 依存も合わせて解消する。
9. TODO 9: `mixin_base.py` の `_ctx` 暗黙依存縮小。 DI 境界を明確化する。
10. TODO 10: `cmd_ingest.py` 分離。 export / ingest / compact を切り分ける。
11. TODO 11: `cmd_mcp.py` 分離。 status と install wizard を分離する。
12. TODO 12: `cmd_tooling.py` 分離。 tool inspection と plan mode を分離する。
13. TODO 13: `utils.py` の export 処理分離。 formatter / I/O service に再配置する。
14. TODO 14: `cmd_notes.py` service 化。 notes 操作を command から切り離す。
15. TODO 15: `cmd_debug.py` 分離。 debug の多目的化を解く。
