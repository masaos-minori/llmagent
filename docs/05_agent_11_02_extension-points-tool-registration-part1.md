---
title: "Agent Extension Points - Tool Registration (Part 1)"
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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_01_extension-points-plugin-command.md`
- `05_agent_11_03_extension-points-registry-rules.md`
- `05_agent_11_02_extension-points-tool-registration-part2.md`

## Keywords

@register_tool
plugin tool precedence
conflict detection
safety tier enforcement
@register_pipeline_stage
