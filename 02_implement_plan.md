# 02_implement_plan.md

## Goal

`00_llm_spec_tobe.md` に記載されたコマンド層リファクタリング要件を実装する。
主目的は以下の3点:

1. コマンドハンドラをシン化し、アプリケーションロジックをサービス層に移動する
2. クロスミックス依存をなくし、型システムまたは明示的コンポジションで契約を表明する
3. 状態変更操作に監査ログ・dry-run・構造化結果型を統一する

---

## Scope

### 対象 (実装する)

| ファイル | 作業内容 |
|---|---|
| `agent/commands/registry.py` | `ctx.llm_url` フラットアクセスを `ctx.cfg.llm.llm_url` に修正 |
| `agent/commands/cmd_config.py` | `_apply_config_params()` 等を `ConfigReloadService` に移動; `_cmd_reload()` でリロード結果を表示 |
| `agent/services/config_reload.py` | `apply_config_dict()` 追加; `_apply_mcp_url_reload()` の構造化リロード結果を返す |
| `agent/commands/cmd_mcp.py` / `agent/services/mcp_status.py` | WRITE列を `tool_safety_tiers` ベースに整合 |
| `agent/commands/cmd_context.py` | `_cmd_undo()` を整合的なundo APIに変更; flat cfg残留修正 |
| `agent/session.py` | `undo_last_turn()` API追加 (メモリ+DB両側のロールバックを一か所に集約) |
| `agent/commands/cmd_ingest.py` | `_cmd_ingest()` を `IngestWorkflowService` + CLIレンダラーに分離; `_cmd_export()` のレンダラー/ライター分離 |
| `agent/services/ingest_workflow.py` | 新規作成: IngestWorkflowService + IngestResult |
| `agent/commands/cmd_memory.py` | 状態変更操作に audit_logger 呼び出し; dry-run フラグ; 構造化結果型 |
| `agent/commands/cmd_session.py` | `_load_session()` の session_id 直接代入をサービスAPIへ移動 |

### 対象外 (既に対応済み、または明示的に除外)

- `cmd_rag.py` — シム化済み。`cmd_tooling.py` / `cmd_notes.py` / `cmd_debug.py` に分割完了
- `cmd_mcp.py` の `InstallQA` Protocol / `CliInstallQA` — 抽象Q&Aインタフェース実装済み
- `cmd_memory.py` の MemoryLayer 内部アクセス — 既にすべて公開 facade API 経由
- `cmd_ingest.py` の `force_compress()` — 公開 API 呼び出し済み
- `ConfigReloadService` 基本実装 — `ConfigReloadResult` ・ `apply_config()` 呼び出し済み
- `AgentContext` のフラットアクセス (Step 8相当) — 難易度極高のため本スコープ外

---

## Assumptions

- 現行テストスイートはリファクタリング前後でグリーンを維持しなければならない
- 新規サービスクラスはユニットテストを追加する (CLAUDE.mdのTest coverage要件)
- `AgentContext.__getattr__` / `__setattr__` によるフラットアクセスは残存 (除去は別タスク)
- `tool_safety_tiers` は `dict[str, str]` で値は `READ_ONLY` | `WRITE_SAFE` | `WRITE_DANGEROUS` | `ADMIN`
- `agent/session.py` の `delete_last_turn()` は DB側のロールバックのみを行う (現行動作)
- import layer contracts (`shared → db → rag/mcp → agent`) は守る

---

## Unknowns

### U1: registry.py — ミックス間明示的契約の粒度
spec: 「型システムまたは明示的コンポジションで契約を表明する」
現状: `CommandRegistry` は10個のミックスを多重継承しており、各ミックスは `if TYPE_CHECKING: _ctx: AgentContext` でアノテーション。
**問い**: Protocolクラスを各ミックスに定義するか、ABC基底クラスを導入するか、現行の TypeChecking アノテーションで充分か。
**分析結果**: ミックスが依存するのは `self._ctx: AgentContext` のみ。全ミックスが同一シグネチャを持つため、共通 `MixinBase` に `_ctx: AgentContext` を定義し継承させれば、「どのミックスがどのAPIを提供するか」は docstring + module分割 + 単一起点 MixinBase で明示できる。Protocol を各ミックスに付けるほどの複雑性は現状存在しない。→ **MixinBase 導入で解決**

