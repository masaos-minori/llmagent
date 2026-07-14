# LLM Agent Improve Summary（改善一覧・優先度順・AI読込向け簡潔版）

## 分散実行基盤の host registry / heartbeat / lease 管理
- 改善案: 分散実行基盤の host registry / heartbeat / lease 管理
- 難易度: 高
- 実装方式: 運用基盤追加
- 実装手順概要:
  - workers テーブルまたは Agent Registry で host registry を保持する。
  - heartbeat、lease timeout、ownership transfer、dead worker recovery を実装する。
  - orphan task reclaim と partial execution recovery を定義する。
- 実装対象:
  - orchestrator/registry/
  - metadata DB schema
  - worker runtime
  - event bus replication

## /diff コマンド（変更差分表示）
- 課題: エージェントがセッション中に行ったファイル変更を一覧で確認する手段がない。
- 改善案: エージェントが書き込んだファイルのパスを追跡し、/diff で git diff または内部 diff を表示する。
- 効果:
  - セッション中の変更点を即座に可視化でき、レビュー / 確認が容易。
  - 意図しない変更の早期検知により、事故・手戻りを低減。
  - 変更範囲の共有が容易になり、チーム内合意・引き継ぎに有効。
- 難易度: 中
- 実装方式:
  - agent_repl.py: _execute_one_tool_call() で modified_files 更新、スナップショット保存。
  - agent_commands.py: _cmd_diff(args) 新規。
- 実装対象:
  - agent_repl.py: _execute_one_tool_call() で modified_files セット更新、スナップショット保存ロジック追加。
  - agent_context.py: modified_files: set[str] / file_snapshots: dict[str, str] フィールド追加。
