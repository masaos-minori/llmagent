# 02_implement_plan.md

## Goal

`00_llm_spec_tobe.md` に記載された後方互換コード除去・責務分離・堅牢化を完了させる。
既に実施済みの改善を除き、残存する技術的負債を段階的に解消する。

---

## Scope

**In scope**

| # | 対象ファイル | 変更内容 |
|---|---|---|
| 1 | `session.py` | `save_many()` を `executemany()` に寄せる |
| 2 | `session.py` | JSON 破損レコード検知を audit イベント化 |
| 3 | `repl_health.py` | watchdog の `transport.start()` 直接呼び出しフォールバック削除 |
| 4 | `repl_tool_exec.py` + テスト | テスト import を新モジュールパスに更新し re-export layer を削除 |
| 5 | `config.py` | `_get_cfg()` の silent fallback → fail-fast |
| 6 | `config.py` | `AgentConfig.__getattr__`/`__setattr__` 除去 (flat access 30 件を移行) |
| 7 | `context.py` | `ServiceContainer` deprecated alias 除去 |
| 8 | `context.py` | `AgentContext.__getattr__`/`__setattr__` 除去 (flat access 320 件を移行) |
| 9 | `factory.py` | builder を `observability`/`memory`/`tools`/`llm` サブモジュールへ分割 |
| 10 | `cli_view.py` | stdout/stderr/input を injectable にし terminal adapter へ寄せる |
| 11 | `repl.py` | `AgentBootstrap` 起動専用クラスを抽出 |

---

## Assumptions

- `.venv/` は `uv sync --dev` 済みで `source .venv/bin/activate` できる
- テストは `python -m pytest tests/ -v` で実行可能
- `ctx.services.lifecycle` は factory.py の `_build_tool_executor()` が必ず構築するため、実行時 `None` にならない
- `AgentConfig` は 7 つの sub-config (`llm`, `rag`, `tool`, `memory`, `mcp`, `approval`, `obs`) で構成済み
- `AgentContext` は `conv`/`turn`/`stats` サブ構造で構成済み
- 新しいモジュール追加時は `deploy/deploy.sh` のコピーリストを更新すること

---

## Unknowns

| ID | 不明点 | エビデンス不足 | 解決方法 | ブロッカーか |
|---|---|---|---|---|
| U1 | `AgentConfig.__getattr__` 経由の flat access 30 件の内訳 (サブ config 別) | 未カウント | `grep -rn "cfg\.\(llm_url\|context_char_limit\|..." scripts/` で各フィールド確認 | No — 実装 Step 6 前に確認 |
| U2 | `AgentContext.__getattr__` 経由の flat access 件数の内訳 | 320 件のうち直接フィールドが何件かは不明 | `grep -rn "ctx\.\(history\|debug_mode\|plan_mode\|stat_\|current_turn_id\|llm_url\b\|shutdown_requested\)" scripts/` | No — 実装 Step 8 前に確認 |
| U3 | `ServiceContainer` を直接 import している箇所 | **解決済み**: `context.py:114` (クラス定義) + `memory/layer.py:43` (docstring) の 2 件のみ | 削除前に該当 2 件を修正 | No |
| U4 | `cli_view.py` injectable 化で影響を受けるテスト数 | **解決済み**: `tests/test_cli_view.py` に 15 メソッド超。`readline` はモック済みだが `print`/`input` はモック未対応 | `TerminalAdapter` 導入後に `test_cli_view.py` を `TerminalAdapter(stdout=io.StringIO())` を使って更新 | No |
| U5 | `factory.py` のサブモジュール分割で `deploy.sh` に追加が必要なファイル数 | 新ファイル数不明 | 分割計画確定後にカウント | No — 実装 Step 9 前に確認 |

---

## Affected Areas

| ファイル | 変更種別 | テスト有無 | チャーンリスク |
|---|---|---|---|
| `scripts/agent/session.py` | 修正 | `tests/test_session.py` | 低 |
| `scripts/agent/repl_health.py` | 修正 (1 行削除) | なし (watchdog は統合テスト相当) | 低 |
| `scripts/agent/repl_tool_exec.py` | 削除 | `test_agent_repl_tool_exec.py` / `test_tool_approval.py` (broken) | 中 |
| `scripts/agent/llm_turn_runner.py` | import 1 行修正 | `tests/test_llm_turn_runner.py` | 低 |
| `tests/test_agent_repl_tool_exec.py` | import 修正 | — | 低 |
| `tests/test_tool_approval.py` | import 修正 | — | 低 |
| `scripts/agent/config.py` | 修正 + flat access 除去 | `tests/test_config_loader.py` | 中 |
| `scripts/agent/context.py` | deprecated alias 除去 + flat access 除去 | `tests/test_agent_session.py` ほか | 高 |
| `scripts/agent/factory.py` + 新サブモジュール群 | リファクタリング + 新規 | `tests/test_agent_factory.py` | 中 |
| `scripts/agent/cli_view.py` | 修正 | `tests/test_cli_view.py` | 中 |
| `scripts/agent/repl.py` | リファクタリング | なし (REPL は手動テスト) | 中 |
| `deploy/deploy.sh` | 新規ファイル追加 | — | 低 |

