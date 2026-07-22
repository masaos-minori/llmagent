---
title: "Agent Operations and Observability - Startup and Health"
category: agent
tags:
  - agent
  - operations
  - startup
  - health-probes
  - operational-verification
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Purpose(目的)

起動手順、運用確認、ヘルスチェック、監査ログ、
OTelトレーシング、`/context` と `/stats` の解釈、トラブルシューティングを文書化する。

---

## Startup Procedure(起動手順)

```bash
# 1. Deploy files (if changed)
cp -r scripts/agent   /opt/llm/scripts/agent
cp -r scripts/shared  /opt/llm/scripts/shared

# 2. Activate venv
source /opt/llm/venv/bin/activate

# 3. Start agent
cd /opt/llm/scripts && python -m agent
```

期待される起動バナー:
``` text
DB: 12,345 chunks | Tools: 14
Memory: disabled
Type /help for commands, /exit to quit.

agent[:#1]>
```

**Memoryの行:** `CliView.write_startup_banner()`(`cli_view.py`)は引数 `memory_mode: str | None = None` を受け取り、`None` でない場合のみ `Memory: <mode>` 行を表示する。`repl.py` の `_print_startup_banner()` は常に `ctx.cfg.memory.use_memory_layer` から `"enabled"`/`"disabled"` を計算して渡すため、この行は常に表示される。

**Workflowの行:** `write_startup_banner()` は `workflow_status` が空文字でない場合のみ `Workflow: <status>` 行を追加表示する。`_get_workflow_status()` は `self._orchestrator is None` なら `"unknown"`、`orchestrator.workflow_status()["tracking"] == "enabled"` なら `"enabled"` を返す。ワークフロー定義は起動時に必ずロードされるため、本番環境では常に `"enabled"` が表示される。

**終了案内の文言:** 最終行は実装上 `"Type /help for commands, /exit to quit."` の固定文字列であり、"Ctrl-C or Ctrl-D" という文言はバナーには含まれない(旧記載は誤り)。ただし実際の終了経路としては `/exit` に加え、`repl.py` の `_read_input()` が `EOFError`(Ctrl-D)・`KeyboardInterrupt`(Ctrl-C)を捕捉して `None` を返し、`_repl_loop()` がそれを見てループを終了するため、Ctrl-C/Ctrl-Dによる終了自体は現在も機能する(根拠: Explicit in code)。

---

### Workflow Pending Approval Recovery

エージェント起動時に、前回のセッションで解決されなかった承認ゲート(つまり `/approve` も `/reject` も発行されなかったもの)が存在する場合、`startup.py` は保留中の承認状態を復元する:

- **タイミング:** 起動時、`ctx.workflow is not None` の場合
- **復元される内容:** `StateStore.find_latest_pending_approval()` を通じて `workflow.sqlite` から取得される最新のグローバルな保留中承認
- **複数セッション時の動作:** 保留中の承認は同時に1件のみ追跡される。全セッションを通じた最新のレコードが復元される(セッション固有ではない)
- **起動時警告の形式:** `[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve <approval_id> [reason] or /reject <approval_id> [reason].`(`reason` が未設定の場合は `none` と表示される。根拠: `startup.py` の `_recover_pending_approvals()`、`approval.reason or 'none'`)
- **確認方法:** `sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1;"`

---

## Operational Verification(運用確認)

