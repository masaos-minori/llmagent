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

> **正典となる仕様。** 本セクションは `repl_health.py` におけるtool definitionsチェックについて記述する。
> ルーティングのドリフト検出（`route_resolver.py` の `validate_routing_against_live`）については
> [04_mcp_03 §Drift validation](04_mcp_03_02_tool-registry.md#drift-validation) を参照。
> これらは異なる機能である。

tool definitionsチェックはagentの起動時に実行され、`config/agent.toml` の `tool_definitions` を、実際の `/v1/tools` レスポンスと比較する。挙動はサーバへの到達可能性と `tool_definitions_strict` の設定によって変わる:

| シナリオ | `strict = false` | `strict = true` |
|---|---|---|
| **一部到達不能** — 一部のサーバが応答する | 到達可能なサーバで検証が進行する；到達不能なサーバは `WARNING` としてログに出力される | 同様 — 到達可能なtoolのみを比較する；到達可能なtoolに不一致があれば `RuntimeError` が発生する |
| **全て到達不能** — どのサーバも応答しない | 検証がスキップされる；`INFO: "All MCP servers unreachable ... skipping tool definition check"` — **local mode: SKIPPED outcome means all tool calls will fail for that session** | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
| **Tool不一致** — 到達可能だが名前が異なる | 方向ごとに `WARNING`（missing_in_server / extra_on_servers） | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

### Startup validation statuses

#### WARNING
A non-critical issue. The system continues operating but the operator should be aware.
Example: optional server discovery failed.
Displayed via `write_warning()` with `[warn]` prefix.

#### FATAL
A critical issue that prevents normal operation. The system may be partially functional.
Displayed via `write_fatal()` with `[fatal]` prefix for visual distinction.
Example: required server discovery failed.

#### SKIPPED
Discovery was skipped entirely. In local mode, this may indicate a full-session tool-call outage.
Displayed via `write_warning()` with `[SKIPPED]` prefix.
Example: MCP discovery skipped due to missing configuration.

### Production vs local behavior differences

MCP discovery behaves differently between production and local modes:

**Duplicate tools:**
- Production: FATAL outcome, startup blocked
- Local: WARNING outcome, startup continues

**Unreachable servers:**
- Production: FATAL outcome, startup blocked
- Local: SKIPPED outcome, startup continues but all tool calls will fail for that session

This difference exists because local mode is designed to be more forgiving during development, while production mode enforces strict validation to prevent partial functionality.

**要点:**
- strictモードでのtool名の不一致は `RuntimeError` を発生させる。
- strictモードで全サーバが到達不能な場合、到達不能なサーバの一覧を含む `RuntimeError` が発生する。非strictモードでは、検証はINFOログとともにスキップされる。
- エラーメッセージは、運用者がデバッグしやすいように、不一致と到達不能サーバを明確に区別して表示する。

**重要:** local modeでdiscoveryがSKIPPEDの場合、起動は継続するが、RuntimeToolRegistryは空または不完全なままになる。このため、LLMがツールを認識していても実行時にすべて失敗する。運用者は`mcp_tool_discovery`のSKIPPED結果をWARNINGと同様の重大度で扱う必要がある。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
