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

## /branch（セッション分岐）
- 課題: 別案を検討するとき、現在の会話履歴を壊さずに分岐して試したい。
- 改善案: /branch <name> で現在の session_id と履歴をフォークし、新セッションとして実験できるようにする。
- 効果:
  - 別案検討を並行して進められ、現行案の履歴を破壊せずに試行可能。
  - 比較検討が容易になり、最終方針の品質向上。
  - やり直しコスト（履歴再構築、再説明）を削減。
- 難易度: 低
- 実装方式:
  - agent_commands.py: _cmd_branch(args) 新規。
- リスク:
  - session の INSERT のみ。ロールバックは対象 session の DELETE で可能。
- 実装対象:
  - agent_session.py: fork_session(name) 新規（セッションのコピーと新 session_id 生成）。

## /rewind（巻き戻し）
- 要望: /undo は直前 1 ターンのみ。複数ターン前の状態に戻したい場面がある。
- 改善案: /rewind <n> で n ターン前まで履歴・DB をロールバックする。
- 効果:
  - 誤誘導 / 誤前提の連鎖を早期に断ち切り、任意地点へ復旧可能。
  - 長いセッションでの試行錯誤の安全弁となり、心理的コストを低減。
  - 不要な履歴を除去でき、コンテキスト節約（トークン削減）に寄与。
- 難易度: 低
- 実装方式:
  - agent_commands.py: _cmd_rewind(args) 新規。
- リスク:
  - DB 削除は非可逆。削除前に session バックアップが必要。
- 対策:
  - 削除実行前に y/N 確認を追加し、sessions / messages テーブルを別テーブルに退避するか、DB ファイルをコピーする。
- 実装対象:
  - agent_session.py: delete_turns(n) 新規（複数ターンの DB 削除）。
