---
title: "Startup Validation Behavior (`tool_definitions_strict`)"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Startup Validation Behavior (`tool_definitions_strict`)

## Startup Validation Behavior (`tool_definitions_strict`)

> **正典となる仕様。** 本セクションは `repl_health.py` におけるtool definitionsチェックについて記述する。
> ルーティングのドリフト検出（`route_resolver.py` の `validate_routing_against_live`）については
> [04_mcp_03 §Drift validation](04_mcp_03_routing_lifecycle_and_execution.md#drift-validation) を参照。
> これらは異なる機能である — `04_mcp_90 §SPEC-01` も参照。

tool definitionsチェックはagentの起動時に実行され、`config/agent.toml` の `tool_definitions` を、実際の `/v1/tools` レスポンスと比較する。挙動はサーバへの到達可能性と `tool_definitions_strict` の設定によって変わる:

| シナリオ | `strict = false` | `strict = true` |
|---|---|---|
| **一部到達不能** — 一部のサーバが応答する | 到達可能なサーバで検証が進行する；到達不能なサーバは `WARNING` としてログに出力される | 同様 — 到達可能なtoolのみを比較する；到達可能なtoolに不一致があれば `RuntimeError` が発生する |
| **全て到達不能** — どのサーバも応答しない | 検証がスキップされる；`INFO: "All MCP servers unreachable ... skipping tool definition check"` | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
| **Tool不一致** — 到達可能だが名前が異なる | 方向ごとに `WARNING`（missing_in_server / extra_on_servers） | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

**要点:**
- strictモードでのtool名の不一致は `RuntimeError` を発生させる。
- strictモードで全サーバが到達不能な場合、到達不能なサーバの一覧を含む `RuntimeError` が発生する。非strictモードでは、検証はINFOログとともにスキップされる。
- エラーメッセージは、運用者がデバッグしやすいように、不一致と到達不能サーバを明確に区別して表示する。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
