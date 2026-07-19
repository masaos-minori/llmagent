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
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_07_tool_schema_export_policy.md
  - 04_mcp_08_tool_capability_naming_convention.md
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
| どのMCPサーバが存在し、何をするのか。ポート・起動モードは | `04_mcp_01` |
| `/v1/call_tool`・Bearer認証・audit logフォーマットは | `04_mcp_02` |
| toolのルーティング、ToolExecutor、新規サーバ追加は | `04_mcp_03`(config defaultsは`04_mcp_06`§Major Default Values) |
| ツールのenabled/disabled_reason、config_dependent、RuntimeToolRegistryの扱いは | `04_mcp_03_06` |
| web-search/github/shell/mdq各mcpが提供するtoolは。mdq-mcpのFTS5検索は本番稼働可能、ハイブリッド検索は未実装 | `04_mcp_04`(mdq-mcpはFTS5検索のみ実装済み) |
| allowed_dirs/allowed_repos、fail-closed/fail-open、dry_run、リスクティア、MDQ/RAG境界は | `04_mcp_05` |
| configファイル一覧、健全性検証、デフォルト値、起動時警告、障害診断は | `04_mcp_06` |
| tool schemaモジュールの命名、TOOL_LISTエクスポート、_MCP_TOOLS参照のクリーンアップは | `04_mcp_07` |
| toolのcapability命名規則(domain.action形式)は | `04_mcp_08` |
| 何が壊れているか、または未実装なのか | `04_mcp_90` |
---

## Navigation to Major Known Issues

| 課題 | 場所 |
|---|---|
| mdq-mcpは本番稼働可能（FTS5検索とインデックスが実装済み） | [04_mcp_04_04_mdq.md](04_mcp_04_04_mdq.md) |

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
| [04_mcp_02_01](04_mcp_02_01_endpoints-and-transport.md) 〜 [_02](04_mcp_02_02_startup-modes-and-health.md)/[_03](04_mcp_02_03_audit-logging-and-errors.md) | プロトコルとトランスポート(3分割) |
| [04_mcp_03_01](04_mcp_03_01_dispatch-and-routing.md) 〜 [_02](04_mcp_03_02_tool-registry.md)/[_03a](04_mcp_03_03_transport-and-health-part1.md)/[_03b](04_mcp_03_03_transport-and-health-part2.md)/[_04](04_mcp_03_04_tool-call-tracing-and-watchdog.md)/[_05](04_mcp_03_05_lifecycle-and-new-server.md)/[_06](04_mcp_03_06_tool-runtime-availability-metadata.md) | ルーティングとライフサイクル(7分割) |
| [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md) 〜 [_02](04_mcp_04_02_file-write-file-delete-shell.md)/[_03](04_mcp_04_03_rag-pipeline-and-cicd.md)/[_04](04_mcp_04_04_mdq.md)/[_05](04_mcp_04_05_git.md)/[_06](04_mcp_04_06_browser.md) | サーバカタログ(6分割、_04=mdq) |
| [04_mcp_05_01](04_mcp_05_01_access-control-and-allowlists.md) 〜 [_02](04_mcp_05_02_auth-profiles-and-sandboxing.md)/[_03](04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)/[_04](04_mcp_05_04_mdq-rag-boundary.md)/[_05](04_mcp_05_05_mdq-enforcement-and-lockdown.md) | セキュリティモデル(5分割) |
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
| [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md) | watchdog削除note(2026-07-16) |
| [04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md](04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md) | health_reason / HealthRegistry |
| [04_mcp_06_14_new-tool-registration-procedure.md](04_mcp_06_14_new-tool-registration-procedure.md) | 新規tool登録 |
| [04_mcp_06_15_new-mcp-server-addition-checklist.md](04_mcp_06_15_new-mcp-server-addition-checklist.md) | 新規サーバ追加チェックリスト |
| [04_mcp_06_16_pre-production-fail-open-checklist.md](04_mcp_06_16_pre-production-fail-open-checklist.md) | 本番投入前チェックリスト |
| [04_mcp_06_17_local-to-production-auth-migration.md](04_mcp_06_17_local-to-production-auth-migration.md) | 認証移行 |
| [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) | スキーマエクスポート |
| [04_mcp_08_tool_capability_naming_convention.md](04_mcp_08_tool_capability_naming_convention.md) | capability命名規則 |
| ~~04_mcp_07_mdq_rag_boundary.md~~ | 削除済み |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | 既知の問題 |

---

## Migration Notes

### POST /v1/search（削除済み — 2026-06-26）

`rag-pipeline-mcp` の `POST /v1/search` エンドポイントは削除された。`rag_service_url` を呼び出している箇所は、正典であるMCP tool call `POST /v1/call_tool {"name": "rag_run_pipeline", "args": {"query": "...", "history_context": []}}` の形式に更新すること。この変更は後方互換ではない — 互換シムは提供されない。

### Gateway形式ツール名と実際のツール名の対応（命名明確化）

初期の「MCP統合プラグインシステム」提案（Gateway形式の関数名）と現在の実際のツール名の対応:
`list_files` → `list_directory`、`read_file` → `read_text_file`、`search_file` →
`search_files`、`invoke_script` → `shell_run`。今後の提案でツール名を参照する際は、Gateway形式
ではなく実際のツール名を使用すること。

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
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_07_tool_schema_export_policy.md`
- `04_mcp_08_tool_capability_naming_convention.md`
- `04_mcp_90_inconsistencies_and_known_issues.md`

## Keywords

mcp
documentation
guide
routing
file-index
