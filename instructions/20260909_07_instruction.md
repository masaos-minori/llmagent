# ツール結果全文の永続化と再参照性強化

- 改善案:
  - tool_result_store の FIFO メモリ保持だけでなく、ツール結果全文を DB 永続化し、セッション再開後も /tool list と /tool show で参照可能にすること。
- 効果:
  - 要約されたツール結果の元全文を後から監査・再利用できること。/session load 後もツール出力の追跡ができること。
- リスク:
  - DB サイズ増加と、機密情報保持期間の管理負担が増えること。
- 実装方式:
  - tool_results テーブルを新設し、session_id、turn_id、tool_name、args_masked、full_text、summary_text、created_at を保存し、/tool list と /tool show を DB ベース参照へ変更する方式。
- 実装対象:
  - agent_session.py
  - agent_commands.py
  - ToolResultStore 相当
  - DB マイグレーション

# 1.2 RAG パイプラインの Stage 分割

- 改善案: RAG パイプラインの Stage 分割
- 実装方式: パイプライン分解
- 実装手順概要:
  - PipelineStage.run(ctx) 共通インターフェースを定義する。
  - MQE / Search / Fusion(RRF) / Rerank / Refine / Augment を独立 stage 化する。
  - 各 stage 単体テストと latency 計測を追加する。
  - 検索結果の dry-run / debug 導線を追加する。
- 実装対象:
  - rag_pipeline.py
  - 検索・rerank 関連モジュール
  - command registry
  - /rag search 実装