### LLMサービスの確認

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":5}' -H 'Content-Type: application/json'
```

### 埋め込みサービスの確認

```bash
curl -s http://127.0.0.1:8081/health
```

### MCPサーバの状態

``` text
agent[:#1]> /mcp
```

期待される結果: すべてのサーバが `OK` ステータスで表示される。

### Minimal Agent DB Initialization(エージェントDBの最小初期化)

#### 使用場面

- 初めてのローカル開発時: session.sqlite と workflow.sqlite がまだ存在しない。
- いずれかのデータベースファイルを削除した後: スキーマが存在しない場合、起動時にエージェントが `OperationalError: no such table: sessions` を発生させる。

#### session.sqlite の初期化

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_session_schema
create_session_schema()
print("session schema OK")
PY
```

作成されるテーブル: `sessions`、`messages`、`memories`、`memories_fts`(FTS5仮想テーブル)、`memory_links`、`session_diagnostics`、`memories_vec`(vec0仮想テーブル)。

実装上の補足: `memory_links` テーブル(`src_id`/`dst_id` による関連メモリ間のリンク、`memories.memory_id` へのFK付き)は既存ドキュメントの一覧に含まれていなかった。根拠: `db/schema_sql.py` の `_SESSION_SCHEMA_TEMPLATE`(Explicit in code)。

#### workflow.sqlite の初期化

エージェント設定で `workflow_db_path` が設定されている場合のみ必要。

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_workflow_schema
create_workflow_schema()
print("workflow schema OK")
PY
```

作成されるテーブル: `tasks`、`attempts`、`processed_events`、`artifacts`、`approvals`、`workflow_schema_version`(適用済みマイグレーションのバージョン記録用)。

実装上の補足: `create_workflow_schema()` はテーブル作成後に `apply_workflow_migrations()`(`db/schema_sql.py`)を呼び出し、`attempts.error_kind`/`attempts.error_detail`/`artifacts.workflow_id`/`artifacts.attempt_number`/`processed_events.workflow_id` の列を `ALTER TABLE ... ADD COLUMN` で追加する。列が既に存在する場合の `duplicate column name` エラーのみ握りつぶし、それ以外の `OperationalError` は再送出される。最後に `workflow_schema_version` へ現在のスキーマバージョンを記録する(既存レコードと同一なら再挿入しない)。根拠: `db/schema_sql.py` の `apply_workflow_migrations()`、`db/create_schema.py` の `_record_workflow_schema_version()`(Explicit in code)。

#### テーブルの検証

```bash
sqlite3 /opt/llm/db/session.sqlite  ".tables"
# Expected: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions

sqlite3 /opt/llm/db/workflow.sqlite ".tables"
# Expected: approvals  artifacts  attempts  processed_events  tasks  workflow_schema_version
```

#### 再実行の安全性

両関数とも `CREATE TABLE IF NOT EXISTS` を使用する — 既存のDBに対して再実行しても安全であり、追加的なマイグレーションパッチのみが適用される。

#### エラーの文脈

エージェント起動時の `sqlite3.OperationalError: no such table: sessions` は、session.sqliteのスキーマが初期化されていないことを意味する。上記の `create_session_schema()` コマンドを実行すること。

---

### DB verification(DBの検証)

検証すべき3つのプラットフォームデータベース:

```bash
# rag.sqlite — RAG documents, chunks, embeddings
sqlite3 /opt/llm/db/rag.sqlite "SELECT lang, COUNT(*) AS docs FROM documents GROUP BY lang;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT COUNT(*) AS chunks FROM chunks;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT chunk_id, LENGTH(embedding) AS bytes FROM chunks_vec LIMIT 3;"
# Expected bytes: 1536 (384 dimensions × 4 bytes)

# session.sqlite — agent sessions and messages
sqlite3 /opt/llm/db/session.sqlite "SELECT session_id, created_at, title FROM sessions ORDER BY session_id DESC LIMIT 5;"
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) AS messages FROM messages;"

# workflow.sqlite — task tracking and event processing
sqlite3 /opt/llm/db/workflow.sqlite "SELECT COUNT(*) AS tasks FROM tasks;"
sqlite3 /opt/llm/db/workflow.sqlite "SELECT status, COUNT(*) FROM tasks GROUP BY status;"
```

3つすべてのスキーマ詳細: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`。

---

## Startup Validation Severity Mapping(起動時検証の重大度マッピング)

