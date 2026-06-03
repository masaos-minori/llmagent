# 02_implement_plan.md

## Goal

`agent/commands/` 配下の後方互換レイヤー・レガシーミックスイン間の暗黙依存を完全に除去する。
アプリケーションロジックをサービスクラスへ、フォーマット処理をレンダラーへ移動し、
明示的な公開 API・型付き戻り値モデルを確立する。

---

## Scope

### 対象

| ファイル | 変更種別 |
|---|---|
| `agent/commands/cmd_config.py` | `ConfigReloadService` 抽出、private 属性直書き廃止 |
| `agent/commands/cmd_context.py` | DB 管理コマンドを `cmd_db.py` へ分離、`_cmd_system` / `_cmd_undo` 修正 |
| `agent/commands/cmd_ingest.py` | クロスミックスイン依存 (`_render_history_md`) 廃止、IngestWorkflowService 抽出 |
| `agent/commands/cmd_mcp.py` | `McpStatusService` / `McpInstallService` / Q&A 抽象インタフェース分離 |
| `agent/commands/cmd_memory.py` | `MemoryLayer` private 属性アクセス廃止、公開 API 経由に統一 |
| `agent/commands/cmd_rag.py` | `cmd_tooling.py` + `cmd_debug.py` + `cmd_notes.py` へ分割 |
| `agent/commands/cmd_session.py` | タイトル生成定数をコンフィグ/専用サービスへ移動 |
| `agent/memory/layer.py` | 公開 API (`list_entries` / `get_entry` / `pin_entry` / `delete_entry` / `prune`) 追加 |
| `shared/llm_client.py` | `apply_config()` 公開セッター追加 |
| `agent/history.py` | `apply_config()` + `force_compress()` 公開 API 追加 |
| `shared/tool_executor.py` | `apply_config()` 公開セッター追加 |
| 新規: `agent/services/config_reload.py` | `ConfigReloadService` クラス |
| 新規: `agent/commands/cmd_db.py` | DB 管理コマンド (`/db` 系) |
| 新規: `agent/commands/cmd_tooling.py` | ツール結果検査・プランモード (`cmd_rag.py` から改名) |
| 新規: `agent/commands/cmd_debug.py` | デバッグ操作コマンド |
| 新規: `agent/commands/cmd_notes.py` | ノート管理コマンド |

### 対象外

- LLM 通信層 (`shared/llm_client.py` の通信ロジック)
- MCP トランスポート層
- RAG パイプライン
- テスト以外の MCP サーバ群

---

## Assumptions

1. `AgentConfig` は現状どおりデータクラスとして維持する (`ctx.cfg.*` アクセスパターンは変更しない)
2. `AgentContext.history` は引き続き `list[LLMMessage]` として維持する
3. 新規サービスクラスは `agent/services/` ディレクトリ配下に配置する
4. REPL の外部インタフェース (スラッシュコマンド名・引数仕様) は変更しない
5. テストカバレッジは変更前後で同等以上を維持する (behavior-lock テストを先に取得する)
6. `startup_mode="subprocess"` (HTTP サーバ) を持つ MCP サーバの設定変更には引き続き再起動が必要

---

## Unknowns

### U-1: system prompt の history 分離が圧縮ロジックに与える影響 [解決済み]

**調査結果**: `HistoryManager._select_turns_to_compress()` は以下のロジックを持つ。

```python
system_msgs = [m for m in history if m["role"] == "system"]
turn_msgs   = [m for m in history if m["role"] != "system"]
# ... 圧縮後 ...
return system_msgs + [summary_msg] + remaining
```

全 `role="system"` メッセージ (本物の system prompt・メモリ注入・圧縮サマリ) を一括して
先頭に戻す設計。このため、本物の system prompt を `ctx.history` から取り除いて
`ctx.system_prompt_content` に分離しても `compress()` 本体は無変更で動作する。

**設計決定**: `ctx.history` には system prompt を含めない。
`Orchestrator._run_turn()` で LLM に送るメッセージリストを構築する際に
`ctx.system_prompt_content` を先頭に挿入する (history への常駐廃止)。
この変更は Phase D にて実施。

