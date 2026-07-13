---
title: "Agent Extension Points - Registry API and Rules"
category: agent
tags:
  - agent
  - extension-points
  - plugin-registry
  - extension-rules
  - mcp-server
related:
  - 05_agent_00_document-guide.md
  - 05_agent_11_01_extension-points-plugin-command.md
  - 05_agent_11_02_extension-points-tool-registration-part1.md
source:
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

## レジストリ API（`shared/plugin_registry.py`）

| Function | Description |
|---|---|
| `get_command(name)` | `(handler, is_prefix) \| None` |
| `iter_commands()` | 登録済みのすべてのコマンドの辞書スナップショット |
| `get_tool(name)` | `Callable \| None` |
| `get_pipeline_post_stages()` | すべての post-rerank ステージハンドラのリストスナップショット |
| `load_plugins(plugin_dir, *, known_tools, override_policy, strict_mode)` | ディレクトリ内のすべての `*.py` をインポートする。loaded/failed/conflict のカウントを含む `PluginLoadResult` を返す。strict モードでは `PluginLoadError` を発生させる |

> **実装補足（Explicit in code）:** `shared/plugin_registry.py` はデコレータとパブリック API の窓口であり、`load_plugins()` / `get_last_load_result()` / `_reset_for_testing()` は実体を `shared/plugin_auto_discover.py` に委譲する薄いラッパーである。関連する内部実装は以下のモジュールに分割されている。
> - `shared/plugin_auto_discover.py` — `*.py` ファイルの走査・`importlib` によるインポート、`_last_load_result` の保持
> - `shared/plugin_conflicts.py` — `validate_tool_conflicts()` / `validate_command_conflicts()`（MCP ツール名・組み込みコマンド名との競合検出）
> - `shared/plugin_result.py` — `PluginFailure` / `PluginLoadResult` / `PluginLoadError` のデータ型定義
> - `shared/plugin_tool_invoker.py` — `PluginToolInvoker`（プラグインツールの実行と例外変換。詳細は [05_agent_11_02](05_agent_11_02_extension-points-tool-registration-part2.md#プラグインツール実行時の契約検証shared-plugin_tool_invokerpy) 参照）
> - `shared/plugin_registries.py` — レジストリの生データ（`_commands` / `_tools` / `_pipeline_post` など）を保持するモジュールレベルの状態

**`load_plugins()` の strict モード挙動（Explicit in code）:** ディレクトリ内の全 `*.py` を最後まで読み込んでから（1件目の失敗で中断しない）、失敗・競合をすべて集約して単一の `PluginLoadError` を送出する。エラーメッセージは以下を `; ` 区切りで連結する。
- `Plugin load failed (N error(s)): <detail>`（読み込み失敗があれば）
- `Tool MCP conflicts rejected: <names>`（`override_policy="reject"` で拒否されたツール名があれば）
- `Command builtin conflicts rejected: <names>`（組み込みコマンドと衝突し拒否されたコマンド名があれば）

**`override_policy` パラメータ（Explicit in code）:** プラグインツール名が `known_tools`（登録済み MCP ツール名の集合）と衝突した場合の扱いを制御する。
- `"reject"`（デフォルト）: 衝突したプラグインツールをレジストリから削除する（`tool_conflicts_shadowed` をインクリメント）
- `"allow"`: 衝突を許容し、プラグインツールが MCP ツールをシャドウしたまま残す（`tool_conflicts_allowed` をインクリメント）

### テストの分離

テスト専用の関数が、グローバルなレジストリ状態をクリアする**唯一**の方法である。

ルール:
- `load_plugins()` または任意の `@register_*` デコレータを呼び出すテストは、
  各テスト関数の前（および任意で後）に `pytest.fixture(autouse=True)` の中で
  この関数を呼び出さなければならない。
- 本番コード（テスト以外のモジュール）はこの関数を**絶対に**呼び出してはならない。
- テストにおけるレジストリ内部の直接変更も禁止されている。
  代わりにこの関数とパブリックなデコレータを使用すること。

**クリア対象（Explicit in code）:** `_reset_for_testing()` は `_commands` / `_tools` / `_pipeline_post` を空にし、`_builtin_command_names` を空の `frozenset` に戻し、`_current_loading_module` を空文字列にリセットし、`_last_load_result` を `None` に戻す。`/plugin status` はこの状態では「Plugin registry not initialized」を表示する。

例。
```python
import pytest
import shared.plugin_registry as plugin_registry

@pytest.fixture(autouse=True)
def reset_registry():
    # Clear all registries (test-only function)
    yield
    # Clear all registries again after test
```

---

## 拡張ルール

1. プラグインツールは `ToolExecutor` によってキャッシュされない（MCP ツールの結果のみがキャッシュされる）
2. 組み込みコマンドと同名のプラグインコマンドは
   ロード時に**拒否され**、レジストリから削除される。strict モードでは `PluginLoadError` が発生する。
3. インポート中に例外を発生させるプラグインファイルは無音でスキップされる。デプロイ前には必ずプラグインをテストすること
4. `@register_pipeline_stage` フックは RAG パイプラインのコンテキスト内で実行される。例外は `run_pipeline_stages()` によって捕捉されログ出力される。パイプラインは hits を変更しないまま継続する
5. プラグインツールのハンドラは `async` 関数でなければならない。コマンドハンドラは同期・非同期のどちらでも構わない

#### フック失敗時の動作

通常モード（デフォルト）では、post-rerank フックが発生させた例外は以下のように扱われる。
- `shared/plugin_registry.py` の `run_pipeline_stages()` によって捕捉される
- フック名、エラータイプ、クエリのコンテキストとともに警告としてログ出力される
- スキップされる: パイプラインはそのフック実行前の hits のまま継続する

strict モード（`RagPipeline.run()` の `hook_strict=True`）では、最初のフック失敗が
元の例外を呼び出し元に発生させる。フックの動作を検証するテストではこのモードを使用すること。

ログ形式: `Plugin hook "<name>" failed on query "<query>": <ErrorType>: <message>`

---

## 新しい MCP サーバーの追加

1. `scripts/mcp_servers/<name>/server.py` で `MCPServer` をサブクラス化し、`dispatch()` をオーバーライドする
2. `server_key` フィールドを含むツール定義を返す `GET /v1/tools` エンドポイントを追加する
3. `shared/tool_constants.py` の frozenset にツール名を追加する（このサーバーが所有するもの）
4. `config/agent.toml` の `[[tool_definitions]]` にツール定義を追加する
5. サーバーアプリ設定を含む `config/<key>_mcp_server.toml` を作成し、`config/agent.toml` に `[mcp_servers.<key>]` トランスポートセクションを追加する
6. `deploy/deploy.sh` のコピーリストに新しいファイルを追加する
7. `deploy/setup_services.sh` に起動ステップを追加する

MCP サーバー追加の完全な手順は
[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_01_extension-points-plugin-command.md`
- `05_agent_11_02_extension-points-tool-registration-part1.md`

## Keywords

Registry API
test isolation
extension rules
hook failure behavior
adding a new MCP server
plugin_auto_discover
plugin_conflicts
override_policy
PluginLoadError aggregation