`StartupOrchestrator._check_services()`(`agent/startup.py`)は8個のチェックを実行し、各結果を
`StartupValidationResult`(`agent/shared/health_models.py`)に `OK` / `WARNING` / `FATAL` / `SKIPPED`
のいずれかとして記録する。`FATAL`が1件でも記録されると、全チェック完了後に`_check_services()`が
`RuntimeError`を送出し起動を中断する(`if pipeline.has_fatal: raise RuntimeError(...)`)。

以下は`agent/startup.py`の`_check_services()`本体と、そこから呼び出される
`agent/repl_health.py`の各チェック関数本体を全文読んで抽出した、正確な分岐条件の一次情報である
(呼び出し箇所の`add_fatal`/`add_warning`/`add_ok`だけでなく、各チェック関数の内部ロジックまで確認済み)。

| Check (source) | Severity | Condition | Rationale |
|---|---|---|---|
| `security_audit` (`audit_security_defaults()`) | FATAL | `audit_security_defaults()` raises `RuntimeError`. In `production_mode=True`: any HTTP MCP server without `auth_token`; `shell`/`github`/`git`/`cicd` audit config fails to load; `shell_sandbox_backend="none"`; `ProductionConfigValidator` reports errors. Independent of `production_mode`: `shell_sandbox_backend="firejail"` configured but the `firejail` binary is not on `PATH` (always raises, even outside production). | Production mode enforces auth/sandbox hardening as hard requirements; a missing `firejail` binary makes the configured sandbox non-functional regardless of security profile, so it is always fatal. |
| `security_audit` (`audit_security_defaults()`) | WARNING | Same checks as above but `production_mode=False` (or non-fatal findings even in production, e.g. GitHub `allow_force_push=true` / `require_pr_review=false`, DENY-ALL empty allowlists for `shell.command_allowlist` / `git.allowed_repo_paths` / `github.allowed_repos` / `cicd.workflow_allowlist` when `security_lockdown_enabled=False`). | Risky-but-not-fatal defaults in local/dev mode; the operator is warned but startup proceeds. |
| `security_audit` (`audit_security_defaults()`) | OK | `pipeline.add_ok("security_audit")` runs unconditionally right after the warnings loop, whenever `audit_security_defaults()` returns without raising. | Note: unlike the other checks below, `security_audit`'s `OK` does **not** mean "no issues" — it is recorded even when one or more `WARNING` outcomes were just added for this same source in the same run; it only signals that the audit function completed without raising. |
| `embedding_dimensions` (埋め込み次元検証) | FATAL | `ctx.cfg.memory.memory_embed_dim != build_db_config().embedding_dims`. | A silent embedding-dimension mismatch would corrupt vector search at query time; caught once at startup instead. |
| `embedding_dimensions` (埋め込み次元検証) | OK | Dimensions match. | — |
| `readiness` (準備状態チェック) | FATAL | `production_mode=True` and `check_service_health()` finds an unreachable/non-200 LLM or embed-LLM service (`result.has_issues`) — チェック関数が `RuntimeError` を内部で送出し、`_check_services()` の汎用例外ハンドラで捕捉。 | Production deployments must not start serving with a known-broken LLM/embedding backend. |
| `readiness` (準備状態チェック) | WARNING | `production_mode=False` and `result.has_issues` (same underlying probe failures as above, but non-fatal in dev). | Local/dev environments tolerate a temporarily unreachable service; the operator is warned instead of blocked. |
| `readiness` (準備状態チェック) | OK | `not result.has_issues` (both LLM and embed-LLM health probes returned HTTP 200). | — |
| `readiness` (準備状態チェック) | *(dead code — documented, not fixed)* | `_check_services()` も `error_messages()` ループを含むが、これは**実行時に到達しない**: `HealthCheckResult.errors` はコードベース全体で一切設定されない — すべての `HealthCheckResult(...)` 構築は `warnings=` のみ渡す。このループを実際の準備状態 FATAL トリガーとして読むべきではない — 実際のトリガーは上記の production-mode raise で、汎用例外ハンドラで捕捉される。 | Documented as-is per explicit reviewer decision; the code is intentionally left unmodified since removing it is a separate refactor outside this change's scope. |
| `tool_definitions` (ツール定義チェック) | WARNING | `tool_result.warning_messages()` が非空 (ツール名ミスマッチ)、**または** 厳密モード (`tool_definitions_strict=True`) の `RuntimeError` ("all servers unreachable" または "mismatch detected") — `_check_services()` の汎用例外ハンドラで捕捉され WARNING にダウングレードされる。 | `tool_definitions` never reaches `FATAL` from `_check_services()`, even when the underlying strict-mode check would otherwise raise — the outer `except` always turns it into a `WARNING`. |
| `tool_definitions` (ツール定義チェック) | OK | `not tool_result.has_issues` (includes the case where no tool definitions are configured or no servers are reachable — チェック関数は空の `HealthCheckResult()` を返す)。 | — |
| `routing_drift` (ルーティングドリフトチェック) | FATAL | `routing_drift_strict=True`(`ctx.cfg.tool.routing_drift_strict`)かつドリフトを検出した場合。`check_routing_drift(ctx, strict=True)` が内部で `RuntimeError` を送出し、`_check_services()` の `except RuntimeError` 節(汎用 `except Exception` より前に評価される)で捕捉され `pipeline.add_fatal("routing_drift", ...)` に回される。 | Previously `strict=` was never passed to `check_routing_drift(ctx)` at this call site, so `routing_drift_strict=True` had no effect and the broad `except Exception` clause would have downgraded any `RuntimeError` to a warning anyway. Both are now fixed: the flag is wired through, and a narrow `except RuntimeError` clause (evaluated before the broad one) routes it to `add_fatal` instead. |
| `routing_drift` (ルーティングドリフトチェック) | WARNING | ドリフトを検出したメッセージ(`routing_drift_strict=False`の場合)、または `check_routing_drift()` からの `RuntimeError` 以外の予期せぬ例外。 | Non-strict drift, and any non-`RuntimeError` failure from the check, still fall through to the generic `except Exception` handler as a warning — never fatal, and never recorded as an explicit `OK` either (see next row). |
| `routing_drift` (ルーティングドリフトチェック) | *(no outcome emitted)* | ドリフトなし (空リストを返す)。 | Unlike most other checks, there is no `pipeline.add_ok("routing_drift")` call anywhere in `_check_services()` — a clean result produces zero recorded outcomes for this source, not an explicit `OK` entry. |
| `routing_safety_tiers` (ルーティング安全性ティアチェック) | WARNING | レジストされたツールに宣言された安全性ティアがないメッセージ、または予期せぬ例外。 | Same rationale as `routing_drift` — a static config check, warning-only. |
| `routing_safety_tiers` (`check_routing_safety_tiers()`) | *(no outcome emitted)* | The check returns an empty list. | As with `routing_drift`, no `add_ok` call exists for this source — silence means healthy. |
| `routing_drift_live` (`check_routing_drift_vs_live()`) | WARNING | `strict=False` (from `ctx.cfg.tool.tool_definitions_strict`, default `False`) and `drift_result.warning_messages()` non-empty (live `/v1/tools` drift or duplicate tool ownership). | Live routing drift in non-strict mode is informational only. |
| `routing_drift_live` (`check_routing_drift_vs_live()`) | OK | `not drift_result.has_issues` (all servers reachable, no drift, no duplicates). | — |
| `routing_drift_live` (`check_routing_drift_vs_live()`) | SKIPPED | `production_mode=False` and any exception from the outer discovery call (including a `check_routing_drift_vs_live()` `RuntimeError` under `strict=True`) — caught by `_check_services()`'s `except Exception as exc:` block, which now branches on `production_mode` (see next row). | Live/dynamic checks may legitimately be unavailable in some valid environments (e.g. MCP servers not yet started); `SKIPPED` distinguishes "could not check" from "checked and found a problem" (`WARNING`). |
| `mcp_tool_discovery` (outer `except Exception` around `McpToolDiscoveryService(ctx).discover_all()`) | FATAL | `production_mode=True` and the outer discovery call raises for any reason (including the `check_routing_drift_vs_live()` cases above). A discovery-call failure means every tool call will fail for the entire session — an outage-grade condition, unlike a per-server finding (handled separately inside the `try` block and never escalated by this except clause). | Production deployments must not silently continue with tool-call routing entirely broken; matches the same production-fatal precedent already used by `_start_servers()` for subprocess startup failures. |
| `routing_drift_live` (`check_routing_drift_vs_live()`) | *(dead code — documented, not fixed)* | `_check_services()` also contains `if strict: pipeline.add_fatal("routing_drift_live", msg)` for each `drift_result.warning_messages()` entry. Reading `check_routing_drift_vs_live()` (`agent/repl_health.py`) in full shows this is **unreachable**: whenever `strict=True` and there is any actual duplicate/drift condition, the function raises `RuntimeError` *before* returning — so a `drift_result` returned (not raised) under `strict=True` can only ever have empty `warning_messages()`. The raise itself is caught by the generic `except Exception` above and reported as `SKIPPED`, not `FATAL`. | Newly identified during this review; mirrors the same pattern as `readiness`'s `error_messages()` loop — an `add_fatal` call sits in the code but the condition that would populate it can never occur at runtime. Documented here for accuracy; the code is intentionally left unmodified (out of scope — no existing severity classification was changed). |
| `rag_consistency` (`RagMaintenanceService().consistency()`) | OK | `rag_check.is_consistent` is `True`. | — |
| `rag_consistency` (`RagMaintenanceService().consistency()`) | WARNING | `rag_check.is_consistent` is `False` — one `WARNING` per entry in `rag_check.issues`. | RAG consistency issues (e.g. orphaned chunks) are recoverable and don't block startup. |
| `rag_consistency` (`RagMaintenanceService().consistency()`) | SKIPPED | Any exception raised while constructing `RagMaintenanceService()` or calling `.consistency()`. | Same rationale as `routing_drift_live`'s `SKIPPED`: a live/dynamic check (touches the RAG DB) that may legitimately be unavailable — e.g. a fresh install with no RAG data yet — distinct from the static config checks (`routing_drift` / `routing_safety_tiers`) which use `WARNING` even on exception, since a failure reading local config is more likely a real config problem than an expected absence of data. |

