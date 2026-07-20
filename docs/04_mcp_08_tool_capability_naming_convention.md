---
title: "MCP Tool Capability Naming Convention"
category: mcp
tags:
  - mcp
  - tool-schema
  - capabilities
  - policy
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_07_tool_schema_export_policy.md
---

# MCPツールケイパビリティ命名規則

## 概要

MCPツールは任意のケイパビリティメタデータを宣言できる。ケイパビリティは `{domain}.{action}` または `{domain}.{subdomain}.{action}` 形式の文字列で、ツールがどのドメインに対してどのようなアクションを実行できるかを示す。

この命名規則は**オプティブ**であり、既存のツールは採用する必要がない。発見サービスはこのフィールドの欠如を許容する（[mcp_tool_discovery.py](04_mcp_03_06_tool-runtime-availability-metadata.md)参照）。

関連: [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — ToolRegistry の所有権・ルーティングの役割について説明している（本ドキュメントのケイパビリティ命名規則とは異なる）。

関連: [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) — TOOL_LISTエクスポートの正規名について説明している（本ドキュメントのケイパビリティ命名規則とは異なる）。

## 命名規則

ケイパビリティ文字列は以下の形式に従う:

``` json
{domain}.{action}
または
{domain}.{subdomain}.{action}
```

- すべてのセグメントは小文字のみ
- セグメント内にはスペースやアンダースコアを含めない
- ドットで区切る
- 正規表現で表すと: `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`

**注意**: この正規表現は文書化目的のみであり、**ランタイムでの正規表現バリデーションは追加されない**。本ドキュメントは形状の慣例を定義するだけで、バリデータの実装を義務付けるものではない。

## ドメイン

ドメインは論理的なリソース領域であり、必ずしもMCPサーバーの名前と1:1に対応するわけではない:

- `filesystem` — ファイルシステム操作
- `git` — Gitリポジトリ操作
- `github` — GitHub API操作
- `process` — プロセス/シェル操作
- `search` — 検索操作
- その他将来のドメイン

このリストは**オープンかつ拡張可能**であり、閉じた列挙型ではない。

## アクションと read/write/delete/admin の区別

アクションは小さな拡張可能な語彙セットで、主に以下の基本アクションに anchored されている:

- `read` — リーダー操作
- `write` — ライター操作
- `delete` — デリーター操作
- `execute` — プロセス/シェルのようなアクション

ドメイン固有の動詞も存在する。例えば `github.issue.write` は単なる `github.write` よりも正確である。

## 複数キャパビリティ

ツールは複数のケイパビリティを宣言できる（例: リードと副作用の両方をトリガーするツール）。そのため、対応する `RuntimeTool` フィールドは単一の文字列ではなく `tuple[str, ...]` である（[runtime_tool.py](04_mcp_03_06_tool-runtime-availability-metadata.md)参照）。

## 具体例

要件の例をそのまま記載する:

- `filesystem.read`
- `filesystem.write`
- `filesystem.delete`
- `git.read`
- `git.write`
- `github.issue.write`
- `process.execute`
- `search.web`

**現在採用しているツール:**

- `browser_fetch` (`web_search-mcp`) — `("web_fetch",)`

## ステータス

これは提案中の標準慣習であり、web_search-mcp の `browser_fetch` が `web_fetch` ケイパビリティを宣言したことで初めて実装に採用された。他のサーバーへの展開は将来の別途スコープされた作業である（リスク#1の緩和策 — 文書が「すでに実証済み」と読まれないようにするため）。

## Related Documents

- [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) — MCPドキュメントガイド
- [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) — ToolRegistryの所有権・ルーティング
- [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) — TOOL_LISTエクスポートの正規名
- [04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md) — RuntimeToolのケイパビリティフィールド

## Keywords

mcp
tool-schema
capabilities
naming-convention
policy