---

## Design

### Step 1-2: session.py — executemany & audit event

`save_many()` の `for row in rows: db.execute(...)` を `db.executemany(sql, rows)` 1 呼び出しに変更。
`fetch_messages()` の JSON 破損時 (現状 `warning` ログのみ) に `audit_logger.warning` ではなく audit イベント
`{"event": "corrupt_record", "session_id": ..., "message_id": ...}` を emit する。
ただし `fetch_messages()` は `AgentContext` を持たないため、破損検知は `SessionMessageRepository` 内で行い
呼び出し元 (`AgentSession`) が監査ログへ記録する設計とする。

### Step 3: repl_health.py — fallback 削除

`_watchdog_check_stdio()` line 256-260 の `else` ブロック (lifecycle が None の場合に直接 `transport.start()` を呼ぶ) を削除。
lifecycle は factory.py が常に注入するため、このパスは dead code であることが確認済み。

### Step 4: repl_tool_exec.py — re-export layer 廃止

現状:
- `test_agent_repl_tool_exec.py` が `repl_tool_exec` から `_classify_risk`, `_check_allowed_root`, `_check_allowed_repo` を import → **ImportError で収集失敗**
- `test_tool_approval.py` が `repl_tool_exec` から `_classify_operation_type` を import → **失敗**
- `llm_turn_runner.py` が `repl_tool_exec` から `execute_all_tool_calls` を import

対処:
1. `test_agent_repl_tool_exec.py`: `from agent.tool_policy import classify_risk as _classify_risk, check_allowed_root as _check_allowed_root, check_allowed_repo as _check_allowed_repo`
2. `test_tool_approval.py`: `from agent.tool_policy import classify_operation_type as _classify_operation_type`
3. `llm_turn_runner.py`: `from agent.tool_runner import execute_all_tool_calls`
4. `repl_tool_exec.py` 削除

### Step 5: config.py — fail-fast

`_get_cfg()` の `except Exception` ブロックで `return {}` (silent fallback) を廃止し、
代わりに `raise ConfigLoadError(f"Failed to load config: {e}")` を raise する。
必須フィールドの欠落は `__post_init__` の `ValueError` で検知済みのため、
`_get_cfg()` のレベルでは「ファイル読み込み失敗」のみを対象にする。

```python
# before
except Exception as e:
    logging.getLogger(__name__).warning("Config load failed: %s", e)
    return {}

# after
except Exception as e:
    raise ConfigLoadError(f"Config load failed: {e}") from e
```

### Step 6: config.py — flat access 除去

1. `grep -rn "cfg\.<flat_field>" scripts/` で 30 件を列挙
2. 各アクセスを `cfg.<sub_config>.<field>` に置換 (例: `cfg.llm_url` → `cfg.llm.llm_url`)
3. `AgentConfig.__getattr__` / `__setattr__` と `_SUB_CONFIGS` を削除
4. ruff / mypy / pytest 通過を確認

### Step 7: context.py — ServiceContainer alias 除去

`ServiceContainer` クラス (alias) を削除。
既知の参照: `agent/context.py:114`, `agent/memory/layer.py:43` の docstring のみ → docstring 修正で対応。

### Step 8: context.py — flat access 除去

最大 scope の変更。事前に behavior-lock テストを取得してから進める (`python-test-and-fix` スキル)。

1. `grep -rn "ctx\.\(history\|debug_mode\|plan_mode\|llm_url\b\|shutdown_requested\|system_prompt\|current_turn_id\|stat_\)" scripts/` で件数確認
2. 変換ルール:
   - `ctx.history` → `ctx.conv.history`
   - `ctx.debug_mode` → `ctx.conv.debug_mode`
   - `ctx.plan_mode` → `ctx.conv.plan_mode`
   - `ctx.llm_url` → `ctx.conv.llm_url`
   - `ctx.shutdown_requested` → `ctx.conv.shutdown_requested`
   - `ctx.system_prompt_name` → `ctx.conv.system_prompt_name`
   - `ctx.system_prompt_content` → `ctx.conv.system_prompt_content`
   - `ctx.current_turn_id` → `ctx.turn.current_turn_id`
   - `ctx.stat_*` → `ctx.stats.stat_*`
