# RAGパイプラインの段階分解

## 概要
RAGパイプラインを複数の段階に分割し、各段階を個別のクラスとして実装することで、コードの可読性と保守性を向上させます。

## 段階構造
パイプラインは以下の5つの段階に分割されます：

1. MQE (Multi-Query Expansion) - クエリ拡張
2. Search - 検索
3. Fusion (RRF Merge) - 結合
4. Rerank - 再ランク
5. Augment - 拡張

## パイプライン構成
- `scripts/rag/stage.py`: PipelineStageプロトコルとPipelineContextデータクラスの定義
- `scripts/rag/stages/`: 各段階の実装
  - `mqe.py`: MQE段階
  - `search.py`: 検索段階
  - `fusion.py`: 結合段階
  - `rerank.py`: 再ランク段階
  - `augment.py`: 拡張段階

## オブザーバビリティ
各段階はPipelineContextのオブザーバー機能をサポートしており、段階完了時にオブザーバーに通知します。