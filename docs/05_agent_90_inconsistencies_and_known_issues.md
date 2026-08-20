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

## 5-Tier Scheme Exception Rationale

This document retains its 5-tier classification scheme (Design Decision / Implementation Bug / Documentation Gap / Needs Confirmation / Operational Observation) as an intentional, documented area-specific exception to the common 17-field Known Issues template (`00_governance_04_known-issues-template.md`).

**Rationale:** The 5-tier scheme serves a distinct classification purpose not directly expressible by the common template's Status/Type fields. Specifically, it separates "confirmed design decision" (意図的な設計判断) from "active defect" (実装上の不具合) at a granularity that the common template's Status (open/resolved/deferred) and Type (implementation-bug/documentation-gap/design-gap/operational-gap) fields do not directly express. The common template conflates "this is a known and accepted design choice" with "this is an acknowledged bug awaiting fix," whereas the Agent document's domain-specific workflow benefits from keeping these semantically distinct.

**Current state:** This document currently has zero open entries to migrate (all historical items resolved or reclassified). The 5-tier scheme adds zero maintenance overhead in its current state.

**Future consideration:** If the common template evolves to include a "Design Decision" type or equivalent discriminator, re-evaluation of this exception may be warranted. Until then, the 5-tier scheme remains the canonical classification for Agent-known-issues.

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
