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

## Skills 読み込み機構
- 課題: 「コードレビュー」「テスト生成」「移行ガイド」など定型手順を毎回会話で指示するのはコスト高。
- 改善案: skills/<name>/SKILL.md に手順テンプレートを定義し、/skill <name> [args] で呼び出せるようにする。
- 効果:
  - 定型手順の再利用により、指示の反復とトークン消費を削減。
  - 手順の標準化により、品質のばらつきを低減し再現性を向上。
  - プロジェクト / 個人スコープ分離により、運用拡張が容易。
- 難易度: 高
- 実装方式:
  - agent_commands.py: _cmd_skill(args) 新規。
  - agent_repl.py: 一時システム追記を渡せる extra_system_prompt 経路追加（必要なら）。
  - config/agent.json: skill_paths 追加。
- 実装対象:
  - agent_repl.py: extra_system_prompt 経路追加（一時システム追記）。
  - config/agent.json: skill_paths キー追加。
  - skills/<name>/SKILL.md: 手順テンプレート定義。

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
