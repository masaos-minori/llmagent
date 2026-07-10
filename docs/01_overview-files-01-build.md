---
title: "Build and Models File Structure"
category: overview
tags:
  - build
  - llama-cpp
  - models
  - gguf
  - deployment
  - file-structure
related:
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
  - 01_overview.md
source:
  - 01_overview-files.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

```
/opt/llm/
├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8001)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8003)
```

## Related Documents

- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`

## Keywords

build
llama-cpp
models
gguf
deployment
file-structure
