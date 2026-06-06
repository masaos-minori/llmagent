# RAG パイプラインの Stage 分割

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
