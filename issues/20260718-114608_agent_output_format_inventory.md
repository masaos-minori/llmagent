# エージェント実行時の画面出力機能の洗い出しと分類(フォーマット統一の事前調査)

**部分対応 (2026-07-19).** 本ファイル「推奨アクション」のうち以下2点を実施:

- `write_debug_rag`(`cli_view.py:206-240` 相当 および `commands/output_port.py:94-133` 相当。
  行番号は削除により失効)の重複デッドコードを削除(`cli_view.py` の `_print_rag_candidate` ヘルパー、
  `commands/output_port.py` の `OutputPort` Protocol 宣言、`tests/test_cli_view.py::test_write_debug_rag`
  も合わせて削除)。復活は行わない判断(呼び出し元が2度とも「不要になったコマンドの削除」で消えており、
  復活を前提とする根拠がないため)。
- 角括弧プレフィックス(`[warn]` `[fatal]` `[error]` `[tool]` `[approval]` `[denied]`
  `[plan-blocked]` `[skipped]` `[approval-pending]` `[context]` `[rag]` `[non-fatal]` `[workflow]`
  `[usage]`)を新設の `scripts/agent/output_tags.py`(`OutputTag` StrEnum)に一元化。
  `[fatal]`/`[FATAL]` の大文字小文字不統一(`startup.py` 2箇所、`workflow/validate.py` 1箇所)は
  小文字 `[fatal]` に統一(`cli_view.py` 側の既存表記を正とした)。影響を受けた
  `tests/test_startup.py::test_production_profile_raises_on_start_failure` の
  `pytest.raises(match="FATAL")` は `match=r"\[fatal\]"` に更新。

未対応のまま残る項目(ユーザーが対象外と判断):

- `OutputPort`/`Writer` の1系統への統合(出力APIの3系統混在の解消)。
- `services/export_formatter.py` の `sys.stdout.write()` を他と同じ出力口に揃えるか。
- `write_table` 未使用箇所(`cmd_mcp.py` の独自テーブル実装、`cmd_config_display.py` の個別整形)の統一。
- `cmd_audit.py`/`cmd_context.py` のエラー表現メソッド不統一(`write_error()` 未使用箇所)。
- ロギングとの二重化(`orchestrator.py`、`startup.py` の `logger.warning` + 画面表示)。

これらは元issueの「統一方針そのものはまだ決定していない」に該当し、別途ユーザー判断が必要。

## 背景

エージェント実行時のターミナル出力フォーマットを統一したいという要望を受け、
現状どの機能がどこで画面出力を行っているかを洗い出し、フォーマットの不統一箇所を
事実ベースで整理した。統一方針そのものはまだ決定していない。

パッケージ実体は `agent/` ではなく `scripts/agent/` 配下(`scripts/` が PYTHONPATH
ルート)。以下のパスは `scripts/agent/` を起点とする。

## 出力の入口(4系統に分散)

| 入口 | 実装方式 | 主な役割 |
|---|---|---|
| `cli_view.py` (`CLIView`) | 直接 `print()`(22箇所) | LLMストリーミング、進捗/スピナー、警告/致命的エラー、起動バナー |
| `tool_output.py` (`emit_*` 関数群) | `commands/output_port.py` の `CliOutputPort` 経由 | ツール呼び出し/結果/承認プロンプト表示 |
| `commands/output_port.py` (`OutputPort` / `CliOutputPort`) | 直接 `print()`(19箇所) | 全スラッシュコマンド(`cmd_*.py` 14ファイル)の共通出力口 |
| `services/export_formatter.py` | `sys.stdout.write()` | `/export` の会話エクスポート出力 |
| `workflow/validate.py` | `print()` / `print(..., file=sys.stderr)` | REPLとは独立したデプロイ時検証CLI(エージェント本体とは無関係) |

`rich` / `click.echo` / ANSIカラー / Markdownレンダラーの使用は無し。全てプレーンテキスト。

## 機能別分類

