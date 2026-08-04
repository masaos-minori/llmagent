---
title: "Scripts File Structure: MCP: shell/rag-pipeline/cicd/mdq/git (Part 5/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-03-scripts-part2.md
  - 01_overview-files-03-scripts-part3.md
  - 01_overview-files-03-scripts-part4.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


各サーバのコアな4点セット（`<service>_server.py`, `<service>_service.py`, `<service>_tools.py`, `<service>_models.py`）には、サービス名が接頭辞として付与されています。補助的なモジュールやヘルパーは、接頭辞なしまたは部分的な接頭辞を持つ場合があります。詳細なファイル構成については、以下の各ディレクトリを参照してください：
- `scripts/mcp_servers/shell/` (# シェル MCP サーバ :8009)
- `scripts/mcp_servers/rag_pipeline/` (# RAG パイプライン MCP サーバ :8010)
- `scripts/mcp_servers/cicd/` (# GitHub Actions CI/CD MCP サーバ :8012)
- `scripts/mcp_servers/mdq/` (# Markdown Context Compression Engine MCP サーバ :8013)
  ※ FTS 管理ツールはコミット `74906389b` により廃止されました（後継ファイルなし）。`db_grep.py` および `db_schema.py` はこれとは無関係な既存モジュールです。
- `scripts/mcp_servers/git/` (# ローカル git 操作 MCP サーバ :8014)

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part4.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure
