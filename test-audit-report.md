# テストスイート QAレビュー・リファクタリング安全性評価・改善計画

作成日: 2026-07-24 / 対象リポジトリ: `/home/masaos/llmagent` (branch: `master`, HEAD時点)
実行環境: `uv run` 経由、Python 3.13、`.venv/`

## 0. 事前確認事項(指示間の整合性)

- `memo1.md` は「破壊的コマンド禁止・読み取り専用調査を優先」と指示する一方、`AGENTS.md` は「ローカルコマンドはdestructiveなものも含め確認なしに直接実行してよい」と指示している。今回は読み取り専用の監査タスクのため実質的な衝突は発生しなかったが、1点だけ注意事象が発生した: `uv run pre-commit run --all-files`(リポジトリ標準の検証コマンド)の `ruff --fix` フックが3ファイル(`scripts/mcp_servers/cicd/cicd_server.py`, `service_business.py`, `scripts/mcp_servers/github/github_server.py`)を自動修正した。`memo1.md`の「本番コードを無断で変更しない」方針に従い、`git checkout --` で直ちに元に戻し、作業ツリーはクリーンな状態を維持した(内容はimport順序の並べ替えのみで、`ruff check`が検出した4件のエラーと一致)。
- `rules/toolchain.md` / `.github/workflows/ci.yml` は検証コマンドで `--compare-branch=main` および `branches: [main]` を指定しているが、本リポジトリには `main` ブランチが存在せず(`git branch -a` は `master` のみ)、これは後述 Finding **CI-1** として報告する。

---

## 1. Overall Findings

- 単体テストの絶対量は多い(`tests/` 配下 269ファイル、4425件 pass)が、**9件の既存テスト失敗**があり、CIの「test」ジョブは現時点で確実にredである。
- `bandit`(セキュリティスキャン)は**現状failしている**(exit code 1)。CIの「lint」ジョブの `Security scan` ステップも現行コードではredになるはずである。9件はいずれも動的WHERE句組み立てによるfalse positiveだが、`# nosec` 未注釈のため機械的に検出され続けている。
- `lint-imports`(アーキテクチャ境界検査)も**現状failしている**。`eventbus` 層が独立層であるべきという `.importlinter` の契約に反し、`db.helper` / `shared.json_utils` に依存している。ドキュメント(`rules/env.md`)の記述と実装が乖離している。
- CIの `diff-cover --compare-branch=main` は本リポジトリでは実行不能(`main` ブランチ不在)。ローカルでも同様に失敗する。CIの `on: push/pull_request: branches: [main]` も同じ理由でトリガーされない可能性が高く、**CIの2ジョブ(lint/test)がそもそも発火しているか自体に疑義がある**。
- 行カバレッジは全体で87%(`coverage report`実測)だが、モジュール間の偏りが大きい。特に `scripts/mcp_servers/github/service_*.py`(GitHub MCPサーバのビジネスロジック一式)は21〜47%と低く、`scripts/agent/commands/memory_data_ops.py`(12%、複雑度D評価)、`scripts/agent/workflow/validate.py`(0%)、`scripts/mcp_launcher.py`(0%)など未テストの本番コードパスが複数存在する。
- 最も強い領域: `mcp_servers` の権限・安全系ガード(`git_security.py`, `github/service_security.py`, `cicd/service_guards.py`, `mdq/auth.py`)、`shared/formatters.py`、`db/schema_sql.py`。いずれもfail-closed設計・境界値・異常系テストが手厚い。
- 最も弱い領域: `scripts/shared/json_utils.py`・`config_utils.py`・`llm_hot_config.py`(専用テストがゼロ、他レイヤーから広く使われる共通コードにもかかわらず無防備)、GitHub MCPサービス層、RAG ingestion の crawler/chunk_splitter 実処理経路。
- リファクタリングの安全性: 全面的に安全とは言えない。`agent/orchestrator.py`・`agent/http_lifecycle.py`・`shared/config_loader.py`・`eventbus/db.py`(マイグレーション部分)・`rag/ingestion/crawler.py` は High-risk-refactor と判定。ガードテスト追加が先行条件。
- 9件の失敗のうち5件(`test_rag_tools_consistency.py`)は「テスト自体がAPI変更に追随できておらずクラッシュしている」状態で、実質的にRAGツール登録の整合性は**現在まったく検証されていない**。これはカバレッジの見かけ上の値(87%)が実際の保護水準を過大評価している典型例である。

---

## 2. Executed Tests / Validation Commands

| # | command | purpose | result | notes |
|---|---|---|---|---|
| 1 | `uv run ruff format --check scripts/` | フォーマット検査 | pass | 差分なし |
| 2 | `uv run ruff check scripts/` | Lint検査 | fail | 4エラー(全てI001 import未整列)。`cicd_server.py`, `service_business.py`(2箇所), `github_server.py`。`--fix`で自動修正可能だが未適用のまま維持(read-only方針) |
| 3 | `uv run mypy scripts/` | 型検査(primary) | pass | 350ファイル、エラー0件 |
| 4 | `uv run pyright scripts/` | 型検査(alternate/cross-validate) | fail | 29エラー、12ファイル。主に`attach_auth_middleware`のFastAPI Protocol不一致(web_search_server.py等)と`git_helper.py`のGitPython動的属性(`git.exc`)アクセス。mypyはpassしておりCIのゲートはmypyのみのため優先度Low、内容確認要 |
| 5 | `uv run bandit -r scripts/ -c pyproject.toml` | セキュリティスキャン | **fail** (exit 1) | 14×B101(assert_used, low), 1×B104(bind-all-interfaces), 3×B105/1×B107(hardcoded password *string定数*, low), 1×B404(subprocess import), **8×B608(SQL injection疑い, medium)**。B608を個別に現物確認した結果、全件が動的WHERE句+プレースホルダのfalse positiveで実害なし(下記2.1参照)だが`# nosec`未注釈のため機械的にfailする |
| 6 | `PYTHONPATH=scripts uv run lint-imports` | アーキテクチャ境界検査 | **fail** | 4契約KEPT、1契約BROKEN。`eventbus-is-isolated`契約違反(下記3, Finding EVENTBUS-1参照) |
| 7 | `uv run pytest -q --tb=short`(フル、非coverage) | ユニット/統合テスト全体 | **fail(partial pass)** | 9 failed, 4425 passed, 13 skipped, 167s。2回実行し同一の9件が再現(決定論的、非flaky) |
| 8 | `uv run coverage run -m pytest tests/` → `coverage xml` → `coverage report` | カバレッジ計測 | fail(pytest部分に起因) / xml生成成功 | 同一9件が失敗(184s、coverage計装により若干遅延)。TOTAL line coverage 87%(17517 stmts, 2290 miss) |
| 9 | `uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | 差分カバレッジ90%ゲート | **not runnable** | `main`ブランチが存在しないため`fatal: ambiguous argument 'main...HEAD'`でエラー終了。Finding **CI-1** |
| 10 | `uv run pre-commit run --all-files` | 最終ゲート | fail→修正後pass相当 | `ruff`フックのみFailed(4件を自動fix、ファイルは直後にgit checkoutで復元)。`ruff-format`/`no-datetime-utc`/`mypy`/`docs-consistency`/`no-compat-stubs`は全てPassed |
| 11 | `uv run check-mcp-docs` | MCPドキュメント整合性 | pass | No issues found |
| 12 | `uv run check-agent-docs` | Agentドキュメント整合性 | pass(warning 2件) | `05_agent_90_inconsistencies_and_known_issues.md`が過去の既知不整合(`/export`, `/rag`)を記録目的で言及しているものを誤検知。実害なし(ドキュメントの性質上の既知の誤検知) |
| 13 | `uv run radon cc scripts/ -s -n C` | 循環的複雑度(C以上) | 実行成功(参考情報) | 27箇所がC〜E評価。最重度: `mcp_servers/mdq/parser.py:parse_markdown` が **E(40)**。詳細は7章 |
| 14 | `uv run vulture` / `uv run semgrep` / `uv run pip-audit` | デッドコード/意味的検査/依存脆弱性 | **未実施** | `rules/toolchain.md`では「Additional static analysis」(CI必須ゲートではない)扱いのため今回はスコープ外。次のタスクとして提案(Task LOW-1) |

### 2.1 bandit B608(SQL injection疑い)8件の内訳と評価

| # | 場所 | 実際の構造 | 評価 |
|---|---|---|---|
| 1 | `scripts/eventbus/db.py:195` | `IN ({",".join("?" for _ in topics)})` + パラメータ化 | false positive |
| 2 | `scripts/eventbus/subscribe_route.py:47` | 同上パターン | false positive |
| 3 | `scripts/mcp_servers/mdq/db_grep.py:72` | `WHERE`句を固定カラム名の断片リストから組立、値は全て`params`でバインド | false positive |
| 4 | `scripts/mcp_servers/mdq/health_check.py:35` | `STALE_SQL_CONDITION`(固定文字列定数)を埋め込み | false positive |
| 5 | `scripts/mcp_servers/mdq/mdq_service.py:205` | 同上(where_clauses断片+params) | false positive |
| 6 | `scripts/mcp_servers/mdq/mdq_service.py:327` | `STALE_SQL_CONDITION`埋め込み | false positive |
| 7 | `scripts/mcp_servers/mdq/search.py:145` | `_build_search_where()`が返す固定断片+params | false positive |
| 8 | `scripts/mcp_servers/mdq/search.py:156` | 同上 | false positive |

全件ユーザー入力が直接SQL文字列へ混入する経路はなく、値は必ず`?`プレースホルダでバインドされている。`scripts/db/maintenance.py:148`・`scripts/db/store_impl.py:258`(db層)には同一パターンに対し既に`# nosec B608`が付与済みであり、本8件のみ注釈漏れという扱いの不一致がある。

---

## 3. Existing Test Failures

### FAIL-1: RAGツール登録整合性テスト一式のクラッシュ (5件)
- **test**: `tests/test_rag_tools_consistency.py::TestRagToolsInRegistry::{test_rag_debug_pipeline_registered, test_rag_run_pipeline_registered, test_rag_delete_document_registered, test_rag_list_documents_registered, test_all_rag_tools_registered}`
- **failure type**: `AttributeError: 'ToolRouteResolver' object has no attribute '_registry'`
- **likely cause**: `scripts/shared/route_resolver.py` の `ToolRouteResolver` はライブ `/v1/tools` ディスカバリを介した `RuntimeToolRegistry` 注入モデル(`_runtime_registry`, `runtime_registry=`引数)に置き換わっているが、テスト側は旧実装(静的な`_registry`属性を直接参照)のまま。テストは`ToolRouteResolver(server_configs={}, discovery_map=None, strict_mode=False)`で`runtime_registry`を渡していないため、そもそも`_registry`という属性自体が存在しない。
- **severity**: High(このテストはRAGツールがツールレジストリに正しく登録されているかを検証する唯一のテストであり、現状は「クラッシュしているため何も検証していない」)
- **deterministic/flaky**: deterministic(2回実行し再現)
- **root cause**: **test code bug**(古いAPIを参照した陳腐化テスト)
- **evidence**: `tests/test_rag_tools_consistency.py:20`, `scripts/shared/route_resolver.py:59-108`