- **ストリーミング/ターン制御**: `write_token`, `write_turn_start`, `write_turn_end`
  (`cli_view.py:130-145`)。`llm_client.py` / `orchestrator.py` / `history.py` はコール
  バック経由で呼ぶのみで自ら `print` しない。
- **進捗/待機表示**: `write_progress`, `clear_progress`, `start_spinner` /
  `stop_spinner`(`cli_view.py:151-181`)。`\r` で同一行上書き。
- **警告/致命的エラー**: `write_warning`(`[warn]`), `write_fatal`(`[fatal]`)。
  `repl.py` / `startup.py` から呼ばれる。
- **起動バナー**: `write_startup_banner`(`cli_view.py:191-204`)。
  `DB: N chunks | Tools: N` 等。
- **ツール実行/承認フロー**: `emit_tool_call`, `emit_tool_result`,
  `emit_approval_prompt`, `emit_denied`, `emit_plan_blocked`, `emit_skipped`,
  `emit_approval_pending_notice`(`tool_output.py`)。承認入力自体は
  `tool_approval.py` の `input("  Execute? [y/N]: ")`。
- **スラッシュコマンド全般**: `write`, `write_success`, `write_error`,
  `write_no_data`, `write_validation_error`, `write_table`, `write_kv`
  (`commands/output_port.py`)。`cmd_session.py` / `cmd_mcp.py` / `cmd_context.py`
  等14ファイルが利用。
- **監査ログ/デバッグ表示**: `/audit`(`cmd_audit.py`)、`/debug`(`cmd_debug.py`)。
- **エクスポート**: `/export`(`services/export_formatter.py`)。
- **独立検証ツール**: `workflow/validate.py`(エージェント起動とは無関係)。

## フォーマット不統一の実例(統一の際の主な論点)

1. **出力APIが3系統混在**: `print()` 直呼び出し / `sys.stdout.write()`
   (`export_formatter.py` のみ)/ Protocol経由(`Writer`, `OutputPort`)。
2. **`write_debug_rag` の重複実装(デッドコード確定)**: `cli_view.py:206-240` と
   `commands/output_port.py:94-133` にほぼ同一ロジックが2重に存在する。
   `grep -rn "write_debug_rag" --include="*.py" .` で全リポジトリを検索した結果、
   ヒットするのは両メソッドの定義自体と `tests/test_cli_view.py` の直接呼び出し
   テストのみで、プロダクションコードからの呼び出しは0件。`ctx.conv.debug_mode` を
   参照する箇所も `cmd_debug.py`(トグル)と `cmd_config_stats.py`(ON/OFF表示)の
   2箇所のみで、RAGパイプライン実行時に `debug_mode` を見て `write_debug_rag` を
   呼ぶ経路はコードベース上に存在しない。削除漏れの経緯は下記「調査で判明した経緯」
   を参照。
3. **角括弧プレフィックスの散在**: `[warn]` `[fatal]`/`[FATAL]`(大文字小文字不統一)
   `[error]` `[tool]` `[approval]` `[denied]` `[plan-blocked]` `[skipped]`
   `[approval-pending]` `[debug]` `[context]` `[rag]` `[usage]` `[non-fatal]`
   `[workflow]` が各モジュールに文字列リテラルでハードコードされ、共通の定数/Enum
   管理が無い。
4. **テーブル表示の不統一**: `write_table()` が用意されているが実利用は
   `cmd_session.py:125`, `cmd_memory.py:159` の2箇所のみ。`cmd_mcp.py` は独自の
   `_format_mcp_table()` で別の固定幅フォーマットを実装しており、
   `cmd_config_display.py` は `write()` で個別にインデント/コロン整形している。
5. **エラー表現の不統一**: `cmd_audit.py` の "not found" 系メッセージは
   `write_error()` ではなく生の `write()`。`cmd_context.py` は
   `write_no_data(f"[warn] {...}")` のように `write_warning()` を使わず別メソッドに
   タグを埋め込んでいる。
6. **標準エラー出力の不統一**: `file=sys.stderr` は `workflow/validate.py` のみで、
   他はエラーメッセージも含め全て標準出力。