### U-2: `/undo` のターン境界定義 [解決済み]

**調査結果**: `Orchestrator._handle_memory_injection()` は以下を実行する。

```python
ctx.history.append({"role": "system", "content": memory_block})  # memory injection
```

これは `ctx.history.append({"role": "user", ...})` の直前に行われる。
結果として 1 ターンの history 構造は:

```
[...前ターンまで...]
{"role": "system", "content": "[Relevant memories]\n..."}  ← メモリ注入 (optional)
{"role": "user",   "content": "..."}
{"role": "assistant", "content": "..." | tool_calls: [...]}
{"role": "tool",   "content": "..."}  ← 0 個以上
```

現行の `_cmd_undo()` は `last_user_idx` から末尾を削除するため、
直前のメモリ注入 `role="system"` メッセージが残留する (バグ)。

**設計決定**: メモリ注入メッセージに `"_memory_injected": True` マーカーを付与し
(Phase D の memory injection 修正と同時実施)、
`_cmd_undo()` は `last_user_idx` から 1 つ前の `_memory_injected` メッセージまで
さかのぼって削除する。Phase I にて実施。

### U-3: `/mcp install` の非対話モードの仕様 [解決済み]

**決定**: CLI フラグ方式を採用する。

```
/mcp install <name>                          # 従来の対話ウィザード
/mcp install <name> --port 8015 --role git   # 非対話モード (全フラグ指定時)
/mcp install <name> --port 8015              # 部分フラグ (未指定項目はウィザードで補完)
```

`CliInstallQA` は引数で渡された値があればそれを返し、なければ `input()` で問い合わせる実装とする。
これにより対話・非対話の境界がフラグの有無で自然に制御される。

### U-4: `/mcp status` の tool safety tier モデルとの整合 [解決済み]

**調査結果**: `agent/tool_policy.py` の実際の tier 名:

```python
_TIER_TO_RISK = {
    "READ_ONLY":       "none",
    "WRITE_SAFE":      "none",
    "WRITE_DANGEROUS": "medium",
    "ADMIN":           "high",
}
```

仕様書の分類との対応:

| 仕様書 | 実装 tier | 説明 |
|---|---|---|
| read-only | `READ_ONLY` | 承認不要 |
| write-safe | `WRITE_SAFE` | 承認不要 (ただし dry-run 推奨) |
| dangerous | `WRITE_DANGEROUS` | medium リスク (承認プロンプト) |
| admin | `ADMIN` | high リスク (承認必須) |

**設計決定**: `/mcp status` の write 判定を現行の `cfg.tool_names ∩ WRITE_TOOLS` から
`tool_safety_tiers` ベースの判定 (`WRITE_DANGEROUS` / `ADMIN` 含む) に変更する。
`McpStatusService.probe_all()` が各サーバのツール名を `tool_safety_tiers` と照合して
tier サマリを返す設計とする。Phase H にて実施。

### U-5: `_render_history_md()` の移動先 [解決済み]

**調査結果**: 参照箇所は 2 箇所のみ。
- 定義: `cmd_rag.py:198` (`_ToolingMixin` のメソッド)
- 参照: `cmd_ingest.py:50` (`self._render_history_md()` + `# type: ignore[attr-defined]` コメント)

テストファイルからは参照なし。

**設計決定**: `agent/commands/utils.py` に `render_history_md(history) -> str` として移動する。
`cmd_tooling.py` と `cmd_ingest.py` の両方が `from agent.commands.utils import render_history_md`
で import する。ミックスインのメソッドとしての提供を廃止し、クロスミックスイン依存を解消する。

---

## Affected areas