3. `__getattr__` / `__setattr__` と `_CONV_FIELDS` / `_TURN_FIELDS` / `_STATS_FIELDS` / `_ALL_COMPAT` を削除

### Step 9: factory.py — submodule split

`factory.py` (192 行) を以下に分割:

| 新ファイル | 移動する関数 |
|---|---|
| `agent/builders/llm.py` | `_build_llm_client()` |
| `agent/builders/tools.py` | `_build_tool_executor()`, `_build_history_manager()` |
| `agent/builders/memory.py` | `_build_memory_layer()` |
| `agent/builders/observability.py` | `_build_audit_logger()`, `init_tracer()`, `_init_plugin_registry()` |
| `agent/factory.py` (残存) | `build_agent_context()` のみ (各 builder を import して呼ぶ orchestrator) |

`deploy/deploy.sh` に新規 `agent/builders/*.py` を追加。

### Step 10: cli_view.py — injectable terminal adapter

```python
@dataclass
class TerminalAdapter:
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    input_fn: Callable[[str], str] = field(default=input)
```

`CLIView.__init__` に `adapter: TerminalAdapter | None = None` を追加。
`print(...)` → `self._adapter.stdout.write(...)` / `self._adapter.stdout.flush()`
`input(...)` → `self._adapter.input_fn(...)`

### Step 11: repl.py — AgentBootstrap 抽出

`AgentREPL` から以下を `AgentBootstrap` に移動:
- `_init_components()`
- `_start_subprocess_servers()`
- `_check_service_health()`
- `_check_tool_definitions()`
- SQLiteHelper 初期化
- ウォッチドッグ起動

`AgentREPL` は `_repl_loop()` と `run()` のみを保持する入出力ループに縮小。

---

## Pre-existing Test Failures (実装開始前の状態)

現在 `test_agent_repl_tool_exec.py` を除外した状態で **42 件の failing tests** が存在する。
これらは過去のリファクタリングで API が変わったがテストが追従していない状態。
実装 Step 0 で一括修正する。

| テストファイル | 件数 | 原因 |
|---|---|---|
| `test_agent_session.py` | 18 | `AgentSession.save()` が Repository 分割で削除された。テストは旧 API を呼ぶ |
| `test_lifecycle.py` | 13 | `ServerLifecycleManager` を Http/Stdio 分割後のアサーションが旧動作を想定 |
| `test_orchestrator.py` | 5 | `ctx.stat_*` flat access が変わったことによる `AttributeError` 等 |
| `test_tool_approval.py` | 5 | `TestClassifyOperationType` が `repl_tool_exec` から `_classify_operation_type` を import しようとして失敗 |
| `test_agent_repl_tool_exec.py` | ImportError | `_classify_risk` / `_check_allowed_root` / `_check_allowed_repo` が `repl_tool_exec` に存在しない |

---

## Implementation Steps

実施順序。上位 step が完了しないと下位が進めない依存あり。

| Step | 内容 | 依存 | 優先度 | 難易度 |
|---|---|---|---|---|
| **0** | **既存テスト 42+件の修正** (API 追従) | なし | **Critical** | 中 |
| 1 | `save_many()` → `executemany()` (session.py) | Step 0 完了後 | High | 低 |
| 2 | watchdog fallback 削除 (repl_health.py) | Step 0 完了後 | High | 低 |
| 3 | テスト import 修正 + `llm_turn_runner.py` 修正 + `repl_tool_exec.py` 削除 | Step 0 完了後 | **Critical** (現在テスト broken) | 低 |
| 4 | JSON 破損 audit event (session.py) | Step 1 完了後 | Medium | 低 |
| 5 | `_get_cfg()` fail-fast (config.py) | なし | Medium | 低 |
| 6 | `AgentConfig` flat access 除去 30 件 (config.py) | Step 5 完了後 | Medium | 中 |
| 7 | `ServiceContainer` alias 除去 (context.py) | Step 6 完了後 | Medium | 低 |
| 8 | `AgentContext` flat access 除去 (context.py) | **behavior-lock テスト取得** + Step 7 完了後 | Low | **高** |
| 9 | `factory.py` submodule split | なし (Step 6-7 と並列可) | Low | 中 |
| 10 | `cli_view.py` injectable adapter | なし (Step 8 と並列可) | Low | 中 |
| 11 | `repl.py` AgentBootstrap 抽出 | Step 9, 10 完了後 | Low | 中 |

### Step 0 の詳細

