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

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。

# Agent Inconsistencies and Known Issues

このファイルは、agent 層（`agent/`、`shared/`）における既知の不具合、仕様の矛盾、
文書間の不整合、未実装領域、および未解決の疑問点を記録する。

---

### AGENT-001: use_memory_layer デフォルト値の文書間不一致

- **ID**: AGENT-001
- **Title**: use_memory_layer デフォルト値の文書間不一致
- **Status**: fixed
- **Severity**: Medium
- **Area**: Agent
- **Type**: document-document-mismatch
- **Source**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1 vs 05_agent_08_01, 05_agent_12_05, 05_agent_13_part2
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1
- **Related**: 未確認
- **Summary**: use_memory_layer のデフォルト値について文書間で矛盾がある
- **Current Description**: 一部ドキュメントで False、他で True と記載
- **Observed Implementation**: コード上のデータクラスデフォルトは True
- **Impact**: 実装者と文書の理解の乖離
- **Recommended Action**: 05_agent_08_03, 05_agent_09_02, 05_agent_12_02_part1 を修正して True に統一
- **Resolution Notes**: 完了済み

---

### AGENT-002: /export がトップレベルコマンドとして誤って記載

- **ID**: AGENT-002
- **Title**: /export がトップレベルコマンドとして誤って記載
- **Status**: fixed
- **Severity**: Low
- **Area**: Agent
- **Type**: document-document-mismatch
- **Source**: 05_agent_07_10 line 92 vs command_defs_list.py line 89-90
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: 05_agent_07_10
- **Related**: 未確認
- **Summary**: /export がトップレベルスラッシュコマンドとして誤って記載されている
- **Current Description**: /export [md|json] [file] がトップレベルコマンドとして記載
- **Observed Implementation**: /session export markdown/json が正しい構文
- **Impact**: CLI リファレンスの正確性に影響
- **Recommended Action**: 05_agent_07_10 を修正して /session export と明記
- **Resolution Notes**: 完了済み

---

### AGENT-003: RAG/Export カテゴリ名が誤り（/rag が存在しない）

- **ID**: AGENT-003
- **Title**: RAG/Export カテゴリ名が誤り（/rag が存在しない）
- **Status**: fixed
- **Severity**: Low
- **Area**: Agent
- **Type**: document-document-mismatch
- **Source**: 05_agent_07_10 title, 05_agent_07_01 index vs command_defs_list.py
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: 05_agent_07_10 title, 05_agent_07_01 index
- **Related**: 未確認
- **Summary**: 「RAG/Export」カテゴリとして記載されているが /rag コマンドは存在しない
- **Current Description**: ファイルタイトルと索引で「RAG/Export」カテゴリとして記載
- **Observed Implementation**: /compact と /session export のみ
- **Impact**: CLI リファレンスの正確性に影響
- **Recommended Action**: 05_agent_07_10 title と 05_agent_07_01 index を「Compact/Export」に統一
- **Resolution Notes**: 完了済み

---

## Related Documents

- `05_agent_00_document-guide.md`

## Keywords

agent
inconsistencies
known-issues
bugs