| エリア | 影響 |
|---|---|
| `agent/commands/registry.py` | ミックスイン名変更 (`_ToolingMixin` → `_ToolingMixin` + `_DebugMixin` + `_NotesMixin`)、インポート変更 |
| `agent/history.py` | `force_compress()` / `apply_config()` 追加 |
| `shared/llm_client.py` | `apply_config()` 追加 |
| `shared/tool_executor.py` | `apply_config()` 追加 |
| `agent/memory/layer.py` | 公開 API 5 件追加 |
| `agent/memory/store.py` | `layer.py` から公開 API 経由で呼ばれるようになる (インタフェースは変更なし) |
| `agent/memory/jsonl_store.py` | `prune()` API から呼ばれる (変更なし) |
| `tests/test_cmd_config.py` | `_sync_services_to_cfg` → `ConfigReloadService` に追従 |
| `tests/test_memory_layer.py` | 新 public API テスト追加 |
| `tests/test_cmd_memory.py` (新規) | `_MemoryMixin` の public API 経由動作のテスト |
| `docs/06_ref-agent-commands.md` | ミックスイン表・メソッド一覧更新 |
| `docs/06_ref-agent-context.md` | system prompt 専用フィールド追記 (U-1 解決後) |

---

## Design

### D-1: サービス公開セッター (Phase A)

各サービスに `apply_config()` メソッドを追加し、コマンド層からの private 属性直書きを廃止する。

```python
# shared/llm_client.py
def apply_config(
    self, *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    max_retries: int | None = None,
    retry_base_delay: float | None = None,
    sse_heartbeat_timeout: float | None = None,
    sse_malformed_retry: int | None = None,
    sse_reconnect_max: int | None = None,
    stream_retry_on_heartbeat_timeout: bool | None = None,
    stream_retry_on_malformed_chunk: bool | None = None,
) -> None: ...

# agent/history.py
def apply_config(
    self, *,
    char_limit: int | None = None,
    compress_turns: int | None = None,
    token_limit: int | None = None,
    tokenize_url: str | None = None,
) -> None: ...

async def force_compress(self, history: list[LLMMessage]) -> list[LLMMessage]: ...

# shared/tool_executor.py
def apply_config(self, *, cache_ttl: float | None = None) -> None: ...
```

### D-2: ConfigReloadService (Phase C)

```python
# agent/services/config_reload.py
class ConfigReloadService:
    def __init__(self, ctx: AgentContext) -> None: ...
    def apply(self, new_cfg: dict[str, Any]) -> ConfigReloadResult: ...

@dataclass
class ConfigReloadResult:
    applied: list[str]       # 即時反映された設定キー
    needs_restart: list[str] # 再起動必要な設定キー
    skipped: list[str]       # 適用できなかった設定キー
```

`cmd_config.py` の `_apply_config_params()` とその 6 サブメソッドを `ConfigReloadService.apply()` に移管。
`/reload` コマンドは `ConfigReloadService` を呼び出し、`ConfigReloadResult` を表示するだけにする。

### D-3: MemoryLayer 公開 API (Phase B)

```python
# agent/memory/layer.py (追加分)
def list_entries(
    self, mem_type: str = "", limit: int = 10
) -> list[MemoryEntry]: ...

def get_entry(self, memory_id: str) -> MemoryEntry | None: ...
def pin_entry(self, memory_id: str) -> bool: ...
def unpin_entry(self, memory_id: str) -> bool: ...
def delete_entry(self, memory_id: str) -> bool: ...
def prune(self, days: int) -> int: ...  # JSONL + SQLite を一括削除し削除件数を返す
```

### D-4: system prompt 専用フィールド (Phase D)

U-1 の調査結果に基づき実施。方針:
- `AgentContext` に `system_prompt_content: str` フィールドを追加
- `Orchestrator._append_user_message()` ターン前に history[0] を `system_prompt_content` から再構築
- `_cmd_system()` は `ctx.system_prompt_content` を更新するのみ (history 直書き廃止)
- memory injection は引き続き別 system ロールとして追記 (混在は許容)

### D-5: cmd_rag.py → 3 ファイル分割 (Phase G)

| 新ファイル | 内容 |
|---|---|
| `cmd_tooling.py` | `_ToolingMixin`: `/tool list`, `/tool show`, `/plan` |
| `cmd_notes.py` | `_NotesMixin`: `/note add/list/delete` |
| `cmd_debug.py` | `_DebugMixin`: `/debug audit/verbose/normal/toggle` |

`_render_history_md()` は `agent/commands/utils.py` に移動し、`cmd_ingest.py` も直接 import する。

### D-6: cmd_mcp.py 分割 (Phase H)

```
cmd_mcp.py
  ├── McpStatusService (agent/services/mcp_status.py)
  │     probe_all() → list[McpServerStatus]
  │     format_table() → str
  └── McpInstallService (agent/services/mcp_install.py)
        build_scaffold(answers: InstallAnswers) → ScaffoldResult
        print_next_steps(result: ScaffoldResult) → None

InstallAnswers (dataclass):
  port: int
  role: str        # "generic" | "sqlite" | "shell" | "git" | "ci"
  with_confd: bool

class InstallQA(Protocol):
    def ask_port(self) -> int: ...
    def ask_role(self) -> str: ...
    def ask_confd(self) -> bool: ...

class CliInstallQA(InstallQA):
    # 初期化時に CLI フラグ値 (port/role/with_confd) を受け取る。
    # 指定済みの場合はそれを返し、None の場合は input() で問い合わせる。
    def __init__(self, port: int | None, role: str | None, with_confd: bool | None): ...
```

### D-7: /undo 改善 (Phase I)

U-2 の調査結果に基づき実施。方針:
- `ctx.session.delete_last_turn()` が DB 上の turn_id 単位で削除していることを確認
- history 側は `last_user_idx` から末尾まで削除 (現行維持)
- memory 注入メッセージ (`role="system"`, content がメモリ注入ブロック) を識別するマーカーを導入し、undo 時にも除去対象に含める

---

## Implementation steps

各フェーズは順番に実施する。フェーズ内のステップは並列可。
各フェーズ開始前に behavior-lock テストを取得すること (`python-test-and-fix` スキル参照)。

### Phase A: サービス公開 API 追加 (前提フェーズ)

1. `agent/history.py` に `apply_config()` + `force_compress()` 追加、テスト追加
2. `shared/llm_client.py` に `apply_config()` 追加、テスト追加
3. `shared/tool_executor.py` に `apply_config()` 追加、テスト追加

### Phase B: MemoryLayer 公開 API

4. `agent/memory/layer.py` に `list_entries()` / `get_entry()` / `pin_entry()` / `unpin_entry()` / `delete_entry()` / `prune()` 追加
5. `agent/commands/cmd_memory.py` を公開 API 経由に書き換え、`_memory_prune` の `SQLiteHelper` 直呼び廃止
6. テスト追加

### Phase C: ConfigReloadService 抽出

7. `agent/services/` ディレクトリ作成
8. `agent/services/config_reload.py` に `ConfigReloadService` / `ConfigReloadResult` 実装
9. `cmd_config.py` の `_apply_config_params()` + 6 サブメソッドを `ConfigReloadService` に委譲
10. `_sync_services_to_cfg()` を `apply_config()` 経由に書き換え (private 属性廃止)
11. テスト更新

### Phase D: system prompt 専用フィールド (U-1 解決後)

12. `AgentContext` に `system_prompt_content: str` 追加
13. `Orchestrator` のターン開始時に `history[0]` を `system_prompt_content` から再構築
14. `_cmd_system()` を `ctx.system_prompt_content` 更新に変更
15. `session_load` (セッション復元) での system prompt 復元も専用フィールド経由に変更
16. テスト追加

### Phase E: force_compress + _cmd_compact 修正

17. `_cmd_compact()` の `_char_limit` 直書きを `hist_mgr.force_compress()` に置き換え

### Phase F: cross-mixin 依存除去

18. `agent/commands/utils.py` 作成、`_render_history_md()` を移動
19. `cmd_ingest.py` の暗黙 `_render_history_md` 参照を `from agent.commands.utils import render_history_md` に変更

### Phase G: cmd_rag.py → 3 ファイル分割

20. `cmd_tooling.py` / `cmd_notes.py` / `cmd_debug.py` 作成
21. `registry.py` のインポートと `CommandRegistry` の MRO を更新
22. `cmd_rag.py` 削除
23. テスト・ドキュメント更新

### Phase H: cmd_mcp.py 分割

24. `agent/services/mcp_status.py` 実装
25. `agent/services/mcp_install.py` + `InstallQA` Protocol 実装
26. `cmd_mcp.py` を薄いディスパッチャに書き換え

