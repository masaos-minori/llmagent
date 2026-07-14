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
