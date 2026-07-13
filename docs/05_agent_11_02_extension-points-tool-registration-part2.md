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

本番モードでは、登録されるすべてのツールは `tool_safety_tiers` に安全ティアのエントリを宣言していなければならない。ティアが欠落している場合、`ProductionConfigValidator.validate()` が本番プロファイルでエラーを返し、呼び出し元が起動時にそれを致命的エラーとして扱う。これにより、リスク分類が定義されていないツールは動作できないことが保証される。未知のティアキー（登録済みのツール名に一致しないキー）も本番環境で致命的なエラーを発生させる。

> **実装補足（Explicit in code）:** `ProductionConfigValidator.validate()` 自体は例外を送出せず、`ConfigValidationResult(errors, warnings)` を返すだけである。エラーをどう扱うかは呼び出し元次第で、実装上2経路が存在し挙動が異なる。
> - `agent/repl_health.py` の起動時ヘルスチェック経路（`tool_safety_tiers` を含む）: 本番モードで `errors` が非空の場合、各メッセージを **`RuntimeError`** として送出する。
> - `agent/config_builders.py` の config ロード経路（`plugin_strict` を含む全 `_REQUIRED_STRICT_KEYS`）: 本番プロファイルで `errors` が非空の場合、`RuntimeError` ではなくログ出力後に **`sys.exit(1)`** でプロセスを終了する。
>
> どちらの経路も `local`/開発プロファイルでは同じ条件を警告（warning）としてログ出力するのみで、起動は継続する。（根拠分類: Explicit in code — `scripts/shared/production_config_validator.py`, `scripts/agent/repl_health.py:855-873`, `scripts/agent/config_builders.py:284-299`）

**CI 自動検出:** config に `plugin_strict` が存在せず、`CI` 環境変数が設定されている場合（GitHub Actions、CircleCI など）、`plugin_strict` は自動的に `True` にデフォルト設定される。config で明示的に `plugin_strict = false` とした場合は常にこれを上書きする。（根拠: `agent/config_builders.py` の `plugin_strict=bool(cfg.get("plugin_strict", os.getenv("CI") is not None))`）

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

#### プラグインツール実行時の契約検証（`shared/plugin_tool_invoker.py`）

`ToolExecutor.execute()` は内部で `PluginToolInvoker.try_execute()` に処理を委譲する。プラグイン関数が登録されていない場合は `None` を返し、`ToolExecutor` は MCP ルーティングにフォールバックする。

- ハンドラが例外を送出した場合、例外はプラグイン外に伝播せず `ToolCallResult(is_error=True, error_type="tool")` に変換される（メッセージは `[plugin error] <tool_name>: <exc>`）。
- 戻り値が `tuple[str, bool]` でない場合（要素数不一致、`output` が `str` でない、`is_error` が `bool` でない）も同様に捕捉され、`error_type="plugin_contract"` の `ToolCallResult(is_error=True)` に変換される（メッセージは `[plugin contract violation] <tool_name>: <detail>`）。`@register_tool` の登録時アノテーション検査に加えて、実行のたびにこの実行時検証が行われる。
- いずれの場合も `request_id=""`, `server_key=""`, `source="plugin"` が設定される。

（根拠分類: Explicit in code — `scripts/shared/plugin_tool_invoker.py`, `scripts/shared/tool_executor.py`）

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
ProductionConfigValidator
PluginToolInvoker
plugin_contract violation
sys.exit(1) vs RuntimeError
