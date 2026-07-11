---
title: "5. Constraints Reference"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 5. 制約リファレンス

## 5. 制約リファレンス

| Constraint | Value |
|---|---|
| 言語判定の閾値 | CJK比率 ≥ 0.10 → `ja`; ページが100文字未満 → ヒント言語を使用 |
| チャンクサイズの範囲 | 40〜500文字 (設定可能) |
| チャンクの重複 | 50文字のスライディングウィンドウ |
| 埋め込みの次元数 | 384 (本番環境、`config/agent.toml:43`)。float32リトルエンディアンBLOB |
| クロール深度 | 最大6ホップ |
| クロールページ数の上限 | サイトごと最大500ページ |
| レプリカ | 単一ノードのSQLiteのみ |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
