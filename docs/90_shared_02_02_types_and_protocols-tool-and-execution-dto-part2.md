---
title: "Shared Types and Protocols - Tool and Execution DTOs (Part 2)"
category: shared
tags:
  - shared
  - types
  - tool-dto
  - action-result
  - tool-spec
  - cache
  - events
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_03_types_and_protocols-reference.md
source:
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 7c. `ToolDefinition` (`shared/tool_registry.py`)

不変のツール定義 — 1 つのツールは必ず 1 つの MCP サーバーに属する。(Explicit in code: `scripts/shared/tool_registry.py` docstring)

**境界条件:** `description` と `input_schema` は将来利用のための予約フィールドであり、デフォルトレジストリ初期化関数では一切設定されず、現状どの呼び出し元からも読まれない。LLMに見せるツールスキーマは各サーバー自身の `tools.py` の `TOOL_LIST` が情報源であり、この `ToolRegistry` からではない。(Explicit in code)

`ToolRegistry` はツールの所有権・ルーティングのみを扱う。ライブ `/v1/tools` の応答は起動時のドリフト検証にのみ使われ、ルーティング判断には使われない。(Explicit in code)

Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

`ArtifactEvent` (event_type, repo, branch, commit, path, pr_number, session_id, timestamp) — リポジトリアーティファクト作成/更新時に発行。(Explicit in code: `scripts/shared/events.py` モジュールdocstring)

> **Note:** `ArtifactEvent` は純粋なデータ構造(`TypedDict`)である。配信の仕組み・イベントバス・購読者は一切存在しない。将来的にアーティファクトイベントを発行しうるコードのための型注釈としてのみ存在する。`ArtifactEvent` のインスタンス生成が何らかのアクションをトリガーすると仮定してはならない。

`RetryEvent` (event_type, workflow_id, task_id, attempt_number, max_attempts, error_type, backoff_sec, session_id, timestamp) — ワークフローステージのリトライ時に発行。

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

不変の `frozen=True` dataclass — FastAPI、MCP、エージェントへの依存はない(shared → external のみ)。`mcp_servers/shell/service.py`(`ShellService`)がその設定オブジェクトとして使用する。(Explicit in code: `scripts/shared/protocols/shell.py`)

**失敗時の意図:** `__post_init__` で以下を検証し、違反時は `ValueError` を送出する: `kill_policy` は `{"sigterm_then_sigkill", "sigkill_only"}` のいずれか、`sandbox_backend` は `{"firejail", "none"}` のいずれか、`timeout_sec >= 1`、`max_output_kb >= 1`、`max_memory_mb >= 1`、`kill_grace_sec >= 0`。(Explicit in code: `scripts/shared/protocols/shell.py`)

目的: シェル実行ポリシーを MCP サーバー実装から分離すること。

Import: `from shared.protocols.shell import ShellPolicy`

---