### FAIL-2: rag_pipeline `/v1/tools` に `schema_version` が欠落
- **test**: `tests/agent/services/test_mcp_tool_discovery.py::TestToolsEndpointSchemaVersion::test_schema_version_present[mcp_servers.rag_pipeline.rag_pipeline_server-app-rag_pipeline]`
- **failure type**: `AssertionError: [rag_pipeline] /v1/tools response missing schema_version`
- **likely cause**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:163` の `list_tools()` が `{"tools": [...]}` を手組みで返しており、他の全MCPサーバ(`git_server.py`, `file/*_server.py`, `shell_server.py`, `mdq_server.py`, `server.py`基底の`build_tools_response()`)が付与している`schema_version`キーを含めていない。
- **severity**: High(MCPツールディスカバリの契約違反。rag_pipelineサーバのクライアントがスキーマバージョンチェックを行う場合に破綻しうる)
- **deterministic/flaky**: deterministic
- **root cause**: **production code bug**
- **evidence**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:162-166`(他サーバとの実装比較は本レポート2章コマンド5関連の`grep`結果)

### FAIL-3: `test_timeout_boundary_fires_after_controlled_time` のモック不備
- **test**: `tests/test_lifecycle.py::TestStartHttpSubprocess::test_timeout_boundary_fires_after_controlled_time`
- **failure type**: `RuntimeError: coroutine raised StopIteration`(→ `pytest.raises(RuntimeError, match="did not become healthy")`のregexミスマッチ)
- **likely cause**: `time.monotonic`を`side_effect=[T, T+0.1, T+1.1]`で3回分のみモックしているが、`scripts/agent/http_lifecycle.py`のタイムアウト検出後、例外ハンドラ内(`scripts/agent/factory.py:169`の`self._failed_starts[server_key] = time.monotonic()`)でさらに1回`time.monotonic()`が呼ばれるため、モックの`side_effect`イテレータが枯渇し`StopIteration`が送出される。
- **severity**: Medium(本番コードの挙動自体は正しい可能性が高く、テストのモック設計ミス)
- **deterministic/flaky**: deterministic
- **root cause**: **test code bug**(`monotonic_values`に呼び出し回数分の値が不足)
- **evidence**: `tests/test_lifecycle.py:278-308`, `scripts/agent/factory.py:165-169`

### FAIL-4: `test_tool_schema.py` の存在しないモジュール参照 (2件)
- **test**: `tests/test_tool_schema.py::{test_config_dependent_field_present_and_requires_config_absent, test_static_schema_required_fields}[mcp_servers.git.tools-TOOL_LIST]`
- **failure type**: `ModuleNotFoundError: No module named 'mcp_servers.git.tools'`
- **likely cause**: コミット `ca6b7bfe`(2026-07-19, "refactor: rename MCP server files to eliminate duplicate filenames")で `mcp_servers/git/tools.py` → `mcp_servers/git/git_tools.py` にリネームされたが、`tests/test_tool_schema.py:25`の`_SCHEM_MODULES`リストが追随していない。
- **severity**: High(file-server/git-serverのTOOL_LIST静的スキーマ検証が2/4モジュールで機能していない)
- **deterministic/flaky**: deterministic
- **root cause**: **test code bug**(リネーム追随漏れ)
- **evidence**: `tests/test_tool_schema.py:22-26`, `git show --stat ca6b7bfe`

### 補足: Skip(13件)の内訳と扱い

| クラスタ | 件数 | 理由 | 分類 |
|---|---|---|---|
| `tests/test_db_consistency_detail.py` | 3 | "DbRagOps class no longer exists" | 削除すべき陳腐化テスト(dead test) |
| `tests/test_mcp_tools_validation.py` | 2 | "Server mcp_servers.cicd.cicd_server:8012 did not become healthy — possibly missing deps" | 環境依存(サブプロセス起動、CI環境依存の可能性) |
| `tests/test_lifecycle.py` | 4 | "source code cfg.cmd removed; skip until source fix" | 明示的なテスト債務(コメント上「修正待ち」と自認) |
| `tests/test_mdq_health_stale.py` | 3 | "Legacy test with broken variable refs (未定義変数)" | 壊れたまま放置された陳腐化テスト(`TestStaleDocumentCountNewSchema`に代替済みと明記) |
| `tests/test_mdq_health_endpoint.py` | 1 | "Requires FTS5 virtual table" | 正当な環境依存スキップ(要対応なし) |

---

## 4. Missing or Inconsistent Test Cases

以下、レイヤー別サブエージェント調査(read-only)の結果を集約。IDはレイヤー略称+連番。

### shared層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| SHARED-1 | Missing test coverage | `shared/json_utils.py`(全107行) | `extract_llm_content`の4分岐(choices欠落/型不一致等)を含め専用テストファイルが存在しない | `grep -rl shared.json_utils tests/`が`test_token_counter.py`のみ | Confirmed |
| SHARED-2 | Missing test coverage | `shared/config_utils.py:16-23`(`get_str`) | 型バリデーション付き共通アクセサが無テスト。agent/mcp_servers/rag/db複数から利用 | `grep -rl config_utils tests/`が0件 | Confirmed |
| SHARED-3 | Missing test coverage | `shared/llm_hot_config.py`(全58行) | `LlmHotConfigHandler.apply_config`/`apply_one`が無テスト。ホットリロード実処理経路 | `grep -rl LlmHotConfigHandler tests/`が0件 | Confirmed |
| SHARED-4 | Missing boundary-condition test | `shared/config_loader.py:92-105`(`load_all`) | 複数ファイルdictマージの衝突分岐が実質未検証・将来的な複数ファイル対応時のリスク | `_BASE_CONFIG_FILES`が1ファイルのみで実質未到達 | Needs confirmation |
| SHARED-5 | Missing boundary-condition test | `shared/config_loader.py:142-145`(`_resolve_path`) | 拡張子省略時`.toml`固定という非対称仕様が無検証 | テスト全件で`.json`拡張子明示 | Confirmed |
| SHARED-6 | Excessive mocking / Missing negative-path test | `shared/production_config_validator.py:29-58` | `known_tools=None`時のフォールバック(registry参照失敗を握り潰す)が全テスト未通過 | 全テストで`known_tools=`明示 | Confirmed |

### agent層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| AGENT-1 | Missing negative-path test | `agent/services/config_reload.py:447-453` | `security_profile`不正値時にValueErrorを握り潰し現状維持するフォールバック未検証 | grep該当テスト0件 | Confirmed |
| AGENT-2 | Missing boundary-condition test | `agent/memory/scoring.py:22-34`(`recency_boost`) | `age_days >= recency_days`の境界(ちょうど7日)未検証 | テスト名に境界ケースなし | Confirmed |
| AGENT-3 | Excessive mocking | `test_orchestrator.py`, `test_lifecycle.py` | `ctx`を`MagicMock()`で全面モック(70-80件規模)。実DB/実サブプロセス結合の非検知リスク | ファイル内モック使用箇所の網羅確認 | Confirmed |
| AGENT-4 | Missing negative-path test | `agent/tool_policy.py:110-131`(`_special_case_risk`) | `force/overwrite/clobber`が全ツール共通でHIGH昇格。read系ツールへの誤適用は未確認 | コードリーディング | Needs confirmation |
| AGENT-5 | Refactoring safety risk | `agent/http_lifecycle.py:341-394`(`shutdown_all`) | シグナルハンドラ差し替え/復元とtry/finally構造が複雑、実プロセス依存で再現性低 | コードリーディング | Needs confirmation |

### mcp_servers層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| MCP-1 | Missing test coverage(デッドコード疑い) | `mcp_servers/server.py:184-205`(`_ensure_error_tracking`, `_record_tool_error`) | 全MCPサーバ実装から呼び出し箇所が0件。テストも無し | `grep -rln "_record_tool_error"`該当なし | Needs confirmation |
| MCP-2 | Missing negative-path test | `mcp_servers/file/read_business.py:165-193`(`read_single_file`) | `stat()`がtry/except外にあり、TOCTOU的`OSError`が未捕捉のまま伝播。他メソッドはOSError捕捉済み | 同ファイル内比較 | Confirmed |
| MCP-3 | Missing test coverage | `mcp_servers/cicd/service_github_actions_job.py:156-189` | ジョブログ取得の非2xx fail-fastと`max_bytes`到達truncationの個別テストが見当たらない | grep結果 | Needs confirmation |
| MCP-4 | Missing boundary-condition test | `mcp_servers/file/delete_service.py:150-156` | ルート直下の重要ディレクトリ再帰削除への特別ガードなし(要件次第) | コードリーディング | Needs confirmation |

### rag層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| RAG-1 | 参考(誤指摘) | `rag/llm_client.py:72,85` | bandit B101はNoneチェック用assertで実害なし(pythonの`-O`実行時無効化リスクのみ) | コードリーディング | Confirmed(低リスク) |
| RAG-2 | Missing test coverage | `rag/llm_client.py:63-86` | URLキャッシュのフォールバック(config失敗時空文字列キャッシュ)とキャッシュ再利用挙動が未テスト | grep該当テストなし | Confirmed |
| RAG-4 | Weak assertion quality | `tests/test_rag_ingestion_pipeline.py:136-146` | `test_chunk_splitter_processes_json`がChunkSplitterを一切呼び出さずJSONキー存在確認のみ | テスト本文確認 | Confirmed |
| RAG-5 | Missing test coverage | `rag/ingestion/crawler.py:264-294,188-230,367-403` | HTTPリトライ/304スキップ/max_pages境界/BFSキュー/リンクフィルタが未テスト(coverage omit対象) | respx/AsyncClient使用箇所なし | Confirmed |
| RAG-6 | Missing integration test | omitされたingestion系一式 | 「integration testで別途検証」の方針記載に反し、実際のE2E統合テストが存在しない | `tests/integration/`に該当ファイルなし | Confirmed |

### db層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| DB-1 | Test/design inconsistency(設定不整合) | `pyproject.toml:118`coverage omit | 削除済みの`scripts/db/migrate.py`がomitリストに残存 | `git log --diff-filter=D`で削除確認 | Confirmed |
| DB-4 | 一貫性の欠如(低リスク) | `db/helper.py:36,276` | `PRAGMA busy_timeout=...`/`wal_checkpoint(...)`のf-string組立がnosec未注釈(値はホワイトリスト/int変換済みで実害なし) | コードリーディング | Confirmed |
| DB-5 | Missing boundary-condition test | `db/maintenance.py:143-151`(`purge_old_sessions`) | `len(rows) == cfg.max_sessions`ちょうどの境界テストが無い(off-by-one検知不能) | `test_db_maintenance.py`確認 | Confirmed |

### eventbus層

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| EVENTBUS-1 | **Refactoring safety risk / アーキテクチャ違反** | `eventbus/db.py:8`, `{ack,dlq,publish,replay,subscribe}_route.py` | `.importlinter`の`eventbus-is-isolated`契約違反。`db.helper`(コミット`d2067882`, 2026-07-12「PRAGMA設定の一元化」)と`shared.json_utils`(コミット`4bdcb014`/`381ba262`)への依存が、重複コード削減リファクタの副作用として意図せず混入。`rules/env.md`の「eventbus→他の全レイヤーから完全に独立」という設計方針とも矛盾。契約自体はEvent Bus基盤導入時(`6153338f`, 2026-06-22)からの当初設計であり、後付けではない | `git log -S`によるコミット追跡、`.importlinter`/`rules/env.md`の記述確認 | **Confirmed** |
| EVENTBUS-4 | Missing regression test | `eventbus/db.py:61-100`(`_migrate`) | 旧スキーマ(`retry_count`列)からの移行テストが存在しない。文字列マッチ判定(`"duplicate column name"`等)はSQLiteのエラーメッセージ変更に脆弱 | grep該当テストなし | Confirmed |
| EVENTBUS-5 | Missing recovery/fallback test | `eventbus/dlq.py:147-162`(`_atomic_write`) | 「JSON書き込み失敗時はDB行を更新しない」という一貫性保証が未テスト | `OSError`注入テストが見当たらない | Confirmed |

### 横断(コマンド実行から直接判明)

| ID | カテゴリ | 対象 | 説明 | 根拠 | 状態 |
|---|---|---|---|---|---|
| COV-1 | Missing test coverage | `mcp_servers/github/service_{file,issues,pull_requests,repository}.py`, `server_{file,issues,pull_requests,repository}.py` | GitHub MCPサーバのビジネスロジック一式が21〜47%カバレッジ(coverage omit対象外、本来検証されるべき層) | `coverage report`実測 | Confirmed |
| COV-2 | Missing test coverage | `agent/commands/memory_data_ops.py`(12%, radon D(23)), `agent/workflow/validate.py`(0%), `mcp_launcher.py`(0%) | 複雑度が高い、または完全に未実行の本番コードパス | `coverage report` + `radon cc`実測 | Confirmed |
| CI-1 | Environment dependency problem / Test/design inconsistency | `.github/workflows/ci.yml`(`branches:[main]`), `rules/toolchain.md`(`--compare-branch=main`) | `main`ブランチがリポジトリに存在しない(実際は`master`)。diff-coverはローカルで即エラー、CIのpush/PRトリガーも発火しない可能性 | `git branch -a`実測、`diff-cover`実行エラー | **Confirmed** |
| SEC-1 | Existing test failure(環境的側面あり) | `pyproject.toml`(bandit設定なし) | banditが8件のB608(false positive)により現状fail。`# nosec`注釈がないため機械的に検出され続ける | 2.1節参照 | Confirmed |
| ARCH-1 | Test/code inconsistency | `tests/test_rag_tools_consistency.py` | FAIL-1と同一。ToolRouteResolverのAPI変更にテストが追随していない | 3章参照 | Confirmed |

---

## 5. Implementation Task List (High / Medium / Low)

### High Priority

**TASK-H1: `test_rag_tools_consistency.py` をToolRouteResolverの現行API(RuntimeToolRegistry注入モデル)に合わせて書き換える**
- Goal: RAGツール登録の整合性検証を復旧する
- Concrete actions:
  1. `tests/test_rag_tools_consistency.py`の`_get_rag_tools_in_registry()`を、`RuntimeToolRegistry`を構築し`ToolRouteResolver(..., runtime_registry=registry)`経由で`resolver.resolve(tool_name)`を呼ぶ形に書き換える(直接`_registry`/`_runtime_registry`という内部属性に触れない)
  2. 実際の本番起動経路(`/v1/tools`ディスカバリ結果)を模したfixtureを用意し、5テスト全てを新APIで再実装
- Acceptance criteria: 5テスト全てpass、かつテストが実際に「RAGツールが解決可能である」ことを検証している(クラッシュで無検証になっていない)ことをレビューで確認
- Definition of Done: `uv run pytest tests/test_rag_tools_consistency.py -v`がpass / 既存の他テストに新規失敗なし / mypy・ruffクリーン
- Main affected files: `tests/test_rag_tools_consistency.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_rag_tools_consistency.py -v`, `uv run pytest -q`

**TASK-H2: rag_pipeline `/v1/tools`に`schema_version`を追加**
- Goal: 全MCPサーバでツールディスカバリ応答のスキーマを統一する
- Concrete actions: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:163`の`list_tools()`を、他サーバ同様`build_tools_response()`(`mcp_servers/server.py:225`)または同等のパターンで`schema_version`を付与するよう修正
- Acceptance criteria: `test_schema_version_present[...rag_pipeline]`がpass。既存の`/v1/tools`利用側(RAG pipelineクライアント)に破壊的変更が無いことを確認
- Definition of Done: 該当テストpass、`uv run pytest -q`で新規失敗なし、mypy/ruffクリーン
- Main affected files: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
- Dependencies: なし
- Validation: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

**TASK-H3: `test_lifecycle.py::test_timeout_boundary_fires_after_controlled_time`のモック不足を修正**
- Goal: タイムアウト境界テストを正しく機能させる
- Concrete actions: `monotonic_values`に、例外ハンドラ内の`time.monotonic()`呼び出し分(1回以上)を追加した値を渡す。実装側(`http_lifecycle.py`/`factory.py`)の`time.monotonic()`呼び出し回数を数え、必要十分な`side_effect`長を用意
- Acceptance criteria: `pytest.raises(RuntimeError, match="did not become healthy")`がStopIterationではなく期待通りの例外で通ること
- Definition of Done: 該当テストpass、他のtest_lifecycle.pyテストに影響なし
- Main affected files: `tests/test_lifecycle.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_lifecycle.py -v`

**TASK-H4: `test_tool_schema.py`のモジュールパスを`mcp_servers.git.git_tools`に修正**
- Goal: file/git-server TOOL_LISTスキーマ検証を復旧
- Concrete actions: `tests/test_tool_schema.py:25`の`("mcp_servers.git.tools", "TOOL_LIST")`を`("mcp_servers.git.git_tools", "TOOL_LIST")`に修正。他の3エントリ(file.read_tools等)がリネーム済み命名規則に合っているか併せて確認
- Acceptance criteria: 2テストともpass
- Definition of Done: `uv run pytest tests/test_tool_schema.py -v`がpass
- Main affected files: `tests/test_tool_schema.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_tool_schema.py -v`

**TASK-H5: eventbusのレイヤー独立性違反を解消する**
- Goal: `.importlinter`の`eventbus-is-isolated`契約を再びKEEPさせる
- Concrete actions:
  1. `db.helper.apply_connection_pragmas`相当の軽量関数(PRAGMA適用のみ)を`eventbus`内に複製する(例: `eventbus/db.py`内にprivateヘルパーとして実装)
  2. `shared.json_utils`の`now_iso`/`dumps`(eventbusが使う2関数のみ)を同様に複製する
  3. `eventbus/db.py`, `ack_route.py`, `dlq.py`, `publish_route.py`, `replay_route.py`, `subscribe_route.py`のimportを複製実装に切り替える
- Acceptance criteria: `PYTHONPATH=scripts uv run lint-imports`が5契約すべてKEEP
- Definition of Done: lint-imports pass、既存eventbusテスト全てpass、複製関数に対する最小限のユニットテスト追加
- Main affected files: `scripts/eventbus/db.py`, `ack_route.py`, `dlq.py`, `publish_route.py`, `replay_route.py`, `subscribe_route.py`
- Dependencies: なし。ただしEVENTBUS-4(マイグレーションガードテスト、TASK-M5)と同一ファイル(`db.py`)を触るため実施順序に注意
- Validation: `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest tests/test_eventbus*.py -v`

**TASK-H6: `.github/workflows/ci.yml`と`rules/toolchain.md`のブランチ名を実態(`master`)に合わせる、またはリポジトリに`main`ブランチを作成する方針を決定する**
- Goal: CIが実際にpush/PRで発火し、diff-coverゲートが機能する状態に戻す
- Concrete actions: 方針決定が必要(下記8章「Additional Confirmation Items」参照)。決定後、`.github/workflows/ci.yml`の`branches:[main]`と`rules/toolchain.md`/CIの`--compare-branch=main`を`master`に統一するか、リポジトリのデフォルトブランチを`main`に変更してリネームする
- Acceptance criteria: `uv run diff-cover coverage.xml --compare-branch=<正しいブランチ名>`がローカルで実行可能。GitHub上でpush/PRに対しCIが実際に起動することを確認
- Definition of Done: CI設定とドキュメントの記述が実際のブランチ名と一致、diff-coverがローカル/CI双方で実行可能
- Main affected files: `.github/workflows/ci.yml`, `rules/toolchain.md`
- Dependencies: 人間による方針確認(Needs confirmation)
- Validation: `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`(暫定確認用)

**TASK-H7: bandit B608(false positive)8件に`# nosec B608`注釈を追加し、CIのSecurity scanをgreenに戻す**
- Goal: `uv run bandit -r scripts/ -c pyproject.toml`をexit 0にする
- Concrete actions: 2.1節の8箇所全てに、`scripts/db/maintenance.py:148`等の既存nosec注釈と同じ形式(理由コメント付き)で`# nosec B608 - ...`を追加。B101(assert_used, 14件)・B104・B105/B107・B404についても、既に許容されている設計判断か再確認し、必要な箇所にのみ注釈を追加(むやみに全件抑制しない)
- Acceptance criteria: `uv run bandit -r scripts/ -c pyproject.toml`がexit 0(medium/high issue 0件)
- Definition of Done: bandit pass、注釈追加のみで実装ロジック変更なし、既存テスト全てpass
- Main affected files: `scripts/eventbus/db.py`, `subscribe_route.py`, `scripts/mcp_servers/mdq/{db_grep,health_check,mdq_service,search}.py`
- Dependencies: なし
- Validation: `uv run bandit -r scripts/ -c pyproject.toml`

**TASK-H8: GitHub MCPサービス層(`service_{file,issues,pull_requests,repository}.py`ほか)にユニットテストを追加**
- Goal: 21〜47%という低カバレッジのGitHub MCPビジネスロジックに主要な正常系・異常系テストを追加する
- Concrete actions: 各`service_*.py`の公開メソッドについて、成功パス・GitHub API異常応答(4xx/5xx)・認可失敗パスの最小テストを追加。既存の`test_github_mcp_service.py`の構成パターンを踏襲
- Acceptance criteria: 対象ファイル群のカバレッジが最低70%以上に到達
- Definition of Done: 新規テストpass、`diff-cover`(TASK-H6解決後)で当該変更行のカバレッジ90%以上
- Main affected files: `tests/test_github_mcp_service.py`(拡張)、対象: `scripts/mcp_servers/github/service_*.py`, `server_*.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_github_mcp_service.py -v`, `uv run coverage report`

### Medium Priority

**TASK-M1: `shared/json_utils.py`・`config_utils.py`・`llm_hot_config.py`に専用ユニットテストを新設**
- Goal: 全レイヤーから使われる共通コードの無防備状態を解消
- Concrete actions: `tests/shared/test_json_utils.py`(`extract_llm_content`の4分岐含む全関数)、`config_utils.py`の`get_str`型不一致テスト、`tests/shared/test_llm_hot_config.py`(9フィールドの適用/非適用)を新設
- Acceptance criteria: 各ファイルの主要関数に正常系+異常系テストが存在
- Definition of Done: 新規テストpass、カバレッジがSHARED-1/2/3対象ファイルで80%以上
- Main affected files: `tests/shared/test_json_utils.py`(新設), 既存`test_config_loader.py`拡張
- Dependencies: なし
- Validation: `uv run pytest tests/shared/ -v`

**TASK-M2: `eventbus/db.py`のスキーマ移行(`_migrate`)にガードテストを追加**
- Goal: 旧スキーマ→新スキーマ移行のリグレッション検知
- Concrete actions: 旧スキーマ(`retry_count`列あり)のSQLiteファイルをfixtureとして用意し、`_migrate`実行後に新カラム(`delivery_failure_count`, `dlq_requeue_count`)が正しく存在すること、既存データが失われないことを検証
- Acceptance criteria: 新規テストpass
- Definition of Done: TASK-H5実施前に完了していることが望ましい(下記7章参照)
- Main affected files: `tests/test_eventbus_db_migration.py`(新設)
- Dependencies: TASK-H5より先に実施推奨
- Validation: `uv run pytest tests/test_eventbus_db_migration.py -v`

**TASK-M3: `rag/ingestion/crawler.py`のリトライ/304/max_pages/リンクフィルタにrespxベースのテストを追加**
- Goal: coverage omit対象だが実質未テストのcrawlerロジックを最低限保護する
- Concrete actions: respxまたはhttpx MockTransportで304スキップ、リトライ、max_pages到達、外部リンクフィルタの4ケースを追加
- Acceptance criteria: 4ケース全てpass
- Definition of Done: 新規テストpass、既存ingestionテストに影響なし
- Main affected files: `tests/test_crawler_retry_boundary.py`(新設)
- Dependencies: なし
- Validation: `uv run pytest tests/test_crawler_retry_boundary.py -v`

**TASK-M4: `tests/test_rag_ingestion_pipeline.py`の弱いアサーション(RAG-4)を実処理検証に置き換える**
- Goal: `ChunkSplitter`の実出力を検証する
- Concrete actions: `test_chunk_splitter_processes_json`を実際に`ChunkSplitter(config).process_file()`を呼び出し、生成chunkの内容を検証する形に修正
- Acceptance criteria: テストがChunkSplitterのMarkdown見出し分割ロジックを実際に踏む
- Definition of Done: 修正後テストpass
- Main affected files: `tests/test_rag_ingestion_pipeline.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_rag_ingestion_pipeline.py -v`

**TASK-M5: `db/maintenance.py`の`purge_old_sessions`に境界値テスト追加(DB-5)**
- Goal: `len(rows) == cfg.max_sessions`ちょうどのoff-by-oneリグレッション検知
- Concrete actions: 境界値ケースを`test_db_maintenance.py`に追加
- Acceptance criteria: 新規テストpass
- Definition of Done: 既存テストと合わせてpass
- Main affected files: `tests/test_db_maintenance.py`
- Dependencies: なし
- Validation: `uv run pytest tests/test_db_maintenance.py -v`

**TASK-M6: 陳腐化テストの削除・整理**
- Goal: `test_db_consistency_detail.py`(DbRagOps不在)・`test_mdq_health_stale.py`の壊れたレガシーケース(3件)を削除しテストスイートを整理
- Concrete actions: skip理由が「クラスが存在しない」「未定義変数を含むレガシーテスト」である7件を削除(代替テストが既に存在することを確認済み: `TestStaleDocumentCountNewSchema`)
- Acceptance criteria: 削除後もカバレッジが低下しないこと
- Definition of Done: `uv run pytest -q`の総件数が意図通り減少し、pass件数に影響なし
- Main affected files: `tests/test_db_consistency_detail.py`, `tests/test_mdq_health_stale.py`
- Dependencies: なし
- Validation: `uv run pytest -q`, `uv run coverage report`(対象ファイルのカバレッジ低下がないか確認)

### Low Priority

**TASK-L1: `ruff check`の4件(import未整列)を`--fix`で解消しコミット**
- Goal: `ruff check scripts/`をクリーンにする
- Concrete actions: `uv run ruff check scripts/ --fix`を実行しレビュー後コミット(本監査で確認済みの3ファイル・4箇所のみ)
- Acceptance criteria: `ruff check`が0エラー
- Definition of Done: pre-commitのruffフックがdiffなしでPassする
- Main affected files: `scripts/mcp_servers/cicd/cicd_server.py`, `service_business.py`, `scripts/mcp_servers/github/github_server.py`
- Dependencies: なし
- Validation: `uv run ruff check scripts/`, `uv run pre-commit run --all-files`

**TASK-L2: pyright 29件の要否確認**
- Goal: mypyとpyrightの検出差分(FastAPI Protocol不一致、GitPython動的属性)を精査し、型スタブ改善または`# type: ignore`要否を判断
- Concrete actions: 12ファイルの各エラーを確認し、真の型不整合と型スタブ限界によるfalse positiveを仕分け
- Acceptance criteria: 判断結果をドキュメント化(対応する/しないを明示)
- Definition of Done: 対応方針決定、必要な修正のみ実施
- Main affected files: 2章コマンド4に列挙の12ファイル
- Dependencies: なし
- Validation: `uv run pyright scripts/`

**TASK-L3: `pyproject.toml`のcoverage omitから削除済み`scripts/db/migrate.py`エントリを除去(DB-1)**
- Goal: 設定の陳腐化解消
- Concrete actions: `pyproject.toml`の該当行を削除
- Acceptance criteria: coverage設定に実在しないファイルへの参照がない
- Definition of Done: `uv run coverage report`が変わらず動作
- Main affected files: `pyproject.toml`
- Dependencies: なし
- Validation: `uv run coverage run -m pytest tests/ && uv run coverage report`

**TASK-L4: vulture/semgrep/pip-auditの定期実行導入検討**
- Goal: デッドコード・意味的パターン・依存脆弱性の継続監視
- Concrete actions: CIまたは定期ジョブへの追加要否を検討(今回はスコープ外につき未実施)
- Acceptance criteria: 導入方針の決定
- Definition of Done: 方針文書化
- Main affected files: `.github/workflows/ci.yml`(要否検討)
- Dependencies: なし
- Validation: `uv run vulture scripts/ --min-confidence 80`等の試験実行

---

## 5.5 Refactoring Safety Assessment

| Component | Classification | Evidence | Refactoring blockers | Required guard tests | Risk if refactored now | Recommended next action |
|---|---|---|---|---|---|---|
| `agent/tool_policy.py` | **Refactor-ready** | 純粋関数中心、DI容易、44+36+36件のテスト | なし | 不要 | 低 | そのまま着手可 |
| `shared/formatters.py` | **Refactor-ready** | `test_formatters.py`(96行)で境界値網羅済み | なし | 不要 | 低 | そのまま着手可 |
| `mcp_servers/dispatch.py` | **Refactor-ready** | fail-open昇格なし、9件のテストで契約固定化済み | なし | 不要 | 低 | そのまま着手可 |
| `mcp_servers/{git_security,github/service_security,cicd/service_guards,mdq/auth}.py` | **Refactor-ready** | fail-closed設計、正常系/拒否系/境界が網羅的 | なし | 不要 | 低 | そのまま着手可 |
| `db/schema_sql.py` | **Refactor-ready** | DDL/マイグレーションのidempotency・エラー伝播が厚くカバー | なし | 不要 | 低 | そのまま着手可 |
| `agent/tool_loop_guard.py` | Refactor-with-guard-tests | ロジック単純だが`ctx.cfg.tool.*`への暗黙依存 | 設定値0/負値境界の未検証 | 境界値characterization test | 中 | ガードテスト追加後に着手 |
| `shared/config_validator.py` / `production_config_validator.py` | Refactor-with-guard-tests | テストは手厚いが`known_tools`省略時フォールバック(SHARED-6)未検証 | 同上 | フォールバック分岐テスト | 中 | ガードテスト追加後に着手 |
| `eventbus/{ack_route,dlq}.py`(promote系) | Refactor-with-guard-tests | 閾値到達・requeue・二重昇格防止テストは充実だが`_atomic_write`失敗系(EVENTBUS-5)未検証 | 同上 | 書き込み失敗時DB非更新テスト | 中 | ガードテスト追加後に着手 |
| `db/helper.py` | Refactor-with-guard-tests | begin_immediate/exclusiveロールバック分岐、reuse_connection状態管理が変更に弱い | 例外時ROLLBACK/reuse_connection挙動未検証 | 例外注入テスト | 中 | ガードテスト追加後に着手 |
| `rag/ingestion/chunk_splitter.py`+`chunk_english/japanese.py` | Refactor-with-guard-tests | 境界値(merge_text_items)は良好だが実処理経路(process_file全体)はRAG-4により弱い | 実出力未検証 | process_file()の実出力検証 | 中 | TASK-M4実施後に着手 |
| `agent/orchestrator.py` | **High-risk-refactor** | 500行超、深いネスト、状態ミューテーション散在、テストが全面MagicMock | 実結合検証皆無 | DB/WorkflowEngine結合を含むintegration characterization test | 高 | ガードテスト追加まで着手しない |
| `agent/http_lifecycle.py` | **High-risk-refactor** | OS/シグナル/サブプロセス副作用が濃密、DI困難、隠れたグローバル状態(`signal.signal`) | プロセスライフサイクル全体のintegrationテストが前提 | 既存integrationテストの維持+FAIL-3修正 | 高 | ガードテスト追加まで着手しない |
| `shared/config_loader.py`(`ConfigLoader`) | **High-risk-refactor** | 全レイヤーから直接利用、`restrict_to()`がクラス変数によるグローバル状態、テストでmonkeypatchリセット必須なほど副作用強い | 複数ファイルマージ順序・`restrict_to`未リセット汚染防止・拡張子解決分岐 | SHARED-4/5のガードテスト | 高 | ガードテスト追加まで着手しない |
| `eventbus/db.py`(スキーマ初期化・マイグレーション) | **High-risk-refactor** | 旧スキーマ移行のリグレッション検知不可(EVENTBUS-4) | 移行再現テストなし | TASK-M2 | 高 | TASK-M2完了後に着手(TASK-H5と同一ファイルのため順序注意) |
| `rag/ingestion/crawler.py`(WebCrawler) | **High-risk-refactor** | coverage omit対象、非同期リトライ/BFS/フィルタが実質未テスト(RAG-5) | respxベーステストなし | TASK-M3 | 高 | TASK-M3完了後に着手 |
| `shared/json_utils.py` | Needs confirmation | ロジックは単純だが専用テスト皆無(SHARED-1) | 「安全に見えるが守られているか不明」 | TASK-M1 | 不明(要ガード追加で再評価) | TASK-M1完了後に再評価 |
| `shared/llm_hot_config.py` | **High-risk-refactor** | テスト皆無(SHARED-3)、本番ホットリロード経路に直結 | フィールド適用漏れが即座に本番挙動へ影響 | TASK-M1 | 高 | TASK-M1完了後に着手 |
| `agent/services/config_reload.py` | Needs confirmation | 分岐は多いが構造は単純、`security_profile`フォールバック未検証(AGENT-1) | 同上 | AGENT-1対応 | 中 | ガードテスト追加後に再評価 |

---

## 6. Test Cases to Add or Update

以下は主要なもののみ抜粋(全件は5章の各TASKに対応)。

**TC-1** / 関連: FAIL-1(TASK-H1) / 対象: `shared/route_resolver.py`(RAGツール登録) / type: regression
- 目的: `RuntimeToolRegistry`注入モデルでRAGツール(`rag_run_pipeline`, `rag_delete_document`, `rag_list_documents`, `rag_debug_pipeline`)が解決可能であることを検証
- Setup: `RuntimeToolRegistry`にRAGツール一式を登録したfixtureを構築
- Input/condition: 各RAGツール名で`resolver.resolve(name)`を呼ぶ
- Expected: `"rag_pipeline"`(または対応するserver_key)が返る
- Negative path: 未登録ツール名で`ValueError`
- Required fixtures: `RuntimeToolRegistry`構築ヘルパー
- Why necessary: 現在この検証が完全に欠落しているため(FAIL-1)
- Acceptance criteria: 5テスト全てpass、クラッシュではなく意味のある検証として機能

**TC-2** / 関連: FAIL-2(TASK-H2) / 対象: `rag_pipeline_server.py` / type: unit
- 目的: `/v1/tools`が`schema_version`を含むことを検証(既存テストで検証済みだが実装修正後の再確認)
- Setup: FastAPI TestClient
- Input/condition: GET `/v1/tools`
- Expected: レスポンスに`schema_version`キーが存在し`MCP_TOOL_SCHEMA_VERSION`と一致
- Required fixtures: 既存`test_mcp_tool_discovery.py`のfixtureを再利用
- Why necessary: 本番コードのスキーマ契約違反を防止
- Acceptance criteria: 既存テストがそのままpass

**TC-3** / 関連: SHARED-1(TASK-M1) / 対象: `shared/json_utils.py::extract_llm_content` / type: unit
- 目的: 4分岐(choices欠落、type不一致複数パターン)全てを検証
- Setup: 各種不正形状のLLMレスポンスdictを用意
- Input/condition: choices欠落/message型不一致/content型不一致の各ケース
- Expected: 正常系は文字列抽出、異常系は`ValueError`
- Boundary condition: 空choicesリスト
- Required fixtures: なし(純粋関数)
- Why necessary: 現状専用テストがゼロ(SHARED-1)
- Acceptance criteria: 4分岐全てにテストケースが存在しpass

**TC-4** / 関連: EVENTBUS-4(TASK-M2) / 対象: `eventbus/db.py::_migrate` / type: regression
- 目的: 旧スキーマ(`retry_count`列あり)から新スキーマへの移行が正しく完了することを検証
- Setup: 旧スキーマDDLで初期化したSQLiteファイルをfixtureとして用意
- Input/condition: `_migrate`実行
- Expected: `delivery_failure_count`/`dlq_requeue_count`列が追加され、既存データが保持される
- Negative path: 移行中の例外発生時にDBが破損しないこと
- Required fixtures: 旧スキーマDDL定数
- Why necessary: 現状この移行パスは完全に未検証(EVENTBUS-4)
- Acceptance criteria: 新規テストpass、既存データの非破壊を確認

**TC-5** / 関連: RAG-5(TASK-M3) / 対象: `rag/ingestion/crawler.py::_fetch_html_async` / type: unit
- 目的: HTTPリトライ・304スキップ・max_pages境界・リンクフィルタを検証
- Setup: respxで503→200のリトライシーケンス、304レスポンス、max_pages=1の設定
- Input/condition: 4パターンそれぞれ
- Expected: リトライ回数上限順守、304時はスキップしてcrawled setに追加しない、max_pages到達で打ち切り
- Boundary condition: max_pagesちょうど到達時
- Required fixtures: respx mock
- Why necessary: 現状これらの分岐は完全に未テスト(RAG-5)
- Acceptance criteria: 4ケース全てpass

**TC-6** / 関連: DB-5(TASK-M5) / 対象: `db/maintenance.py::purge_old_sessions` / type: unit
- 目的: `len(rows) == cfg.max_sessions`境界でのoff-by-one検証
- Setup: `max_sessions`と同数のセッション行を用意
- Input/condition: `purge_old_sessions`実行
- Expected: 削除件数0(境界値では削除しない、または削除する—仕様通りの1択を明示)
- Boundary condition: `max_sessions - 1`, `max_sessions`, `max_sessions + 1`の3点
- Required fixtures: 既存`test_db_maintenance.py`のfixture
- Why necessary: 現状ちょうど境界のケースが無い
- Acceptance criteria: 3点のテストが追加されpass

---

## 7. Recommended Execution Order

1. **即時(ブロッキング、他作業と独立)**: TASK-H1〜H4(9件の既存テスト失敗の解消)。いずれも独立したファイルの修正で相互依存なし。並行実施可能。
2. **即時(可観測性回復)**: TASK-H7(bandit nosec注釈)。CIのSecurity scanをgreenに戻す。他タスクと独立。
3. **方針決定が先行するもの**: TASK-H6(main/masterブランチ不整合)。人間の判断が必要なため、決定後に着手。決定後はdiff-coverが機能し、以降のカバレッジ関連タスクの効果測定が可能になる。
4. **ガードテスト→リファクタの順序が必須なもの**:
   - TASK-M2(eventbus移行ガードテスト) → **その後に** TASK-H5(eventbusレイヤー独立性修正)。理由: TASK-H5は`eventbus/db.py`の依存を切り離す変更であり、移行ロジック自体には触れない見込みだが、同一ファイルへの変更が重なるため、先にリグレッション検知手段(TASK-M2)を用意してからTASK-H5を実施する方が安全。
   - TASK-M3(crawlerガードテスト) → その後に crawler.pyのリファクタ(本レポートでは未提案だが、High-risk-refactor判定のため将来のリファクタ提案時はこの順序を厳守)
   - TASK-M1(shared共通コードのガードテスト) → その後に`config_loader.py`/`llm_hot_config.py`のリファクタ(同上、未提案だが順序を明記)
5. **並行実施可能な中位優先度**: TASK-M4, M5, M6(テスト品質改善、他タスクと独立)
6. **後回しでよいクリーンアップ**: TASK-L1〜L4(ruff自動修正、pyright精査、coverage設定清掃、追加静的解析導入検討)

---

## 8. Additional Confirmation Items Needed

- **TASK-H6の方針**: `main`ブランチを新設してリポジトリのデフォルトブランチとするか、CI設定・`rules/toolchain.md`の記述を`master`に統一するか、人間の判断が必要。GitHub側のブランチ保護設定・既存PRへの影響も要確認。
- **EVENTBUS-1の対応方針**: 本レポートでは「eventbus内に複製実装する」ことを推奨したが、代替案として「`.importlinter`/`rules/env.md`を更新し依存を正式に許容する」という選択肢もある。アーキテクチャ方針の最終決定は人間が行うべき(TASK-H5参照)。
- **MCP-1(`_record_tool_error`系のデッドコード疑い)**: 将来使用予定で残しているのか、削除すべきデッドコードなのか実装者への確認が必要。
- **AGENT-4(force/overwriteフラグの全ツール共通HIGH昇格)**とMCP-4(delete_directoryの重要ディレクトリ再帰削除ガード欠如)は意図した仕様か要件確認が必要。
- **TASK-H8のカバレッジ目標値(70%)**は暫定値。GitHub MCPサーバの利用頻度・重要度に応じて人間がSLA的な目標値を設定するのが望ましい。
- **TASK-L2(pyright 29件)**: mypyとの検出差分をどこまで追及するか(CIゲートに追加するか、現状のcross-validate用途に留めるか)は方針確認が必要。

---

## Mutation Testing Candidates

| Candidate ID | Target module | Reason | Risk addressed | Suggested initial scope | Priority | Related finding IDs |
|---|---|---|---|---|---|---|
| MUT-1 | `mcp_servers/mdq/auth.py::authorize_path` | `startswith(str(resolved_root) + os.sep)`の`+ os.sep`除去ミューテーションで`/opt/repos-evil`が`/opt/repos`のprefixにマッチする典型的脆弱性パターンを検知できるか | パストラバーサル認可バイパス | `+ os.sep`除去/`startswith`→`in`変異体の生存確認 | High | MCP-2関連 |
| MUT-2 | `mcp_servers/{git_security,github/service_security,cicd/service_guards}.py`の`if not allowed:`系fail-closed分岐 | 反転(`if allowed:`)ミューテーションが最も実害大きい権限系判定 | 権限昇格・不正アクセス許可 | 空リスト/None/1要素の3境界 | High | 4章mcp_servers層 |
| MUT-3 | `eventbus/ack_route.py:89`の`failure_count >= cfg.max_retry`境界 | ちょうどmax_retry到達時のDLQ昇格判定はコア仕様 | 誤ったDLQ昇格タイミング | 境界値ちょうど/1手前/1超過の3点 | High | EVENTBUS-1関連 |
| MUT-4 | `rag/ingestion/chunk_utils.py::merge_text_items`の境界比較演算子 | min_chunk/max_chunk/overlap境界のoff-by-one | チャンク分割の誤り(検索精度低下に直結) | 境界値ちょうどのテスト追加 | High | RAG-5 |
| MUT-5 | `shared/json_utils.py::extract_llm_content`のisinstance連鎖(4条件) | 現状無テストにつき変異体が容易に生存 | LLM応答パース失敗の見逃し | TASK-M1完了後に実施 | High | SHARED-1 |
| MUT-6 | `mcp_servers/dispatch.py::dispatch_tool`の`except ValueError`→`except Exception`変異 | fail-fast/fail-open境界の崩壊検知 | 意図しない例外握り潰し | 既存9テストで生存しないか確認 | High | MCP層全般 |
| MUT-7 | `mcp_servers/mdq/parser.py::parse_markdown`(radon E(40)) | 複雑度E評価、分岐が非常に多く変異体が生存しやすい | Markdown解析の誤り | 高複雑度関数の分割前にmutmut等で生存率計測 | Medium | 2章radon結果 |
| MUT-8 | `agent/commands/memory_data_ops.py::memory_list`(radon D(23), coverage 12%) | 複雑度と低カバレッジの重複箇所、最もリグレッションに弱い | メモリ管理コマンドの誤動作 | TASK-M1範囲外、別途カバレッジ向上後に実施 | Medium | COV-2 |
| MUT-9 | `db/maintenance.py::purge_old_sessions`の`rows[cfg.max_sessions:]`スライス境界 | DB-5と対応するoff-by-one | セッション削除件数の誤り | TASK-M5完了後に実施 | Medium | DB-5 |
| MUT-10 | `shared/config_loader.py::load_all`の`isinstance(val, dict) and isinstance(merged.get(key), dict)` | 複合条件、境界不到達の懸念(SHARED-4) | 設定マージ衝突の誤処理 | TASK-M1完了後、複数config対応時に実施 | Medium | SHARED-4 |

---

## 9. GitHub Issue Drafts (English, AI-oriented)

### Issue 1: Fix outdated `ToolRouteResolver` API usage in `test_rag_tools_consistency.py`

**Title**: Fix `AttributeError: 'ToolRouteResolver' object has no attribute '_registry'` in RAG tool registry consistency tests

**Summary**: 5 tests in `tests/test_rag_tools_consistency.py` crash with `AttributeError` because `ToolRouteResolver` was refactored to use a `RuntimeToolRegistry`-injection model (`_runtime_registry`), but the tests still reference the removed `_registry` attribute.

**Background**: `ToolRouteResolver` (`scripts/shared/route_resolver.py`) previously exposed a static internal `_registry`. It was refactored so that routing is resolved solely via an injected `RuntimeToolRegistry` (populated from live `/v1/tools` discovery), accessible as `self._runtime_registry`. `tests/test_rag_tools_consistency.py` was not updated.

**Problem**: `TestRagToolsInRegistry._get_rag_tools_in_registry()` constructs `ToolRouteResolver(server_configs={}, discovery_map=None, strict_mode=False)` (no `runtime_registry` passed) and then accesses `resolver._registry.get_all_tool_names()`, which raises `AttributeError`. As a result, RAG tool registration is currently **not validated at all** by this test file.

**Evidence**: `tests/test_rag_tools_consistency.py:20`; `scripts/shared/route_resolver.py:59-124` (constructor signature and `resolve()`/`_lookup_runtime_registry()` implementation).

**Required Changes**: Rewrite `_get_rag_tools_in_registry()` (and the 5 test methods that use it) to build a `RuntimeToolRegistry` fixture populated with the RAG tool set, inject it via `ToolRouteResolver(..., runtime_registry=registry)`, and assert via `resolver.resolve(tool_name)` returning the expected server key (not by reaching into a private `_registry`/`_runtime_registry` attribute).

**Acceptance Criteria**: All 5 tests in `tests/test_rag_tools_consistency.py` pass and genuinely exercise tool resolution (i.e., they fail if a RAG tool is missing from the registry fixture).

**Definition of Done**: `uv run pytest tests/test_rag_tools_consistency.py -v` passes; `uv run pytest -q` shows no new failures; `uv run ruff check scripts/ tests/` and `uv run mypy scripts/` remain clean.

**Validation Commands**: `uv run pytest tests/test_rag_tools_consistency.py -v`, `uv run pytest -q`

**Out of Scope**: Do not modify `ToolRouteResolver` itself; this is a test-only fix.

**AI Implementation Instruction**: Read `scripts/shared/route_resolver.py` in full to understand the current `RuntimeToolRegistry` injection contract before touching the test file. Do not reintroduce any reference to a private `_registry` attribute.

---

### Issue 2: `rag_pipeline` MCP server `/v1/tools` response is missing `schema_version`

**Title**: Add `schema_version` to rag_pipeline `/v1/tools` response to match all other MCP servers

**Summary**: `test_schema_version_present[...rag_pipeline]` fails because `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`'s `list_tools()` hand-builds its response dict without the `schema_version` key that every other MCP server includes.

**Background**: Every other MCP server (`git_server.py`, `file/*_server.py`, `shell_server.py`, `mdq_server.py`, base class `MCPServer.build_tools_response()` in `scripts/mcp_servers/server.py:225`) returns `{"schema_version": MCP_TOOL_SCHEMA_VERSION, "tools": [...]}`. `rag_pipeline_server.py` returns only `{"tools": [...]}`.

**Problem**: MCP tool discovery clients relying on `schema_version` presence for all servers will fail or behave inconsistently against `rag_pipeline`.

**Evidence**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:162-166`; contrast with `scripts/mcp_servers/git/git_server.py:92-104`, `scripts/mcp_servers/server.py:225-235`.

**Required Changes**: Modify `rag_pipeline_server.py`'s `list_tools()` to include `schema_version` (reuse the shared `build_tools_response()` pattern/helper if applicable, rather than hand-rolling the dict).

**Acceptance Criteria**: `test_schema_version_present[mcp_servers.rag_pipeline.rag_pipeline_server-app-rag_pipeline]` passes.

**Definition of Done**: Target test passes; `uv run pytest -q` shows no new failures; mypy/ruff clean; no other MCP server's discovery contract regresses.

**Validation Commands**: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`, `uv run pytest -q`

**Out of Scope**: Do not change the tool list contents themselves, only the response envelope.

**AI Implementation Instruction**: Compare against `git_server.py`'s `list_tools()` implementation as the reference pattern before editing.

---

### Issue 3: Fix insufficient `time.monotonic` mock in `test_lifecycle.py::test_timeout_boundary_fires_after_controlled_time`

**Title**: Fix `StopIteration`/regex-mismatch failure in HTTP subprocess timeout-boundary test

**Summary**: The test mocks `time.monotonic` with a 3-value `side_effect` list, but the code path under test (including its exception handler) calls `time.monotonic()` more than 3 times, exhausting the mock and raising `StopIteration` instead of the expected `HttpStartupError`/`RuntimeError`.

**Background**: `scripts/agent/factory.py:169` calls `time.monotonic()` inside the exception handler after `http_lifecycle.py`'s `start()` raises `HttpStartupError`. The test's `monotonic_values = [T, T + 0.1, T + 1.1]` does not account for this extra call.

**Problem**: `pytest.raises(RuntimeError, match="did not become healthy")` fails because the actual exception message is `"coroutine raised StopIteration"`, masking whatever the real timeout behavior would produce.

**Evidence**: `tests/test_lifecycle.py:278-308`; `scripts/agent/factory.py:165-169`; `scripts/agent/http_lifecycle.py:306`.

**Required Changes**: Extend `monotonic_values` (or switch to a callable `side_effect` that never exhausts, e.g. `itertools.count` seeded appropriately) so every real call site in the timeout + failure-recording path receives a value.

**Acceptance Criteria**: The test raises and matches `RuntimeError` with message containing `"did not become healthy"`, not `StopIteration`.

**Definition of Done**: `uv run pytest tests/test_lifecycle.py -v` passes; no new failures elsewhere in `test_lifecycle.py`.

**Validation Commands**: `uv run pytest tests/test_lifecycle.py -v`

**Out of Scope**: Do not modify `http_lifecycle.py` or `factory.py` production code; this is a test-only fix unless investigation reveals a genuine production bug in the failure-recording path.

**AI Implementation Instruction**: Count the exact number of `time.monotonic()` calls along the exercised code path (including the except-block) before choosing the new mock strategy.

---

### Issue 4: `test_tool_schema.py` references non-existent module `mcp_servers.git.tools`

**Title**: Fix stale module path `mcp_servers.git.tools` → `mcp_servers.git.git_tools` in TOOL_LIST schema tests

**Summary**: Commit `ca6b7bfe` ("refactor: rename MCP server files to eliminate duplicate filenames") renamed `mcp_servers/git/tools.py` to `mcp_servers/git/git_tools.py` across the codebase, but `tests/test_tool_schema.py`'s `_SCHEM_MODULES` list was not updated, causing 2 parametrized tests to fail with `ModuleNotFoundError`.

**Background**: The rename affected 36 files across 8 MCP servers per the commit message. `tests/test_tool_schema.py:22-26` is the only remaining reference to the pre-rename path.

**Problem**: `test_static_schema_required_fields[mcp_servers.git.tools-TOOL_LIST]` and `test_config_dependent_field_present_and_requires_config_absent[mcp_servers.git.tools-TOOL_LIST]` both fail with `ModuleNotFoundError: No module named 'mcp_servers.git.tools'`, meaning the git-server TOOL_LIST schema is currently unchecked by this file.

**Evidence**: `tests/test_tool_schema.py:22-26`; commit `ca6b7bfe` diff (git server files renamed to `git_*.py`).

**Required Changes**: Update `_SCHEM_MODULES` entry `("mcp_servers.git.tools", "TOOL_LIST")` to `("mcp_servers.git.git_tools", "TOOL_LIST")`.

**Acceptance Criteria**: Both parametrized tests pass for the git module.

**Definition of Done**: `uv run pytest tests/test_tool_schema.py -v` passes fully.

**Validation Commands**: `uv run pytest tests/test_tool_schema.py -v`

**Out of Scope**: Do not touch the file/read_tools, write_tools, delete_tools entries (already correct).

**AI Implementation Instruction**: Grep the whole repo for any other lingering `mcp_servers.<server>.tools` (pre-rename) references before closing this issue, in case other files have the same staleness.

---

### Issue 5: `eventbus` layer violates its own architectural isolation contract

**Title**: Remove `eventbus` → `db`/`shared` imports to restore `.importlinter` `eventbus-is-isolated` contract

**Summary**: `PYTHONPATH=scripts uv run lint-imports` reports the `eventbus-is-isolated` contract as BROKEN: `eventbus/db.py` imports `db.helper`, and `eventbus/{ack,dlq,publish,replay,subscribe}_route.py` import `shared.json_utils`. Per `rules/env.md`, eventbus is documented as fully independent from every other layer, and the `.importlinter` contract has enforced this since the Event Bus's initial introduction (commit `6153338f`).

**Background**: Git history shows the violation was introduced unintentionally by two later deduplication refactors: commit `d2067882` ("PRAGMA設定の一元化") introduced the `db.helper` dependency, and commits `4bdcb014`/`381ba262` ("timestamp helper 統合"/"orjson.dumps置換") introduced the `shared.json_utils` dependency. Neither commit updated `.importlinter` or `rules/env.md`, and neither commit message declares an intentional architecture change.

**Problem**: The dependency graph no longer matches the documented and originally-enforced architecture. `lint-imports` currently fails, meaning this check is not passing in its current state (whether or not it's wired into CI is a separate open question — see CI-1).

**Evidence**: `PYTHONPATH=scripts uv run lint-imports` output showing 6 violating edges; `.importlinter` contract `eventbus-is-isolated`; `rules/env.md` "eventbus → 他の全レイヤーから完全に独立"; `git log -S` for `d2067882`, `4bdcb014`, `381ba262`, `6153338f`.

**Required Changes**: Duplicate the small, side-effect-free functions eventbus depends on (`apply_connection_pragmas` from `db/helper.py`; `now_iso` and `dumps` from `shared/json_utils.py`) into the `eventbus` package itself, and switch all 6 violating import sites to the local copies.

**Acceptance Criteria**: `PYTHONPATH=scripts uv run lint-imports` reports all 5 contracts as KEPT.

**Definition of Done**: lint-imports passes; all existing `tests/test_eventbus*.py` pass unmodified in behavior; a minimal unit test is added for the duplicated helper(s) if none exists.

**Validation Commands**: `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest tests/test_eventbus*.py -v`

**Out of Scope**: Do not change `db/helper.py` or `shared/json_utils.py` themselves; do not alter eventbus's externally-observable behavior (SQLite pragmas, JSON serialization format, timestamp format must stay byte-identical).

**AI Implementation Instruction**: Before implementing, add the migration guard test described in the companion coverage-gap finding EVENTBUS-4 (old-schema → new-schema migration test) if it does not already exist, since this change touches `eventbus/db.py`, the same file with the untested `_migrate()` function. Do this to reduce regression risk from touching this file twice.

---

### Issue 6: CI and coverage tooling reference a non-existent `main` branch

**Title**: Fix `main`/`master` branch mismatch breaking `diff-cover` and CI triggers

**Summary**: `.github/workflows/ci.yml` triggers on `branches: [main]` and `rules/toolchain.md` documents `uv run diff-cover coverage.xml --compare-branch=main --fail-under=90`, but this repository's only branch (local and `origin`) is `master`. Running the documented command locally fails immediately with `fatal: ambiguous argument 'main...HEAD': unknown revision or path not in the working tree`.

**Background**: `git branch -a` shows only `master` and `remotes/origin/master`. No `main` branch exists anywhere in this repository.

**Problem**: (1) The documented `diff-cover` command in the standard validation sequence cannot be run as written by anyone following `rules/toolchain.md`. (2) `.github/workflows/ci.yml`'s `on: push: branches: [main]` / `on: pull_request: branches: [main]` triggers reference a branch that doesn't exist, which means CI may never actually run on pushes/PRs against the real default branch (`master`) unless GitHub-side branch protection or repository settings compensate for this in a way not visible from the local checkout.

**Evidence**: `git branch -a` output; `diff-cover` stack trace (`CommandError: fatal: ambiguous argument 'main...HEAD'`); `.github/workflows/ci.yml:5-7`; `rules/toolchain.md` §7.

**Required Changes**: Decide and apply one of: (a) rename the default branch to `main` repository-wide (GitHub default-branch rename + local branch rename + update any hardcoded references), or (b) update `.github/workflows/ci.yml` and `rules/toolchain.md` to use `master` consistently. This decision requires human confirmation (see Additional Confirmation Items in the source audit).

**Acceptance Criteria**: `uv run diff-cover coverage.xml --compare-branch=<correct-branch> --fail-under=90` runs without error locally; a test push/PR against the real default branch visibly triggers the CI workflow on GitHub.

**Definition of Done**: CI config and documentation both reference the same, real branch name; diff-cover runs successfully in both CI and local validation; evidence of a successful CI run attached to the PR that closes this issue.

**Validation Commands**: `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (or the chosen branch name), manual verification of a GitHub Actions run triggered by this change.

**Out of Scope**: Do not change the 90% coverage threshold itself as part of this fix.

**AI Implementation Instruction**: This issue requires a human decision on which branch name is canonical before implementation — do not unilaterally rename the repository's default branch. Flag this explicitly and wait for confirmation rather than guessing.

---

### Issue 7: Annotate false-positive bandit B608 findings so the security scan gate passes

**Title**: Add `# nosec B608` annotations to 8 false-positive SQL-injection findings blocking `bandit`

**Summary**: `uv run bandit -r scripts/ -c pyproject.toml` currently exits with code 1 due to 8 medium-severity B608 (`hardcoded_sql_expressions`) findings. All 8 are verified false positives — dynamically assembled `WHERE`/`IN` clause fragments built from fixed column names, with all actual values passed through parameterized `?` placeholders, never string-interpolated. The same pattern elsewhere in the codebase (`scripts/db/maintenance.py:148`, `scripts/db/store_impl.py:258`) already carries `# nosec B608` annotations; these 8 do not.

**Background**: `rules/toolchain.md` documents bandit as a required step in the standard validation sequence ("Address high/medium severity findings before proceeding"), and it is the `Security scan` step in `.github/workflows/ci.yml`'s `lint` job.

**Problem**: The CI `lint` job's `Security scan` step will fail on the current codebase. The 8 findings are: `scripts/eventbus/db.py:195`, `scripts/eventbus/subscribe_route.py:47`, `scripts/mcp_servers/mdq/db_grep.py:72`, `scripts/mcp_servers/mdq/health_check.py:35`, `scripts/mcp_servers/mdq/mdq_service.py:205`, `scripts/mcp_servers/mdq/mdq_service.py:327`, `scripts/mcp_servers/mdq/search.py:145`, `scripts/mcp_servers/mdq/search.py:156`.

**Evidence**: Full `bandit -r scripts/ -c pyproject.toml` output; manual code review of each of the 8 locations confirming parameterized query construction with fixed column names and no string-interpolated user input; comparison with existing `# nosec B608` usage in `scripts/db/maintenance.py` and `scripts/db/store_impl.py`.

**Required Changes**: Add a `# nosec B608 - <short reason: dynamic WHERE fragment from fixed columns, values bound via placeholders>` comment to each of the 8 lines, following the exact wording style already used in `scripts/db/maintenance.py`/`store_impl.py`.

**Acceptance Criteria**: `uv run bandit -r scripts/ -c pyproject.toml` exits 0 with zero unaddressed medium/high findings.

**Definition of Done**: bandit passes; no production logic changed (comment-only diff); existing tests unaffected.

**Validation Commands**: `uv run bandit -r scripts/ -c pyproject.toml`

**Out of Scope**: Do not suppress the B101/B104/B105/B107/B404 findings as part of this issue — those require separate case-by-case review (see TASK-L2-adjacent follow-up, not drafted here as it is not High priority).

**AI Implementation Instruction**: Before adding each annotation, re-verify (do not assume from this report alone) that the specific line's SQL string has no non-parameterized dynamic content — re-read the full function each nosec is added to, since bandit line numbers can drift if the file has since changed.

---

### Issue 8: Add unit tests for GitHub MCP service layer (21–47% coverage)

**Title**: Raise test coverage for `mcp_servers/github/service_*.py` and `server_*.py` business logic

**Summary**: `scripts/mcp_servers/github/service_pull_requests.py` (21%), `service_repository.py` (27%), `service_issues.py` (31%), `service_file.py` (40%), and the corresponding `server_*.py` route wrappers (43–47%) are the lowest-covered non-omitted production modules in the repository, per `uv run coverage report`.

**Background**: `pyproject.toml`'s coverage `omit` list explicitly excludes only `scripts/mcp_servers/github/server.py` (FastAPI entry point), not the `service_*.py` business-logic files, meaning these are intended to be unit-tested but are not.

**Problem**: The bulk of GitHub MCP tool business logic (issue/PR/repository/file operations against the GitHub API) has little to no success-path or error-path test coverage, making regressions in this subsystem likely to go undetected.

**Evidence**: `uv run coverage report` output lines for the listed files; existing `tests/test_github_mcp_service.py` as the current (partial) coverage source.

**Required Changes**: Add unit tests to `tests/test_github_mcp_service.py` (or split into per-concern test files) covering, for each of `service_file.py`, `service_issues.py`, `service_pull_requests.py`, `service_repository.py`: at least one success-path test and at least one GitHub-API-error-path test (4xx/5xx response handling) per public method.

**Acceptance Criteria**: Each of the 4 listed `service_*.py` files reaches at least 70% line coverage.

**Definition of Done**: New tests pass; `uv run coverage report` shows ≥70% for the 4 files; no new lint/type errors; existing GitHub MCP tests unaffected.

**Validation Commands**: `uv run pytest tests/test_github_mcp_service.py -v`, `uv run coverage run -m pytest tests/ && uv run coverage report`

**Out of Scope**: Do not modify production `service_*.py`/`server_*.py` logic as part of this issue unless a genuine bug is discovered while writing tests (if so, file a separate issue).

**AI Implementation Instruction**: Follow the existing mocking conventions already used in `tests/test_github_mcp_service.py` for GitHub API responses rather than introducing a new mocking library or pattern.
