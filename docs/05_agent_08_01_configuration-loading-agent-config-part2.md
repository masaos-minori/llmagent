---
title: "Agent Configuration - Loading and AgentConfig Structure (Part 2)"
category: agent
tags:
  - agent
  - configuration
  - config-loading
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config-part1.md
---

# エージェント設定

- 運用 → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

`AgentConfig`の構造とフィールド間制約について文書化する。

## Design Intent

### 構造の概要

`AgentConfig`は7つのドメインサブ設定とスカラーフィールドで構成される:
- `llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`
- `security_lockdown_enabled`: DENY-ALL承認警告の抑制

### 無効なキー

`workflow_mode`と`workflow_require_approval`は有効なキーではない。
`build_agent_config()`はこれらのキーを消費せず、エラー・警告なしで無視される。

### ワークフロー必須の設計判断

エージェントは無条件に有効なワークフロー定義を要求する。
`StartupOrchestrator`の初期化処理は`Orchestrator.__init__()`の前に
2つのプレフライトチェックを呼び出す:
1. ワークフロー定義の存在チェック
2. ワークフロースキーマ検証

いずれのチェックも`StartupOrchestrator.run()`によって捕捉されない;
失敗はREPLに伝播し、起動を中止させる。

### フィールド間検証

- `rag.use_semantic_cache=True` → `rag.embed_url`は非空である必要がある
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir`は非空である必要がある
- `memory.memory_embed_enabled=True` → `rag.embed_url`は非空である必要がある

## Responsibility Boundary

- **正典**: `agent/config_builders.py`の`AgentConfig`データクラス

## Key Constraints

- ワークフロー定義は必須（スキップ不可）
- 無効なキーは静かに無視される

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`

## Keywords

configuration loading
hot-reload eligibility
AgentConfig structure
