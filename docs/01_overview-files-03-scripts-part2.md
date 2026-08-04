---
title: "Scripts File Structure: Agent Commands (Part 2/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-03-scripts-part3.md
  - 01_overview-files-03-scripts-part4.md
  - 01_overview-files-03-scripts-part5.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   │   ├─ commands/
│   │   │   # 主要なスラッシュコマンド (/help, /config, /stats 等) を実装。
│   │   │   # 責任ごとに 12 個の mixin クラスに分割されており、詳細は
│   │   │   # scripts/agent/commands/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part4.md`
- `01_overview-files-03-scripts-part5.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure
