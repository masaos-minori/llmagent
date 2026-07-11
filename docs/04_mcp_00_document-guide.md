---
title: "MCP Documentation Guide"
category: mcp
tags:
  - mcp
  - documentation
  - guide
  - routing
  - file-index
related:
  - 04_mcp_01_system_overview.md
  - 04_mcp_02_protocol_and_transport.md
  - 04_mcp_03_routing_lifecycle_and_execution.md
  - 04_mcp_04_server_catalog.md
  - 04_mcp_05_security_and_safety_model.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_07_tool_schema_export_policy.md
  - 04_mcp_90_inconsistencies_and_known_issues.md
---

# MCP Documentation Guide

再構成されたMCPドキュメント群のエントリポイント。
どの章を開くべきかを判断するために、まず本ファイルを読むこと。

---

## Reading Order

```
01 → 02 → 03 → 04 → 05 → 06 → 90
```

---

## AI Query Routing Table

| 質問 | ファイル |
|---|---|
| どのMCPサーバが存在し、何をするのか？ | `04_mcp_01` |
| サーバはどのポートで動作するのか？ | `04_mcp_01` |
| どの起動モードが利用可能か？ | `04_mcp_01` |
| `/v1/call_tool` はどのように動作するのか？ | `04_mcp_02` |
| Bearer認証はどのように動作するのか？ | `04_mcp_02` |
| audit logのフォーマットは？ | `04_mcp_02` |
| toolはどのようにサーバへルーティングされるのか？ | `04_mcp_03` |
| ToolExecutorはどのように動作するのか？ | `04_mcp_03` |
| watchdogはどのように動作するのか？ | `04_mcp_03` §Watchdog；config defaultsは `04_mcp_06` §Major Default Values |
| 新しいMCPサーバを追加するには？ | `04_mcp_03` |
| 起動時のtool-definition警告はどのように発生するのか？ | `04_mcp_06` §Startup Validation Behavior |
| MCPの障害を診断するには？ | `04_mcp_06` §MCP Failure Diagnosis |
| web-search-mcpが提供するtoolは？ | `04_mcp_04` |
| github-mcpが提供するtoolは？ | `04_mcp_04` |
| shell-mcpのshell_runが受け付けるものは？ | `04_mcp_04` |
| mdq-mcpは本番稼働可能か？ | `04_mcp_04`（本番稼働可能；FTS5検索とインデックスが実装済み） |
| allowed_dirsはどのように動作するのか？ | `04_mcp_05` |
| githubのallowed_reposはどのように動作するのか？ | `04_mcp_05` |
| fail-closedとfail-openの違いは？ | `04_mcp_05` |
| どのtoolがdry_runに対応しているか？ | `04_mcp_05` |
| リスクティアとは何か？ | `04_mcp_05` |
| tool schemaモジュールはどのように命名されるのか？ | `04_mcp_07` |
| 正典となるTOOL_LISTエクスポートとは？ | `04_mcp_07` |
| _MCP_TOOLS参照をクリーンアップするには？ | `04_mcp_07` |
| サーバごとにどのconfigファイルが存在するのか？ | `04_mcp_06` |
| サーバが健全かどうかを検証するには？ | `04_mcp_06` |
| デフォルトのconfig値は何か？ | `04_mcp_06` |
| MDQとRAGはどちらを使うべきか？ | `04_mcp_05 §MDQ vs RAG Boundary` |
| MDQ/RAG境界のルールとは？ | `04_mcp_05 §MDQ vs RAG Boundary` |
| 何が壊れているか、または未実装なのか？ | `04_mcp_90` |

---

## Navigation to Major Known Issues