7. **ロギングとの二重化**: `orchestrator.py:290-316`, `startup.py:304-329` で
   `logger.warning` と画面表示(`write_warning` 相当)が同時に行われている。

## 調査で判明した経緯(`write_debug_rag` の削除漏れの実態)

git履歴を追った結果、`cli_view.py` 側と `commands/output_port.py` 側の
`write_debug_rag` は、それぞれ**別の時代に別のRAGデバッグ機能から呼ばれていたが、
呼び出し元だけが個別に削除され、メソッド本体が両方とも取り残された**という、
二重の削除漏れであることが判明した。

- **`cli_view.py` 側**: コミット `124499ac` 付近で `scripts/agent/rag_debug.py` /
  `repl_debug.py` が導入され、`on_debug` コールバック(コメント曰く
  `CLIView.write_debug_rag` を想定)経由でRAGデバッグ情報を渡す設計だった。その後
  コミット `271084c8`("refactor(agent): remove obsolete files, backward-compat
  stubs, and split session.py")で `rag_debug.py` / `repl_debug.py` が
  "no live imports"(コミットメッセージより引用)として削除された。この時点で
  `on_debug` を実際に配線していた呼び出し元は既に失われていたが、
  `cli_view.CLIView.write_debug_rag` 自体は削除対象に含まれず現在まで残存している。
- **`commands/output_port.py` 側**: 上記削除後、コミット `e3bf8af5`
  ("impl: wire debug_fn in /rag search --debug; show fallback reasons in
  timings")で `/rag search <query> --debug` サブコマンド(当時 `cmd_ingest.py`、
  後に `cmd_rag_export.py`)から `self._out.write_debug_rag(...)` を呼ぶ形で
  独立に再実装された。その後2026-07-14のコミット `846dc93b`
  ("feat: remove dead RAG pipeline settings from Agent config and unused
  /db rag /rag commands")で `/rag` スラッシュコマンドが丸ごと削除され、この
  呼び出し元も一緒に消えたが、`commands/output_port.py` 側の
  `write_debug_rag` メソッド自体は削除対象に含まれず現在まで残存している。
- いずれの削除コミットも「不要になった呼び出し元・コマンドを消す」意図の変更であり、
  コミットメッセージ上、メソッド本体を意図的に残す・将来復活させる旨の記述は無い。
  そのため両メソッドは**単純な削除漏れ**と判断でき、復活を前提とする根拠は無い。

検証コマンド:

```
grep -rn "write_debug_rag" --include="*.py" .
grep -rn "debug_mode" scripts/ --include="*.py"
git log --all --oneline --diff-filter=A -S"def write_debug_rag" -- '*cli_view.py'
git log --all --oneline -S"def write_debug_rag" -- '*output_port.py'
git show 271084c8 --stat | grep -i "rag_debug\|repl_debug"
git show 846dc93b --stat | grep -i "cmd_rag_export\|cmd_db"
```

## 未確認・不明点

- 統一方針(採用フォーマット、プレフィックス体系の一元化、テーブル方式の統一など
  の方向性)は本調査の時点では未決定 — これは事実調査ではなく意思決定待ちの事項
  であるため、引き続き未確定のまま残る。

## 推奨アクション(次のステップの選択肢)

- `write_debug_rag`(`cli_view.py:206-240`, `commands/output_port.py:94-133`)は
  デッドコードと確定したため、削除するか(RAGデバッグ表示機能自体を廃止扱いにする)、
  もしくは何らかの形で復活させるか(例: `/debug` に旧`/rag search --debug`相当の
  サブコマンドを追加する)を決定する。現状放置すると3.の重複実装がさらに
  フォーマット不統一の温床になる。
- プレフィックスタグ(`[warn]` 等)を列挙型または定数モジュールに一元化する設計を
  検討する。
- `commands/output_port.py` の `OutputPort` を `cli_view.py` の `Writer` と統合し、
  出力APIを1系統(Protocol経由)に寄せることを検討する。
- `services/export_formatter.py` の `sys.stdout.write()` を他と同じ出力口に揃える
  かどうかを判断する。
