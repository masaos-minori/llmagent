---
title: "Agent Inconsistencies and Known Issues"
category: agent
tags:
  - agent
  - inconsistencies
  - known-issues
  - bugs
related:
  - 05_agent_00_document-guide.md
---

# Agent Inconsistencies and Known Issues

## Purpose

agent 層（`agent/`、`shared/`）における既知の不具合、仕様の矛盾、文書間の不整合、未実装領域、未解決の疑問点を記録する。

## Design Intent

- 各エントリは「何が問題か」「なぜ問題なのか」「オペレータは何を確認すべきか」「どう対処すべきか」を明示する
- 「コード差分メモ」「ファイルX行Yで確認」のような機械的なマッピングは削除する（コードから機械的に導出可能な情報はソースを指すだけで十分）
- 運用判断は絶対に落とさない。不明な場合は保持して人間レビュー対象としてマークする

## Responsibility Boundary

- このファイルが所有するもの: agent 層の既知の不整合カタログ（5段階分類付き）
- このファイルが所有しないもの: 個別のバグ追跡（`issues/`）、実装の詳細な修正手順

## Key Constraints

- エントリを削除する前に現在のコードで不一致がまだ存在するか確認する
- 「Implementation fix required」分類のエントリは `issues/` に別途チケットを作成する
- 「Needs Confirmation」エントリの理由を常に明記する
- 5段階分類（Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable）を各エントリに付与する

## Operational Notes

- 現時点でオープンな項目はない（2026-07-23 移行完了後、すべてのエントリが5段階分類で処理済み）

## Known Limitations

- 既存のエントリは移行日（2026-07-23）時点のコードベースに基づいて分類されている。新しいエントリは随時追加が必要

## Related Docs

- `05_agent_00_document-guide.md`
