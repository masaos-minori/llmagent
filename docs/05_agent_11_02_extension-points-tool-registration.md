---
title: "Agent Extension Points - Tool Registration"
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
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## `@register_tool`

```python
@register_tool(name: str, *, known_tools: frozenset[str] = frozenset(), override_policy: str = "reject")
async handler(args: dict) -> tuple[str, bool]   # (result_text, is_error)
```

- ローカルの Python 関数をツールハンドラとして登録する
- MCP ルーティングを完全にバイパスする
- キャッシュチェックと MCP ディスパッチの**前**に `ToolExecutor.execute()` から呼び出される
- 戻り値: `(result_text: str, is_error: bool)`

**戻り値型の検証（fail-fast）:** 登録時に `@register_tool` は
関数の戻り値アノテーションを検査する。アノテーションが欠落している、または `tuple[str, bool]` でない場合、
即座に `ValueError` が発生する。この場合ツールは登録**されない**。デプロイ前に
アノテーションを修正すること。

```python
# Contract: must annotate return type as tuple[str, bool]
@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:   # required
    return str(args.get("text", "")), False
```

**なぜ警告ではなく fail-fast にするのか。** 静かな警告は本番環境で見逃され、
呼び出し時に予期しない動作を引き起こしていた。登録時に失敗させることで、エラーを見逃せなくする。

**実行時の戻り値検証:** `ToolExecutor.execute()` は呼び出し時に実際の戻り値を検証する。戻り値が**ちょうど2要素**の `tuple` であること（`len == 2`）、`result[0]` が `str` であること、`result[1]` が `bool` であることを確認する。要素数が2以外の tuple は `ValueError` を発生させる。最初の要素が `str` でない場合は `TypeError` を発生させる。2番目の要素が `bool` でない場合は `TypeError` を発生させる。

- アクセス: `plugin_registry.get_tool(name)` → `Callable | None`

### プラグインツールの優先度と競合ポリシー

プラグインツールは `plugins/` ディレクトリにあるプラグインファイル内の
`@register_tool()` デコレータを介して登録される。プラグインツールが
MCP ツールと同名の場合、結果は `plugin_tool_override` に依存する。

- **`plugin_tool_override = false`（デフォルト）:** 競合するプラグインツールは
  起動時に拒否され、レジストリから削除される。
- **`plugin_tool_override = true`:** プラグインツールがそのセッションにおいて MCP
  ツールより優先される（`ToolExecutor.execute()` でプラグインツールが最初にチェックされる）。

#### 競合検出

`plugin_tool_override = false`（デフォルト）の場合。

- 起動時に、既知のすべての MCP ツール名が `ToolRegistry` から収集される。
- プラグインツール名が既知の MCP ツールのいずれかと一致する場合、そのツールは**拒否される**（レジストリから削除される）。
- ログ: `[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — rejected`
- 競合したツールのみが削除され、プラグインモジュールおよびその他のツールのロードは継続する。

`plugin_tool_override = true` の場合。

- 競合は許容され、ログ出力される: `[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — allowed`
- プラグインツールがそのセッションにおいて MCP ツールより優先される。

#### 設定

`config/agent.toml` に設定する。

```toml
plugin_tool_override = false  # or true to allow shadowing
plugin_strict = false         # or true to fail startup on first plugin import error
```

#### 厳格プラグインロードモード

`plugin_strict = true` の場合、まずすべてのプラグインファイルが試行される。ロードループ全体の完了後、失敗が発生していれば、失敗の詳細をすべて集約したメッセージを持つ単一の `PluginLoadError`（`RuntimeError` のサブクラス）が発生する。

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

## Keywords

@register_tool
plugin tool precedence
conflict detection
safety tier enforcement
@register_pipeline_stage
