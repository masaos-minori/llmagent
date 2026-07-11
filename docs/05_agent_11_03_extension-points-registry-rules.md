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
  - 05_agent_11_02_extension-points-tool-registration.md
source:
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## レジストリ API（`shared/plugin_registry.py`）

| Function | Description |
|---|---|
| `get_command(name)` | `(handler, is_prefix) \| None` |
| `iter_commands()` | 登録済みのすべてのコマンドの辞書スナップショット |
| `get_tool(name)` | `Callable \| None` |
| `get_pipeline_post_stages()` | すべての post-rerank ステージハンドラのリストスナップショット |
| `load_plugins(plugin_dir, *, known_tools, override_policy, strict_mode)` | ディレクトリ内のすべての `*.py` をインポートする。loaded/failed/conflict のカウントを含む `PluginLoadResult` を返す。strict モードでは `PluginLoadError` を発生させる |

### テストの分離

テスト専用の関数が、グローバルなレジストリ状態をクリアする**唯一**の方法である。

ルール:
- `load_plugins()` または任意の `@register_*` デコレータを呼び出すテストは、
  各テスト関数の前（および任意で後）に `pytest.fixture(autouse=True)` の中で
  この関数を呼び出さなければならない。
- 本番コード（テスト以外のモジュール）はこの関数を**絶対に**呼び出してはならない。
- テストにおけるレジストリ内部の直接変更も禁止されている。
  代わりにこの関数とパブリックなデコレータを使用すること。

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
4. `config/tools_definitions.toml` にツール定義を追加する
5. アプリ設定と `[mcp_servers.<key>]` トランスポートセクションを持つ `config/<key>_mcp_server.toml` を作成する
6. `deploy/deploy.sh` のコピーリストに新しいファイルを追加する
7. `deploy/setup_services.sh` に起動ステップを追加する

MCP サーバー追加の完全な手順は
[04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) を参照。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_01_extension-points-plugin-command.md`
- `05_agent_11_02_extension-points-tool-registration.md`

## Keywords

Registry API
test isolation
extension rules
hook failure behavior
adding a new MCP server