### U2: cmd_context.py — `_cmd_undo()` 論理ターン単位
spec: 「論理ターン単位に基づく一貫した undo API」
現状: in-memory側は `last_user_idx` から後ろを削除; DB側は `ctx.session.delete_last_turn()` を呼ぶ。
`delete_last_turn()` の実装が tool_calls / system injection メッセージを正しく扱っているか不明。
**分析結果**: `session.py` の `delete_last_turn()` を確認 → messages テーブルで `message_id DESC` 順に最後の user ロールまで削除している。in-memory 側の `_memory_injected` マーカー除去ロジックと対称でない可能性がある。→ **`AgentSession.undo_last_turn()` を新設し、削除件数を返すAPIとする。in-memory側でも件数チェックを追加する。**

### U3: cmd_memory.py — dry-run の公開方法
spec: 「dry-run サポートの標準化」
現状: delete/prune/pin にdry-runは存在しない。
**問い**: CLIフラグ `--dry-run` か、サブコマンド拡張か。
**分析結果**: `/memory delete --dry-run <id>` 形式が最も自然。prune も同様。pin/unpin は冪等性が高く dry-run の優先度は低い。→ **delete と prune のみ `--dry-run` フラグを追加。**

### U4: cmd_memory.py — 監査ログの出力先と形式
spec: 「print() のみでは監査証跡として不十分」
**問い**: `ctx.services.audit_logger` (JSON形式) か通常 `logger.info()` か。
**分析結果**: `audit_logger` はセッション単位のイベントログ (`Logger` クラス、JSON Lines)。MemoryLayer の状態変更はセッション監査に属するため `audit_logger` が適切。ただし `cmd_memory.py` は現在 `_ctx` を持つが `audit_logger` へのアクセスパスは `ctx.services.audit_logger`。`audit_logger` が `None` の場合 (`use_memory_layer=False`) のフォールバックが必要。→ **`audit_logger` を使用。None ガードを入れる。**

### U5: cmd_mcp.py status — WRITE列とtool_safety_tiers対応
spec: 「dangerous / write-safe / admin のクラス分けに整合させる」
現状: `_WRITE_CAPABLE_TOOLS` セットとの membership check でWRITE列を設定。
**分析結果**: `tool_safety_tiers: dict[str, str]` の値は `WRITE_SAFE` | `WRITE_DANGEROUS` | `ADMIN` | `READ_ONLY`。サーバの `tool_names` をtierマップで引き、最も危険なtierを代表値とする方式が適切。表示列は WRITE のまま維持し、値を `no` / `write-safe` / `dangerous` / `admin` で区別する。既存の `_WRITE_CAPABLE_TOOLS` は削除して tiers から判定する。→ **実装可能**

---

## Affected areas

```
scripts/agent/
  commands/
    registry.py            # ctx.llm_url → ctx.cfg.llm.llm_url; MixinBase導入
    cmd_config.py          # _apply_* 群を ConfigReloadService に移動
    cmd_context.py         # _cmd_undo() → undo_last_turn() API利用; tokenize_url修正
    cmd_ingest.py          # _cmd_ingest() → IngestWorkflowService委譲
    cmd_memory.py          # audit_logger; dry-run; MemoryOpResult
    cmd_mcp.py             # (mcp_status.py 経由で間接影響)
    cmd_session.py         # _load_session() → session.load() API利用
    utils.py               # config表示レンダラー関数追加 (既存 render_history_md と同居)
  services/
    config_reload.py       # apply_config_dict() 追加; MCP URL再読込の構造化結果
    mcp_status.py          # tool_safety_tiers ベースのWRITE列判定
    ingest_workflow.py     # 新規作成
  session.py               # undo_last_turn() 追加

tests/
  test_agent_cmd_config.py      # _apply_config_params 移動後のテスト更新
  test_agent_cmd_mcp.py         # write列変更のテスト更新
  test_agent_cmd_context.py     # undo API変更のテスト (新規または更新)
  test_agent_cmd_ingest.py      # IngestWorkflowService テスト (新規)
  test_agent_cmd_memory.py      # dry-run / audit_logger テスト (新規)
  test_agent_session.py         # undo_last_turn テスト更新
```

