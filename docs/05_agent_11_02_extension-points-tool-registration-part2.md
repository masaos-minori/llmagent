---
title: "Agent Extension Points - Tool Registration (Part 2)"
category: agent
tags:
  - agent
  - extension-points
  - register-tool
  - pipeline-stage
related:
  - 05_agent_00_document-guide.md
  - 05_agent_11_01_extension-points-plugin-command.md
  - 05_agent_11_03_extension-points-registry-rules.md
source:
  - 05_agent_11_02_extension-points-tool-registration-part1.md
---

# Agent Extension Points

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

#### 安全ティアの強制

本番モードでは、登録されるすべてのツールは `tool_safety_tiers` に安全ティアのエントリを宣言していなければならない。ティアが欠落している場合、`ProductionConfigValidator.validate()` により起動時に致命的な `RuntimeError` が発生する。これにより、リスク分類が定義されていないツールは動作できないことが保証される。未知のティアキー（登録済みのツール名に一致しないキー）も本番環境で致命的なエラーを発生させる。

**CI 自動検出:** config に `plugin_strict` が存在せず、`CI` 環境変数が設定されている場合（GitHub Actions、CircleCI など）、`plugin_strict` は自動的に `True` にデフォルト設定される。config で明示的に `plugin_strict = false` とした場合は常にこれを上書きする。

デフォルトは `false`（フェイルオープン）であり、失敗は `[plugin] skipped: <filename> (<ErrorType>)` としてログ出力され、ロードは継続する。

`PluginLoadResult.failed` の各失敗エントリ: `PluginFailure(path="<filename>", error="Plugin load failed (<filename>): <ErrorType>: <message>")`

`PluginLoadResult` のフィールド: `loaded_count`、`failed`、`tool_conflicts_shadowed`、`tool_conflicts_allowed`、`command_shadows_rejected`

最新の `PluginLoadResult` は `plugin_registry.get_last_load_result()` からアクセス可能であり、`/plugin status` によって表示される。

#### 優先順位

1. プラグインツール（`ToolExecutor.execute()` で最初にチェックされる）
2. MCP ツール（`ToolRouteResolver` を介してルーティングされる）
3. 組み込みコマンド（スラッシュコマンド。ツール呼び出しではない）

混乱を避けるため、既存の MCP ツール名と重複しない名前をプラグインツールに付けること。

**MCP との優先度比較:** プラグインツールが先にチェックされる。MCP ツールと同名の
プラグインツールは、そのセッション内のすべての呼び出しにおいて MCP ツールをシャドウする（競合検出によって拒否されない限り）。

#### オブザーバビリティの制限

プラグインツールは `source="plugin"` および空の `mcp_request_id` を持つ `tool_exec` オーディットイベントを `audit_tool_exec()` 経由で発行する。しかし、MCP ツールイベントとは異なり、プラグインのオーディットイベントには以下が欠けている。

- **`X-Request-Id` なし**: プラグインツールは HTTP トランスポート層を経由しないため、サーバー側のログと関連付けるための `request_id` が存在しない。
- **`server_key` なし**: `server_key` フィールドはプラグインツールでは常に空である。

つまり、プラグインツールのオーディットイベントは MCP サーバーのアクセスログと関連付けることができない。詳細は [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md#plugin-tool-audit-events) を参照。

---

## `@register_pipeline_stage`

```python
@register_pipeline_stage(when: str = "post")
handler(hits: list[dict], query: str) -> list[dict]
```

- `when="post"`: フックはクロスエンコーダーによる rerank ステージの後に実行される
- rerank 済みの hits リストと元のクエリ文字列を受け取る
- （変更されている可能性のある）hits リストを返さなければならない
- 登録済みのすべての post-rerank ステージは登録順に実行される
- アクセス: `plugin_registry.get_pipeline_post_stages()` → `list[Callable]`

**現時点の制限:** `when="post"`（post-rerank）のみがサポートされる。pre-search
および pre-rerank のフックは未実装である。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_01_extension-points-plugin-command.md`
- `05_agent_11_03_extension-points-registry-rules.md`
- `05_agent_11_02_extension-points-tool-registration-part1.md`

## Keywords

@register_tool
plugin tool precedence
conflict detection
safety tier enforcement
@register_pipeline_stage