### Phase I: cmd_context.py 分割 + /undo 改善

27. `agent/commands/cmd_db.py` 作成、`/db` 系メソッドを移動
28. `_cmd_undo()` を U-2 解決後の論理ターン単位で修正
29. `registry.py` 更新

### Phase J: cmd_session.py タイトル生成設定化

30. `AgentConfig` に `title_llm_temperature: float = 0.1` / `title_llm_max_tokens: int = 20` 追加
31. `_generate_session_title()` をコンフィグ参照に変更
32. `config/agent.toml` に設定項目追記

---

## Validation plan

各フェーズ完了時に以下を実施する。

```bash
ruff check scripts/ tests/
mypy scripts/ --ignore-missing-imports
python -m pytest tests/ -x -q
lint-imports  # import layer contract 確認
```

フェーズ別重点確認:

| フェーズ | 重点テスト |
|---|---|
| A | `test_llm_client.py` / `test_history.py` / `agent/test_tool_executor.py` |
| B | `test_memory_layer.py` / 新 `test_cmd_memory.py` |
| C | `test_cmd_config.py` (全メソッド) |
| D | `test_orchestrator.py` / セッション復元シナリオ |
| G | `test_cmd_rag.py` → `test_cmd_tooling.py` に移行 |
| H | `test_cmd_mcp.py` |
| I | `test_cmd_context.py` / undo シナリオ (tool メッセージ混在) |

---

## Risks

### R-1: system prompt 分離による圧縮・セッション復元の回帰 [中 (U-1 解決で低減)]

U-1 の調査で `compress()` は `role="system"` を一括分離・再付与する設計と確認済み。
`ctx.history` から system prompt を除外しても圧縮ロジック本体への影響はない。
残るリスクは `_load_session()` でのセッション復元時に `history[0]` として system prompt を
挿入している箇所と、`/export` での history 出力に system prompt が含まれなくなる点。

**対処**:
- `_load_session()` は `ctx.system_prompt_content` を復元するのみとし、history への直接挿入を廃止
- `/export` コマンドは `ctx.system_prompt_content` を先頭に付与してエクスポートする
- Phase D 実施前に `_load_session()` の全参照を洗い出し、behavior-lock テストを取得する

### R-2: MRO の変化による `CommandRegistry` 動作変化 [中]

ミックスイン数が増加 (現在 7 → 最大 10) することで Python の MRO (Method Resolution Order) が変化し、
同名メソッドの解決順が変わる可能性がある。

**対処**: Phase G・I 後に `registry.py` の MRO を明示的に `__init_subclass__` または
`type(CommandRegistry).__mro__` で確認し、意図しないオーバーライドが発生していないことをテストで保証する。

### R-3: `apply_config()` でのスレッドセーフ性 [中]

`ToolExecutor._cache_ttl` への書き込みは現在ロックなし。`apply_config()` 導入後も
キャッシュアクセスと TTL 更新が競合する可能性がある (asyncio シングルスレッドなので通常は問題なし)。

**対処**: asyncio イベントループ内での呼び出しであることをコメントで明記し、
threading を使う場合は `asyncio.Lock` でガードするよう注記する。

### R-4: `cmd_rag.py` 改名によるインポート参照漏れ [低]

`registry.py` 以外に `cmd_rag.py` を import しているファイルが存在した場合に実行時エラー。

**対処**: Phase G 前に `grep -r "cmd_rag" scripts/ tests/` で全参照を洗い出してから実施する。

### R-5: `MemoryLayer.prune()` の JSONL / SQLite 整合性 [低 → 解決済み]

**調査結果**: `JsonlMemoryStore` が公開するのは `append()` / `read_all()` のみ。
削除 API は存在しない。JSONL は append-only の source of truth であり物理削除は行わない設計。

**設計決定**: `MemoryLayer.prune(days)` は SQLite (`memories` テーブル + `memories_fts`) のみ削除する。
JSONL のエントリは残留するが、SQLite から除外されるため実行時には参照されない。
これは既存の `_memory_prune()` が `SQLiteHelper` 経由でのみ削除している現行動作と同じ意味論。
リスクは低い。