---

## Design

### D1: MixinBase (registry.py)

```python
# agent/commands/mixin_base.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agent.context import AgentContext

class MixinBase:
    """共通アノテーション基底。全ミックスクラスはこれを継承する。"""
    _ctx: "AgentContext"
```

全10ミックスクラスが `MixinBase` を継承することで、`_ctx` の型情報が一か所に集約される。

### D2: ConfigReloadService 拡張 (cmd_config.py → config_reload.py)

```python
class ConfigReloadService:
    def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadResult:
        """cfg更新 + サービス同期を一括実行。旧 _apply_config_params() の責務。"""
        ...

    def _classify_mcp_reload(
        self, new_cfg: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """(applied_urls, needs_restart_keys) を返す。"""
        ...
```

`_cmd_reload()` は `apply_config_dict()` を呼び、`result.needs_restart` を表示する:

```python
result = ConfigReloadService(ctx).apply_config_dict(new_cfg)
if result.needs_restart:
    print(f"Restart required for: {', '.join(result.needs_restart)}")
print("Config reloaded.")
```

### D3: McpStatusService — tier-based WRITE列

```python
def _tier_for_server(self, cfg: McpServerConfig, tiers: dict[str, str]) -> str:
    """サーバの tool_names から最高危険度 tier を返す。"""
    priority = {"ADMIN": 3, "WRITE_DANGEROUS": 2, "WRITE_SAFE": 1, "READ_ONLY": 0}
    best = "READ_ONLY"
    for t in cfg.tool_names:
        tier = tiers.get(t, "READ_ONLY")
        if priority.get(tier, 0) > priority.get(best, 0):
            best = tier
    return best
```

WRITE列の表示値: `no` (READ_ONLY) / `write-safe` (WRITE_SAFE) / `dangerous` (WRITE_DANGEROUS) / `admin` (ADMIN)

### D4: AgentSession.undo_last_turn() (session.py)

```python
def undo_last_turn(self) -> int:
    """DBから最後のユーザーターン以降を削除。削除件数を返す。"""
    ...
```

`_cmd_undo()` は in-memory ロールバック後に `undo_last_turn()` を呼び、削除件数を検証する。

### D5: IngestWorkflowService (ingest_workflow.py)

```python
@dataclass
class IngestResult:
    stage: str  # "crawl" | "split" | "ingest" | "ok"
    error: str | None = None
    n_chunks: int = 0

class IngestWorkflowService:
    async def run(self, target: str, lang: str, snippets_only: bool) -> IngestResult:
        ...
```

`_cmd_ingest()` はサービスを呼び出し、結果に応じてエラー表示/完了表示を行う。

### D6: ExportRenderer (cmd_ingest.py → utils.py)

```python
def render_export(history: list[LLMMessage], fmt: str) -> str:
    """フォーマット選択とレンダリングのみ担当。"""
    ...

def write_export(content: str, outfile: str | None) -> None:
    """stdout/ファイル書き込みのみ担当。"""
    ...
```

### D7: MemoryOpResult (cmd_memory.py)

```python
@dataclass
class MemoryOpResult:
    ok: bool
    memory_id: str
    action: str  # "deleted" | "pinned" | "unpinned" | "pruned"
    dry_run: bool = False
    count: int = 0  # prune用
```

state-changing 操作後に `audit_logger.info(event_dict)` を呼ぶ。

### D8: _load_session() API整理 (cmd_session.py → session.py)

