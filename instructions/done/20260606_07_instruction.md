# Prompt Injection / Retrieval Trust 対策

- 改善案: Prompt Injection / Retrieval Trust 対策
- 実装方式: セキュリティ強化
- 実装手順概要:
  - document sanitization、tool instruction isolation、citation separation を導入
  - retrieval trust scoring を導入
  - RAG 文書とシステム指示の混線を避けるプロンプト境界を定義
- 実装対象:
  - rag_pipeline.py
  - prompt builder
  - retriever 実装
  - security policy 実装