| サブタスク | 対象 | 対処方法 |
|---|---|---|
| 0-a | `test_agent_session.py` (18 件) | `session.save()` → `session._message_repo.save()` 等の新 API に更新、または `AgentSession` に旧 API の thin wrapper を追加 |
| 0-b | `test_lifecycle.py` (13 件) | HTTP/Stdio 分割後の新 `ServerLifecycleManager` の振る舞いに合わせてモックとアサーションを更新 |
| 0-c | `test_orchestrator.py` (5 件) | `ctx.stat_*` アクセスの変化を確認し修正 |
| 0-d | `test_tool_approval.py` `TestClassifyOperationType` (5 件) | `from agent.tool_policy import classify_operation_type` に修正 |
| 0-e | `test_agent_repl_tool_exec.py` (ImportError) | Step 3 と同時対応 |

---

## Validation Plan

各 Step 完了後に実行するバリデーション。

| Step | コマンド | 合格基準 |
|---|---|---|
| 1, 2, 3 | `python -m pytest tests/test_agent_repl_tool_exec.py tests/test_tool_approval.py tests/test_session.py -v` | エラー 0 件 |
| 3 (削除確認) | `grep -rn "from agent.repl_tool_exec" scripts/ tests/` | マッチ 0 件 |
| 4 | `python -m pytest tests/test_session.py -v` | エラー 0 件 |
| 5 | `python -m pytest tests/test_config_loader.py -v` | エラー 0 件 |
| 6 | `PYTHONPATH=scripts lint-imports && python -m pytest tests/ -v` | エラー 0 件 |
| 7 | `grep -rn "ServiceContainer" scripts/ tests/` | マッチ 0 件 |
| 8 | `python -m pytest tests/ -v && PYTHONPATH=scripts lint-imports` | 全テスト通過 |
| 9 | `python -m pytest tests/test_agent_factory.py -v` | エラー 0 件 |
| 10 | `python -m pytest tests/test_cli_view.py -v` | エラー 0 件 |
| 全 Step | `ruff check scripts/ && mypy scripts/ && bandit -r scripts/ -c pyproject.toml && pre-commit run --all-files` | 全チェック通過 |

---

## Risks

| ID | リスク | 影響度 | 対処 |
|---|---|---|---|
| R1 | Step 8 の flat access 除去は 320 件規模のバラつきがあり、見落としが `AttributeError` を引き起こす | **高** | behavior-lock テスト取得 → ast-grep で `ctx\.FLAT_FIELD` を網羅的に検出 → mypy を通して未移行箇所を型エラーで検出。段階的 PR で差し戻し可能にする |
| R2 | Step 5 の fail-fast により、開発環境の設定不備が即座に起動失敗になる | 中 | `config/` 設定ファイルの全キーが存在するか CI で確認。`ConfigLoadError` を明示的な例外クラスにしてログを充実させる |
| R3 | Step 9 の factory 分割で `deploy.sh` 更新漏れによる本番デプロイ失敗 | 中 | 分割完了後に `scripts/agent/builders/` 以下のファイルを全て `deploy.sh` に追記。CI で `diff deploy.sh` をレビュー |
| R4 | Step 3 (`repl_tool_exec.py` 削除) により他の未発見 import が壊れる | 低 | 削除前に `grep -rn "repl_tool_exec" scripts/ tests/ docs/` で全参照を洗い出す |
| R5 | Step 10 の CLI injectable 化でインタラクティブテストが `sys.stdout` 依存から外れる | 低 | `TerminalAdapter(stdout=io.StringIO())` を使ったユニットテストを追加し、既存の `CLIView` テストが通ることを確認 |
| R6 | Step 0-a で `AgentSession` に旧 API wrapper を追加するか、テストを新 API に書き換えるかの判断によってテストの網羅性が変わる | 中 | 旧 API wrapper (thin delegation) を `AgentSession` に残さず、テストを新 Repository API で書き直す。これにより Repository レイヤーの単体テストが増加し品質が向上する |

### R1 対処の詳細手順 (Step 8 実施前)

```bash
# 1. behavior-lock テスト取得 (python-test-and-fix スキル)
# 2. 移行前に flat access 全件を機械的に抽出
grep -rn "ctx\.\(history\b\|debug_mode\|plan_mode\|llm_url\b\|shutdown_requested\|system_prompt_name\|system_prompt_content\|current_turn_id\|stat_turns\|stat_tool_calls\|stat_tool_errors\|stat_latency\|stat_semantic_cache_hits\|stat_input_tokens\|stat_output_tokens\)" scripts/ | wc -l
# 3. mypy で型チェックを掛けて AttributeError を事前検出
mypy scripts/ 2>&1 | grep "has no attribute"
```
