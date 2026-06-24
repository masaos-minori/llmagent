# Implementation Procedure: docs/03_rag_05_configuration_and_operations.md

## Goal

`rag_crawler.toml` を `config/rag_pipeline.toml` に統一する (docs 内の検索置換)。

## Scope

**In:**
- `docs/03_rag_05_configuration_and_operations.md:250` — `rag_crawler.toml` → `config/rag_pipeline.toml`
- その他 RAG docs の同様な誤記

**Out:** config loader 実装の変更

## Implementation

```bash
# 1. 誤記を全 RAG docs から検索
grep -rn "rag_crawler.toml\|rag-pipeline\|crawl.toml" docs/

# 2. 置換
sed -i 's/rag_crawler\.toml/config\/rag_pipeline.toml/g' docs/03_rag_05_configuration_and_operations.md
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 誤記なし | `grep -rn "rag_crawler.toml" docs/` | 0 matches |
| 正名称のみ | `grep -rn "rag_pipeline.toml" docs/03_rag_05*.md` | 全参照あり |
