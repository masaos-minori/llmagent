# Git / GitHub の危険操作ガードと artifact flow 整備

- 改善案: Git / GitHub の危険操作ガードと artifact flow 整備
- 実装方式: 運用ポリシー＋実装分離
- 実装手順概要:
  - Worker は commit 作成まで、push / PR / merge は Orchestrator のみ実行する。
  - protected branch、force push 禁止、allowed_repositories、PR review policy を定義する。
  - artifact.updated イベントで repo / branch / commit / path / lfs / pr を通知する。
  - Git の clone / cache / cleanup / retention policy を定義する。
- 実装対象:
  - orchestrator/gitops/
  - Git MCP
  - GitHub MCP
  - shared schemas
  - repo policy 設定
