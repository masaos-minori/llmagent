# 02_implement_plan.md

spec: `00_llm_spec_tobe.md`

---

## Goal

`00_llm_spec_tobe.md` に基づく2項目の spec 変更を実装する。

1. **Agent REPL changes** — `/chat` / `/code` 削除、プロンプト変更、`chat_url`/`code_url` 削除、in-process RAG のパイプライン除去
2. **Shell execution policy** — 実行ポリシー明確化、リソース制限、専用 MCP への分離、監査ログ

---

## Scope

### In-scope (未実施)

| 番号 | 項目 | 主な対象ファイル |
|---|---|---|
| S-1 | two-stage fetch を orchestrator から除去 | `scripts/agent/orchestrator.py` |
| S-2 | RagPipeline 初期化を factory から除去 | `scripts/agent/factory.py` |
| S-3 | `ServiceContainer.rag` フィールド削除 | `scripts/agent/context.py` |
| S-4 | `AgentConfig` から RAG 関連フィールド全削除 | `scripts/agent/config.py` |
| S-5 | `/rag` コマンド全削除 | `scripts/agent/commands/cmd_rag.py`, `registry.py` |
| S-6 | startup banner の `use_search` 参照削除 | `scripts/agent/repl.py` |
| S-7 | config hot-reload の RAG フィールド削除 | `scripts/agent/commands/cmd_config.py` |
| S-8 | `config/agent.toml` から RAG 関連キー削除 | `config/agent.toml` |
| S-9 | テスト更新 | `tests/test_cmd_rag.py`, `test_orchestrator.py`, `test_agent_rag.py` |

### Out-of-scope (既実装済み)

| 項目 | 確認箇所 |
|---|---|
| `/chat` / `/code` コマンド除去 | `repl.py:58–78` — SLASH_COMMANDS に存在しない |
| プロンプト `>` への変更 | `repl.py:88` — `return "> "` |
| `chat_url`/`code_url` 削除・`llm_url` 統合 | `config/agent.toml:2` — `llm_url` のみ存在 |
| auto-RAG injection 除去 | `orchestrator.py` handle_turn() に RAG 挿入なし |
| `shared/protocols/shell.py` (ShellPolicy) | 実装済み |
| `mcp/shell/service.py` (setrlimit, firejail, kill policy, 監査ログ) | 実装済み |
| `config/shell_mcp_server.toml` | 実装済み |

### Not-in-scope (変更しない)

- `scripts/rag/` モジュール全体 — `mcp/rag_pipeline/service.py` が `RagPipeline` を使用するため存続
- `scripts/mcp/rag_pipeline/` — rag-pipeline-mcp サービスは in-process ではなく別プロセス MCP のため除去対象外

---

## Assumptions

1. "Remove in-process RAG from the REPL pipeline flow" の除去対象は:
   - `handle_turn()` 内の two-stage fetch パス
   - `/rag` コマンド (手動 `/rag search` を含む)
   - `factory.py` での `RagPipeline` インスタンス化
   - `AgentConfig` の RAG 設定フィールド
2. `scripts/rag/` モジュール自体は `mcp/rag_pipeline/service.py` が依存するため削除しない。
3. `_budget_breakdown()` の `'rag'` キー (`cmd_context.py`) は、コンテキスト計測ユーティリティとして RAG 不使用時も `rag=0` を表示するだけで問題ないため変更しない。

---

## Unknowns

全 Unknown は分析・ユーザー確認により解決済み。

| ID | 内容 | 解決方法 |
|---|---|---|
| U-1 | two-stage fetch は pipeline flow に含まれるか | `_finalize_answer()` 内から呼ばれ自動実行される → 含まれる |
| U-2 | 手動 `/rag search` を残すか | ユーザー確認: 削除する |
| U-3 | `bd['rag']` 参照 | `_budget_breakdown()` ユーティリティは変更不要 (rag=0になるだけ) |
| U-4 | `rag/` モジュールを削除するか | `mcp/rag_pipeline/service.py` が依存するため削除しない |

---

## Affected areas