補足:
- `FATAL`は全チェック完了後に集約判定される。単一の`FATAL`でも起動全体が中断される。
- `WARNING`と`SKIPPED`はいずれも起動を継続させるが意味が異なる: `WARNING`は「チェックを実行し問題を検出した」、`SKIPPED`は「チェック自体を実行できなかった」ことを示す。
- 表中の *(dead code — documented, not fixed)* / *(no outcome emitted)* は、コード上に存在するが実行時には到達しない分岐、または「正常時に何のoutcomeも記録されない」挙動についての注記であり、レビュー時にコードの意図を明確化するために追記したものである(該当コード自体は変更していない)。
- テストによる裏付け: `tests/test_startup.py`の`TestCheckServicesSeverityClassification`が、上表の各行に対応する回帰テストを提供する。`routing_drift`のFATAL行(`routing_drift_strict=True`時)とWARNING行(`routing_drift_strict=False`時)は、`TestCheckServicesSeverityClassification`クラス自体にはまだ個別テストがないが、`tests/test_startup_validation_pipeline.py`の`test_routing_drift_strict_true_raises_fatal`(FATAL、`check_routing_drift()`の`RuntimeError`が`_check_services()`経由で伝播し起動を中断することを検証)と`test_routing_drift_strict_false_warns_only`(WARNING、ドリフトメッセージが起動を中断しないことを検証)によって、`_check_services()`経由のエンドツーエンドの回帰カバレッジが確保されている。
- 回帰テスト: `tests/test_startup.py`の`test_mcp_tool_discovery_fatal_in_production_on_exception`が、`production_mode=True`時にこの分岐が`FATAL`になることを検証する。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

startup procedure
operational verification
health probes
minimal agent db initialization
