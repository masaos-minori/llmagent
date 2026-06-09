# 実装順 TODO

対象: `agent/commands` 配下コマンド実装群

## 0. 実装方針

- 最優先方針は、後方互換性維持のために残っている facade 依存・遅延同期・手書き dispatch の重複を削除し、コマンド層を CLI 表示アダプタに縮退させること である。特に `cmd_memory.py` の `MemoryLayer` 依存と、`cmd_context.py` の system prompt 遅延同期は優先的な削除対象である。
- 実装順は、dispatch / 引数解析の正常化 → 後方互換機能の除去 → 業務ロジックの service 移管 → 出力整形共通化 の順とする。これにより、後続改修が局所実装へ再汚染されることを防ぐ。

## TODO 1. `registry.py` を宣言的コマンド定義方式へ再編する

### 目的

- `registry.py` は `_cmd_help()`、`sync_cmds`、`async_cmds`、`prefix_cmds`、plugin dispatch を個別管理しており、help / usage / dispatch の情報源が分散している。これを単一のコマンド定義メタデータへ統合する。

### 実施内容

- `dispatch()` の `sync_cmds` / `async_cmds` / `prefix_cmds` を 1 つの宣言的レジストリへ統合する。
- `_cmd_help()` の手書きヘルプを廃止し、コマンド定義から自動生成する。
- plugin コマンドも同じ定義系に乗せ、built-in / plugin の衝突検出ルールを実装する。

### 完了条件

- help / usage / dispatch の定義元が 1 か所になる。
- コマンド追加時に複数箇所を修正しなくて済む。


## TODO 2. 共通引数解析基盤を導入し、各 mixin の手書き parser を削除する

### 目的

- `/session`、`/db`、`/memory`、`/ingest`、`/note`、`/tool` などがそれぞれ `split()` / `isdigit()` / フラグ走査を個別に実装しているため、usage 判定・エラー表示・未知オプション処理が不統一である。

### 実施内容

- 共通 parser を導入し、以下の局所実装を削除対象とする。
  * `cmd_db.py` の `_parse_flag_int()` / `_parse_flag_str()`。
  * `cmd_session.py` の `parts = args.strip().split()` と手書き subcommand 分岐。
  * `cmd_memory.py` の `parts = args.strip().split()` と `--dry-run` / `isdigit()` 判定。
  * `cmd_notes.py` の `split(None, 1)` と `arg.isdigit()` 判定。
  * `cmd_ingest.py` の `lang` / `--snippets-only` 手解析。
  * `cmd_tooling.py` の `/tool show <id>` の `isdigit()` 判定。
- prefix コマンドの厳格なコマンド境界判定を導入し、`startswith()` の曖昧一致を廃止する。

### 完了条件

- 各 mixin に散在する引数解析ロジックが削除される。
- 未知オプション・不足引数・型不正の扱いが統一される。


## TODO 3. `cmd_memory.py` から `MemoryLayer` 依存を削除する

### 目的

- `cmd_memory.py` は `from agent.memory.layer import MemoryLayer` として後方互換 facade に依存しており、今回方針では最優先の削除対象である。一覧・検索・pin/unpin・delete・prune を新しい memory service 群へ直接接続する。

### 実施内容

- `MemoryLayer` の import と型依存を削除する。
- `list_entries()`, `search()`, `get_entry()`, `pin_entry()`, `unpin_entry()`, `delete_entry()`, `count_prunable()`, `prune()` を前提とする facade 呼出を廃止し、用途別 service API に置換する。
- `_memory_list()`, `_memory_search()`, `_memory_show()`, `_memory_pin()`, `_memory_delete()`, `_memory_prune()` の責務を、
  * state change / query service
  * audit service
  * formatter
    へ分解する。

### 完了条件

- `cmd_memory.py` から `MemoryLayer` 参照が消える。
- memory 操作が古い facade API に依存しなくなる。


## TODO 4. `cmd_context.py` の system prompt 遅延同期を廃止する

### 目的

- `_cmd_system()` は `ctx.conv.system_prompt_content` のみ更新し、`history[0]` は「次ターン開始時に Orchestrator が同期する」としている。この二重状態は後方互換的な逃げ道であり、即時一貫更新へ改めるべきである。

### 実施内容

- `_cmd_system()` 実行時に、canonical field だけでなく `history[0]` も即時更新する設計へ変更する。
- system prompt 切替ロジックを command から独立した service に移し、history 整合性をその service が保証する。
- 遅延同期前提のコメント・実装依存を削除する。

### 完了条件

- system prompt の保持状態が単一責務化される。
- 次ターンまで待たないと履歴整合しない状態がなくなる。


# 推奨実装順

1. TODO 1: `registry.py` 宣言的再編。dispatch / help / usage の単一化を最初に行う。
2. TODO 2: 共通引数解析基盤導入。各コマンドの局所 parser を先に整理する。
3. TODO 3: `cmd_memory.py` の `MemoryLayer` 依存削除。後方互換 facade を最優先で外す。
4. TODO 4: `cmd_context.py` system prompt 遅延同期廃止。二重状態を解消する。