| 課題 | 場所 |
|---|---|
| mdq-mcpは本番稼働可能（FTS5検索とインデックスが実装済み） | [04_mcp_04 §mdq-mcp](04_mcp_04_server_catalog.md) |
| cicd workflow_allowlistのRuntimeErrorに関する記載の不整合 | [MCP-09](04_mcp_90_inconsistencies_and_known_issues.md#mcp-09-cicd-workflow_allowlist-policy-mismatch--runtimeerror-vs-warning) |

---

## Canonical Source Rules

- `06_ref-mcp.md` は `ToolExecutor`、`HttpTransport`、routingについての正典であった。内容は現在 `04_mcp_03` にある。
- `04_spec_mcp.md` はシステム概要、サーバ一覧、McpServerConfigについての正典であった。内容は現在 `04_mcp_01`、`04_mcp_03`、`04_mcp_06` にある。
- `04_mcp-protocol.md` はwatchdog、起動モード、新規サーバ追加手順についての正典であった。内容は現在 `04_mcp_03` にある。
- サーバ別の `04_mcp-*.md` ファイルはサーバ固有仕様についての正典である。内容は現在 `04_mcp_04` にある。
- 旧ファイルと新ファイルの内容が食い違う場合は、新しく再構成されたファイルを信頼すること。

---

## File Index

| ファイル | 説明 |
|---|---|
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | エントリポイント |
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | システム概要 |
| [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | プロトコルとトランスポート |
| [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) | ルーティングとライフサイクル |
| [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) | サーバカタログ |
| [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) | セキュリティモデル |
| [04_mcp_06_01_purpose.md](04_mcp_06_01_purpose.md) | config目的 |
| [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) | config一覧 |
| [04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md](04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md) | McpServerConfigフィールド |
| [04_mcp_06_04_major-default-values.md](04_mcp_06_04_major-default-values.md) | デフォルト値 |
| [04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md](04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md) | 長時間実行される操作 |
| [04_mcp_06_06_verification-methods.md](04_mcp_06_06_verification-methods.md) | 検証方法 |
| [04_mcp_06_07_reading-audit-logs.md](04_mcp_06_07_reading-audit-logs.md) | audit log |
| [04_mcp_06_08_end-to-end-tool-call-tracing.md](04_mcp_06_08_end-to-end-tool-call-tracing.md) | トレーシング |
| [04_mcp_06_09_mcp-failure-diagnosis.md](04_mcp_06_09_mcp-failure-diagnosis.md) | 障害診断 |
| [04_mcp_06_10_settings-with-high-operational-impact.md](04_mcp_06_10_settings-with-high-operational-impact.md) | 運用上重要な設定 |
| [04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md) | 起動時検証 |
| [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md) | watchdog設定 |
| [04_mcp_06_13_watchdog-health-reasons-scheduling.md](04_mcp_06_13_watchdog-health-reasons-scheduling.md) | watchdogヘルス |
| [04_mcp_06_14_new-tool-registration-procedure.md](04_mcp_06_14_new-tool-registration-procedure.md) | 新規tool登録 |
| [04_mcp_06_15_new-mcp-server-addition-checklist.md](04_mcp_06_15_new-mcp-server-addition-checklist.md) | 新規サーバ追加チェックリスト |
| [04_mcp_06_16_pre-production-fail-open-checklist.md](04_mcp_06_16_pre-production-fail-open-checklist.md) | 本番投入前チェックリスト |
| [04_mcp_06_17_local-to-production-auth-migration.md](04_mcp_06_17_local-to-production-auth-migration.md) | 認証移行 |
| [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) | スキーマエクスポート |
| ~~04_mcp_07_mdq_rag_boundary.md~~ | 削除済み |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | 既知の問題 |

---

## Migration Notes

### POST /v1/search（削除済み — 2026-06-26）

`rag-pipeline-mcp` の `POST /v1/search` エンドポイントは削除された。

**変更前:**
```http
POST /v1/search
{"query": "...", "history_context": "..."}
```

**変更後（正典となるMCP tool call）:**
```http
POST /v1/call_tool
{"name": "rag_run_pipeline", "args": {"query": "...", "history_context": []}}
```

`rag_service_url` を呼び出している箇所は、MCP tool callの形式に更新すること。
この変更は後方互換ではない — 互換シムは提供されない。

---

## Legacy Source Document Policy

**方針: 削除。** Git履歴に全内容が保存されているため、アーカイブは不要。

旧MCPソースファイル（`04_spec_mcp.md`、`04_mcp-*.md`、`06_ref-mcp.md`）は
ドキュメント再構成フェーズ（plan 71-76）の間は保持されていたが、2026-06-26付で削除された。
復元が必要な場合は `git log --all -- docs/<filename>` を使用すること。

---

## Known Limitations

- `04_spec_mcp.md` §13の既知の問題はすべて `04_mcp_90` に転記済み。

## Related Documents

- `04_mcp_01_system_overview.md`
- `04_mcp_02_protocol_and_transport.md`
- `04_mcp_03_routing_lifecycle_and_execution.md`
- `04_mcp_04_server_catalog.md`
- `04_mcp_05_security_and_safety_model.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_07_tool_schema_export_policy.md`
- `04_mcp_90_inconsistencies_and_known_issues.md`

## Keywords

mcp
documentation
guide
routing
file-index