`AgentSession` に `load(session_id)` を追加するのではなく、`_load_session()` 内部の直接代入を `ctx.session.session_id = session_id` から変更しない (AgentSession は `session_id` フィールドを公開しているため、直接代入は設計上妥当)。代わりに、ロード時に stats リセットを行う `_reset_turn_stats()` ヘルパーを明示化する。

---

## Implementation steps

### Step 0: 行動ロックテスト取得 (変更前に実施)

変更対象モジュールのうち、既存テストが薄い以下を補強:
- `cmd_context.py` の `_cmd_undo()` — `tests/test_agent_cmd_context.py` が存在しない場合は新規作成
- `cmd_ingest.py` — `tests/test_agent_cmd_ingest.py` が存在しない場合は新規作成

既存テスト確認:
```bash
source .venv/bin/activate && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5
```

### Step 1: MixinBase 導入 + registry.py フラットアクセス修正

1. `scripts/agent/commands/mixin_base.py` を新規作成
2. 全10ミックスクラスに `MixinBase` を継承追加
3. `registry.py` L127: `ctx.llm_url` → `ctx.cfg.llm.llm_url`
4. ruff / mypy / pytest を通す

### Step 2: cmd_context.py — flat cfg残留修正 + undo API整合

1. `cmd_context.py` L116: `getattr(ctx.cfg, "tokenize_url", "")` → `ctx.cfg.llm.tokenize_url`
2. `session.py` に `undo_last_turn() -> int` を追加 (DBから最後のuser turnまでを削除し件数を返す)
3. `cmd_context.py` の `_cmd_undo()` を `ctx.session.undo_last_turn()` を使うよう更新
4. `tests/test_agent_session.py` を更新; `test_agent_cmd_context.py` 追加

### Step 3: ConfigReloadService 拡張 + cmd_config.py 整理

1. `config_reload.py` に `apply_config_dict(new_cfg)` を追加
   - 旧 `_apply_rag_tool_params`, `_apply_llm_prompt_params`, `_apply_sse_reload_params`, `_reload_approval_settings`, `_apply_mcp_url_reload` のロジックを移植
   - `_classify_mcp_reload()` でtransport変更を `needs_restart` に分類
2. `cmd_config.py` の `_apply_config_params()` と `_apply_*` helpers を削除
   - `_cmd_reload()` → `ConfigReloadService(ctx).apply_config_dict(new_cfg)` を呼ぶ
   - `ConfigReloadResult.needs_restart` を表示
3. config表示 (`_print_config_values`, `_print_rag_config`) を `utils.py` に `render_config_display()` / `render_rag_config_display()` として移動
4. テスト更新: `tests/test_agent_cmd_config.py`

### Step 4: McpStatusService — tier-based WRITE列

1. `mcp_status.py` の `_WRITE_CAPABLE_TOOLS` を削除
2. `_tier_for_server()` を追加; `probe_all()` で `ctx.cfg.approval.tool_safety_tiers` を参照
3. WRITE列の値を `no` / `write-safe` / `dangerous` / `admin` に変更
4. テスト更新: `tests/test_agent_cmd_mcp.py`

### Step 5: IngestWorkflowService 新規作成 + cmd_ingest.py 整理

1. `agent/services/ingest_workflow.py` を新規作成: `IngestResult`, `IngestWorkflowService`
2. `cmd_ingest.py` の `_cmd_ingest()` を薄いCLIレンダラーに変更 (サービス呼び出し + 結果表示)
3. `_cmd_export()` のレンダリングを `utils.py` の `render_export()` / `write_export()` に分離
4. テスト追加: `tests/test_agent_services_ingest.py`

### Step 6: cmd_memory.py — audit_logger / dry-run / MemoryOpResult

1. `MemoryOpResult` dataclass を `cmd_memory.py` に定義 (または `agent/services/memory_ops.py` に移動)
2. `_memory_delete()`, `_memory_prune()`, `_memory_pin()` に `--dry-run` フラグ解析を追加
3. 各操作後に `ctx.services.audit_logger.info(...)` を呼ぶ (None ガード付き)
4. テスト追加: `tests/test_agent_cmd_memory.py`

