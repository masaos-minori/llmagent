---
title: "Agent Extension Points - Plugin Architecture and Commands"
category: agent
tags:
  - agent
  - extension-points
  - plugin-architecture
  - register-command
related:
  - 05_agent_00_document-guide.md
  - 05_agent_11_02_extension-points-tool-registration.md
  - 05_agent_11_03_extension-points-registry-rules.md
source:
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## 目的

プラグインアーキテクチャ、すべての `@register_*` デコレータ、拡張ルール、
および組み込み機能と拡張機能の間の優先関係を文書化する。

---

## プラグインアーキテクチャ

プラグインは `plugins/*.py` にある Python ファイルである（プロジェクトルート、つまり `scripts/` の2階層上を基準とする）。

**ロード:**
1. プラグインレジストリの初期化時に、起動時に `plugin_registry.load_plugins(plugin_dir)` が呼び出される
2. 各 `*.py` ファイルはアルファベット順にインポートされる
3. `@register_*` デコレータはインポート時に実行され、ハンドラをグローバルに登録する
4. ロード中のエラーは `[plugin] skipped: <filename> (<ErrorType>)` として個別にログ出力される
5. config で `plugin_strict=true` の場合、すべてのプラグインが試行され、最後に集約された詳細を含む単一の `PluginLoadError` が発生する
6. ロード後、サマリー行がログ出力される: `[plugin] loaded=N, skipped=M`
7. ロード後、プラグインのツール名およびコマンド名が組み込み名と照合され、競合はそれぞれソースモジュール名とともにログ出力される
8. ディレクトリが見つからない場合 → 0個のプラグインがロードされる（エラーなし）

起動時ログ形式（個別スキップ）:
`[plugin] skipped: <filename> (<ErrorType>)`

起動時ログ形式（競合）:
`[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — rejected|allowed`

起動時ログ形式（コマンドシャドウ）:
`[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`

```python
# plugins/my_plugin.py
from shared.plugin_registry import register_command, register_tool, register_pipeline_stage

@register_command("/ping")
async def cmd_ping(ctx, args: str) -> None:
    print("pong")

@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:
    return str(args.get("text", "")), False

@register_pipeline_stage(when="post")
def post_rerank(hits, query):
    return hits   # modify and return hits list
```

---

## `@register_command`

```python
@register_command(name: str, *, prefix: bool = False)
handler(ctx: AgentContext, args: str) -> None  # sync or async
```

- `name`: `/` を含むスラッシュコマンド文字列（例: `"/ping"`）
- `prefix=False`: 完全一致のみ
- `prefix=True`: 後続の引数を受け付ける（`line.startswith(name + " ")`）
- ディスパッチ優先度: 組み込みコマンドより**低い**（2番目にチェックされる）
- アクセス: `plugin_registry.get_command(name)` → `(handler, is_prefix) | None`

**組み込みとプラグインの優先度:**
組み込みコマンドが最初にマッチングされる。組み込みにマッチしない場合、プラグインコマンドが試行される。組み込みコマンドと同名の
プラグインコマンドは**ロード時に拒否される**（プラグインコマンドレジストリから削除される）。
これらは `iter_commands()` に現れず、ディスパッチもされない。これは
起動時の強制であり、ディスパッチ時の優先度ではない。

#### コマンドシャドウポリシー

組み込みコマンドと同名のプラグインコマンドは、**オプションA（拒否）**ポリシーの対象となる。

- ロード時に、シャドウしているコマンドはコマンドレジストリから**削除**され、`iter_commands()` に現れず、ディスパッチもされない。
- ログ: `[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`
- `plugin_strict = true` の場合、すべてのプラグインのロード後に、`"Command builtin conflicts rejected: /help, /debug"`（拒否されたコマンド名のカンマ区切りリスト）を含むメッセージとともに `PluginLoadError` が発生する。
- 非strictモード（デフォルト）では、拒否はログ行を出す以外は無音であり、起動は通常通り継続する。
- `/plugin status` は `"Command shadows (rejected)"` のもとでこの件数を報告する。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_02_extension-points-tool-registration.md`
- `05_agent_11_03_extension-points-registry-rules.md`

## Keywords

plugin architecture
@register_command
command shadow policy