```
scripts/agent/orchestrator.py
  ├── import: from rag.repository import fetch_full_document  → 削除
  ├── _fetch_two_stage_context()   → 削除
  ├── _maybe_two_stage_fetch()     → 削除
  ├── _finalize_answer()           → two_stage_done 引数・分岐 削除、戻り値 str | None に変更
  └── handle_turn()                → two_stage_done 変数 削除

scripts/agent/factory.py
  ├── import: from rag.pipeline import RagPipeline  → 削除
  ├── _init_rag_pipeline()         → 関数ごと削除
  └── build_agent_context()        → _init_rag_pipeline() 呼び出し 削除

scripts/agent/context.py
  └── ServiceContainer.rag: RagPipeline | None  → フィールド削除
  └── import: from rag.pipeline import RagPipeline (TYPE_CHECKING)  → 削除

scripts/agent/config.py
  ├── AgentConfig フィールド削除:
  │   rag_top_k, use_mqe, use_search, use_rrf, use_rerank, rag_min_score,
  │   rag_service_url, use_rag_mcp, use_two_stage_fetch, two_stage_max_docs
  ├── __post_init__(): _validate_rag_params() 呼び出し + rag バリデーション 削除
  ├── _validate_rag_params()       → メソッドごと削除
  └── _from_toml()                 → RAG フィールドの読み込み行 削除

scripts/agent/repl.py
  ├── SLASH_COMMANDS               → "/rag" 削除
  ├── docstring                    → RagPipeline 記述 削除
  └── _print_startup_banner()      → use_search 分岐を削除 (chunk_count 表示は DB 直参照のため維持 or 削除)

scripts/agent/commands/cmd_rag.py
  ├── import: from rag.types import ... → 削除
  └── _RagMixin から削除:
      _cmd_rag_search(), _print_rag_results(), _cmd_rag_toggle(), _cmd_rag()

scripts/agent/commands/registry.py
  ├── help text: /rag 関連行 削除
  └── dispatch: ("/rag", self._cmd_rag, True) 削除

scripts/agent/commands/cmd_config.py
  ├── _cmd_config_show() → rag_top_k / use_mqe / use_search / use_rrf / use_rerank 表示行 削除
  └── _apply_config_params() → rag フィールドの hot-reload 行 削除

config/agent.toml
  削除キー: use_search, use_mqe, use_rrf, use_rerank, rag_top_k, rag_min_score,
            rag_service_url, use_rag_mcp, use_two_stage_fetch, two_stage_max_docs

tests/test_cmd_rag.py
  → use_search / _cmd_rag_search 関連テスト 削除 (他コマンドのテストは維持)

tests/test_orchestrator.py
  → two_stage_done / _finalize_answer シグネチャ変更への追従

tests/test_agent_rag.py
  → services.rag 参照テスト 削除
```

---

## Design

### two-stage fetch 除去後の orchestrator pipeline

```
現在:
  handle_turn()
    → _handle_memory_injection
    → _handle_history_compression
    → _handle_llm_turn
        └── LLM loop
              └── _finalize_answer(answer, two_stage_done)
                    └── [NEED_CONTEXT] marker → _maybe_two_stage_fetch()
                                                  → ctx.services.rag.last_reranked
                                                  → fetch_full_document()
                                                  → LLM 再実行

除去後:
  handle_turn()
    → _handle_memory_injection
    → _handle_history_compression
    → _handle_llm_turn
        └── LLM loop
              └── _finalize_answer(answer)  ← two_stage_done 引数なし
                    ← [NEED_CONTEXT] 分岐なし
```

### /rag コマンド削除後の cmd_rag.py

`_RagMixin` には `/tool`, `/note`, `/plan`, `/debug` の非 RAG ハンドラも含まれる。  
RAG 関連メソッドのみ削除し、`_RagMixin` クラス自体と非 RAG メソッドは維持する。

---

## Implementation steps

### Step 1: `scripts/agent/orchestrator.py` — two-stage fetch 全除去

1-a. `from rag.repository import fetch_full_document` インポート行を削除

1-b. `_fetch_two_stage_context()` メソッド全体を削除

1-c. `_maybe_two_stage_fetch()` メソッド全体を削除

1-d. `_finalize_answer()` の変更:
   - シグネチャから `two_stage_done: bool` 引数を削除
   - `if not two_stage_done:` ブロック (`_maybe_two_stage_fetch` 呼び出し) を削除
   - 戻り値型を `tuple[str | None, bool]` → `str | None` に変更

1-e. `handle_turn()` の変更:
   - `two_stage_done = False` 初期化を削除
   - `_finalize_answer(answer, two_stage_done)` → `_finalize_answer(answer)` に変更
   - `answer, two_stage_done = await ...` → `answer = await ...` に変更

### Step 2: `scripts/agent/factory.py` — RagPipeline 初期化除去

2-a. `from rag.pipeline import RagPipeline` インポート行を削除

2-b. `_init_rag_pipeline()` 関数全体を削除

2-c. `build_agent_context()` から `_init_rag_pipeline(ctx, view)` 呼び出しを削除

### Step 3: `scripts/agent/context.py` — ServiceContainer.rag 削除

3-a. `if TYPE_CHECKING: from rag.pipeline import RagPipeline` ブロックを削除

3-b. `ServiceContainer.rag: RagPipeline | None = None` フィールドを削除

### Step 4: `scripts/agent/config.py` — RAG フィールド全削除

4-a. `AgentConfig` から以下フィールドを削除:
   `rag_top_k`, `use_mqe`, `use_search`, `use_rrf`, `use_rerank`, `rag_min_score`,
   `rag_service_url`, `use_rag_mcp`, `use_two_stage_fetch`, `two_stage_max_docs`

4-b. `__post_init__()` から `self._validate_rag_params()` 呼び出しを削除

4-c. `_validate_rag_params()` メソッドごと削除

4-d. `_from_toml()` から各 RAG フィールドの読み込み行を削除