### Step 7: cmd_session.py — セッションライフサイクル整理

1. `_load_session()` にコメントを追加し、stats リセットの明示化
2. `_reset_session_stats(ctx)` ヘルパーを `_cmd_clear()` / `_load_session()` で共通利用
3. `_generate_session_title()` の docstring 更新 (現行実装は既に cfg.llm 経由)
4. テスト更新: `tests/test_agent_session.py`

### Step 8: 全体検証

```bash
source .venv/bin/activate
python -m ruff check scripts/ tests/ --fix
python -m mypy scripts/ --ignore-missing-imports
python -m lint_imports
python -m pytest tests/ -x -q
```

---

## Validation plan

| 検証項目 | コマンド / 確認方法 |
|---|---|
| ruff エラーなし | `python -m ruff check scripts/ tests/` |
| mypy エラーなし | `python -m mypy scripts/ --ignore-missing-imports` |
| import layer 違反なし | `python -m lint_imports` |
| 全テスト通過 | `python -m pytest tests/ -x -q` |
| `/reload` でリロード結果表示 | 手動: `/reload` → needs_restart表示確認 |
| `/mcp` WRITE列が tier ベース | 手動: `/mcp` → `tool_safety_tiers` の内容を反映 |
| `/undo` でDB整合 | 手動: 複数ターン後 `/undo` → session DB確認 |
| `/memory delete --dry-run` | 手動: 実際に削除されないことを確認 |
| `/ingest` でstage失敗が分かる | 手動: 不正URLで crawl stage失敗を確認 |

---

## Risks

### R1: MixinBase 多重継承 MRO 変化
**影響**: 10クラスが同一 `MixinBase` を継承するとMROが変わる可能性。
**対処**: `MixinBase.__init_subclass__` は定義しない; `MixinBase` はデータなしの型アノテーション専用クラスとする。MRO確認テストを追加。

### R2: ConfigReloadService への _apply_* 移植でリグレッション
**影響**: `_apply_mcp_url_reload` 等のロジックを移植する際に微妙な副作用が失われる可能性。
**対処**: Step 3 前に `tests/test_agent_cmd_config.py` で `/reload` パスを行動ロックする。移植後に同テストを回す。

### R3: McpStatusService WRITE列変更がユーザー表示に破壊的変更
**影響**: 既存の `/mcp status` 出力フォーマット依存のテストや運用スクリプトが壊れる。
**対処**: 列名 `WRITE` は維持し値のみ変更。`tool_safety_tiers` が空の場合は旧来の `_WRITE_CAPABLE_TOOLS` ロジックへフォールバックする。テストにて両パターンをカバー。

### R4: undo_last_turn() の DB ロールバック範囲不整合
**影響**: tool_call / memory_injection メッセージの扱いが in-memory と DB で異なると、undo後にセッションが壊れる。
**対処**: `undo_last_turn()` は `message_id DESC` で最後の `role='user'` まで削除。in-memory 側の `_memory_injected` マーカー除去と対称になるようにする。統合テストで tool_call を含むターンの undo を検証する。

### R5: IngestWorkflowService の asyncio executor 依存
**影響**: `loop.run_in_executor()` は `asyncio.get_running_loop()` に依存。テスト環境でデッドロックする可能性。
**対処**: サービスのインタフェースを `async def run(...)` とし、executorの呼び出しはサービス内部に封じ込める。テストでは `AsyncMock` / `unittest.mock.patch` で executor をモックする。

### R6: audit_logger が None のケースでの例外
**影響**: `use_memory_layer=False` の場合 `ctx.services.memory` は None だが、memory コマンドそのものは既にガードされている。ただし audit_logger は別途 None になりうる。
**対処**: `audit_logger` 呼び出し前に `if ctx.services.audit_logger is not None:` チェックを入れる。