### Step 5: `scripts/agent/repl.py` — /rag 削除・startup banner 修正

5-a. `SLASH_COMMANDS` リストから `"/rag"` を削除

5-b. `_print_startup_banner()` の `ctx.cfg.use_search` 分岐を削除
   - `use_search` を参照せず常に `_get_chunk_count()` を表示するか、chunk_count 表示自体を削除

5-c. docstring・クラスコメントから `RagPipeline` の記述を削除

### Step 6: `scripts/agent/commands/cmd_rag.py` — RAG メソッド削除

6-a. `from rag.types import LLMMessage, RagHit` の `RagHit` を削除 (LLMMessage は他メソッドで使用)

6-b. 以下メソッドを削除:
   - `_print_rag_results()`
   - `_cmd_rag_search()`
   - `_cmd_rag_toggle()`
   - `_cmd_rag()`

### Step 7: `scripts/agent/commands/registry.py` — /rag dispatch 削除

7-a. help text から `/rag` 関連行を削除

7-b. dispatch テーブルから `("/rag", self._cmd_rag, True)` を削除

### Step 8: `scripts/agent/commands/cmd_config.py` — RAG フィールド表示・hot-reload 削除

8-a. `_cmd_config_show()` から `rag_top_k` / `use_mqe` / `use_search` / `use_rrf` / `use_rerank` 表示行を削除

8-b. `_apply_config_params()` から RAG フィールドの hot-reload 行を削除

### Step 9: `config/agent.toml` — RAG 関連キー削除

削除するキー:
`use_search`, `use_mqe`, `use_rrf`, `use_rerank`, `rag_top_k`, `rag_min_score`,
`rag_service_url`, `use_rag_mcp`, `use_two_stage_fetch`, `two_stage_max_docs`
(コメント行も含む)

### Step 10: テスト更新

10-a. `tests/test_cmd_rag.py` — `use_search` / `_cmd_rag_search` 関連テスト削除。`/tool`, `/note`, `/debug` テストは維持。

10-b. `tests/test_orchestrator.py` — `two_stage_done` / `_finalize_answer` 引数変更への追従確認

10-c. `tests/test_agent_rag.py` — `ctx.services.rag` 参照テストを削除または更新

### Step 11: バリデーション実行 (次節参照)

---

## Validation plan

```bash
# 1. フォーマット・lint
ruff format scripts/ && ruff check scripts/ tests/ --fix && ruff check scripts/ tests/

# 2. 型チェック
mypy scripts/ tests/

# 3. import layer 検証
PYTHONPATH=scripts lint-imports

# 4. テスト
pytest tests/ -v

# 5. カバレッジ
coverage run -m pytest tests/ && coverage xml
diff-cover coverage.xml --compare-branch=master --fail-under=90

# 6. pre-commit 全ゲート
pre-commit run --all-files
```

---

## Risks

### R-1: `_finalize_answer()` 戻り値型変更による型エラー

**内容**: `_finalize_answer()` の戻り値が `tuple[str | None, bool]` → `str | None` に変わる。LLM loop 内の呼び出し箇所を全件修正しないと mypy エラー。

**対処**: 実装後に `mypy scripts/` を実行し、型エラーを全件解消してから pytest を実行する。

### R-2: `cmd_rag.py` の `LLMMessage` import 残留

**内容**: `_RagMixin` には非 RAG メソッド (`_render_history_md`) が `LLMMessage` を使う。`RagHit` のみ除去し `LLMMessage` は残す必要がある。

**対処**: Step 6-a でインポートを精査し、`RagHit` のみ除去する。

### R-3: startup banner の `use_search` 参照

**内容**: `repl.py:237` — `chunk_count = self._get_chunk_count() if ctx.cfg.use_search else "disabled"` が `use_search` フィールド削除後に型エラーになる。

**対処**: `_get_chunk_count()` を常時呼ぶか、DB チャンク数表示行自体を削除する。`_get_chunk_count()` は SQLite DB に直接アクセスするため `use_search` フラグ不要。

### R-4: test_cmd_rag.py の残存 use_search 参照

**内容**: `tests/test_cmd_rag.py` が `cfg.use_search` に依存するテストを含む。フィールド削除後に ImportError/AttributeError が発生する。

**対処**: Step 10-a で該当テストを削除し、`/tool`, `/note`, `/debug` テストのみ残す。

### R-5: rag-pipeline-mcp への影響なし (確認)

**内容**: `mcp/rag_pipeline/service.py` は `rag.pipeline.RagPipeline` を lazy import で使用。`scripts/rag/` を削除しないため影響なし。

**対処**: 確認のみ (変更不要)。

### R-6: `AgentConfig` フィールド削除による既存設定ファイルのトランプ

**内容**: `config/agent.toml` に削除対象キーが残っている場合、`_from_toml()` が `cfg.get()` で読み込む際は `None` を返すだけで問題は起きない。ただし `toml` のキーを削除しないと余剰設定が残る。

**対処**: Step 9 で `config/agent.toml` からも対象キーを明示的に削除する。
