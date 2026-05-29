# 02_implement_plan.md
# ディレクトリ構成リファクタリング計画

## Goal

`scripts/` 配下に 75+ ファイルが完全フラットに並んでいる現状を、
**agent / MCP Server / RAG** のドメイン境界に沿ったパッケージ構造へ再編し、
モジュール検索・依存方向の把握・新規ファイルの配置先判断を容易にする。

---

## Scope

| 対象 | 変更内容 |
|---|---|
| `scripts/*.py` (75 ファイル) | ドメイン別サブディレクトリへ移動 + import 書き換え |
| `tests/*.py` (25 ファイル) | import パス更新 / `conftest.py` 更新 |
| `init.d/` (12 サービス) | `command_args` のモジュール参照を新パスへ更新 |
| `deploy/deploy.sh` | 個別 `cp` → `rsync -r` または glob コピーへ書き換え |
| `pyproject.toml` | `mypy.files`, `coverage.source`, `pyright.include` 更新 |
| `config/*.toml` | 変更なし (ファイル名は変えない) |
| `plugins/` | 変更なし |

後方互換性は要件外。

---

## Assumptions

1. Python パッケージ化 (pip install -e) はしない。`scripts/` を `sys.path` に追加する現行方式を継続する。
2. `scripts/` ディレクトリ名は変更しない (OpenRC の `directory="/opt/llm/scripts"` を最小変更に留める)。
3. 各サブパッケージに `__init__.py` を置くが、re-export は行わない (フラット import を維持しない)。
4. bowler は module rename には不適 (関数/クラス名のみ); import 書き換えは `libcst` スクリプトまたは `sed` で行う。

---

## Unknowns (解消済み)

| # | 不明点 | 解決 |
|---|---|---|
| U1 | `[tool.importlinter]` セクションが未設定 | 今回スコープで `.importlinter` を新規作成する (Phase 7) |
| U2 | `mcp_installer.py` が動的 import を行うか | 確認済み: 動的 import なし。テンプレートファイルを生成するだけ。ただし生成テンプレート内の `scripts/<module>_mcp_server.py` 出力先と `command_args="{module}_mcp_server:app"` パターンが新構造に合わなくなるため、`mcp/installer.py` 自体を更新する必要がある (Phase 5 に追加) |
| U3 | `memory/` を `agent/` 内か `shared/` か | 確認済み: RAG 側からメモリを呼ぶ予定なし → `agent/memory/` に配置確定 |

---

## Affected areas

```
scripts/                  ← 全ファイルが移動対象
tests/                    ← import パス全更新
init.d/                   ← command_args のモジュール参照更新
deploy/deploy.sh          ← コピー方法変更
pyproject.toml            ← mypy / coverage / pyright の paths 更新
conftest.py               ← sys.path は scripts/ のままなので変更なし
CLAUDE.md                 ← Architecture 欄のパス記述更新
routing.md                ← docs path mapping 更新
rules/env.md              ← ディレクトリ構成記述更新
docs/*.md                 ← import 例・ファイルパスの記述更新
```

---

## Design

### 新ディレクトリ構成

```
scripts/
  agent.py                      # エントリポイント (ルートに残す)
  agent/                        # Agent REPL コア
    __init__.py
    repl.py                     # ← agent_repl.py
    repl_health.py              # ← agent_repl_health.py
    repl_tool_exec.py           # ← agent_repl_tool_exec.py
    repl_debug.py               # ← agent_repl_debug.py
    orchestrator.py             # ← orchestrator.py
    config.py                   # ← agent_config.py
    context.py                  # ← agent_context.py
    session.py                  # ← agent_session.py
    history.py                  # ← history_manager.py
    cli_view.py                 # ← cli_view.py
    commands/
      __init__.py
      registry.py               # ← agent_commands.py
      cmd_config.py             # ← agent_cmd_config.py
      cmd_context.py            # ← agent_cmd_context.py
      cmd_ingest.py             # ← agent_cmd_ingest.py
      cmd_mcp.py                # ← agent_cmd_mcp.py
      cmd_rag.py                # ← agent_cmd_rag.py
      cmd_session.py            # ← agent_cmd_session.py
    memory/
      __init__.py
      layer.py                  # ← memory_layer.py
      store.py                  # ← memory_store.py

  mcp/                          # MCP サーバ群
    __init__.py
    server.py                   # ← mcp_server.py (base)
    models.py                   # ← mcp_models.py
    installer.py                # ← mcp_installer.py
    file/
      __init__.py
      common.py                 # ← file_mcp_common.py
      read_models.py            # ← file_read_mcp_models.py
      read_service.py           # ← file_read_mcp_service.py
      read_tools.py             # ← file_read_mcp_tools.py
      read_server.py            # ← file_read_mcp_server.py
      write_models.py           # ← file_write_mcp_models.py
      write_service.py          # ← file_write_mcp_service.py
      write_server.py           # ← file_write_mcp_server.py
      delete_models.py          # ← file_delete_mcp_models.py
      delete_service.py         # ← file_delete_mcp_service.py
      delete_server.py          # ← file_delete_mcp_server.py
    github/
      __init__.py
      models.py                 # ← github_mcp_models.py
      service.py                # ← github_mcp_service.py
      tools.py                  # ← github_mcp_tools.py
      server.py                 # ← github_mcp_server.py
    shell/
      __init__.py
      models.py                 # ← shell_mcp_models.py
      service.py                # ← shell_mcp_service.py
      server.py                 # ← shell_mcp_server.py
    web_search/
      __init__.py
      server.py                 # ← web_search_mcp_server.py

  rag/                          # RAG パイプライン
    __init__.py
    pipeline.py                 # ← agent_rag.py
    repository.py               # ← rag_repository.py
    llm.py                      # ← rag_llm.py
    types.py                    # ← rag_types.py
    utils.py                    # ← rag_utils.py
    ingestion/
      __init__.py
      crawler.py                # ← web_crawler.py
      crawler_utils.py          # ← crawler_utils.py
      chunk_splitter.py         # ← chunk_splitter.py
      chunk_utils.py            # ← chunk_utils.py
      chunk_english.py          # ← chunk_english.py
      chunk_japanese.py         # ← chunk_japanese.py
      ingester.py               # ← rag_ingester.py
      pipeline_utils.py         # ← pipeline_utils.py
    mcp/
      __init__.py
      server.py                 # ← rag_mcp_server.py
      service.py                # ← rag_pipeline_mcp_service.py
      models.py                 # ← rag_pipeline_mcp_models.py

  db/                           # SQLite 層
    __init__.py
    helper.py                   # ← sqlite_helper.py
    maintenance.py              # ← db_maintenance.py
    store.py                    # ← db_store.py
    tool_results.py             # ← tool_result_store.py
    create_schema.py            # ← create_schema.py
    migrate.py                  # ← migrate_db.py

  shared/                       # 横断共通
    __init__.py
    llm_client.py               # ← llm_client.py
    logger.py                   # ← logger.py
    config_loader.py            # ← config_loader.py
    formatters.py               # ← formatters.py
    git_helper.py               # ← git_helper.py
    otel_tracer.py              # ← otel_tracer.py
    plugin_registry.py          # ← plugin_registry.py
    tool_executor.py            # ← tool_executor.py
```

### 依存方向ルール

```
agent → rag, db, shared, mcp (installer のみ)
mcp   → db, shared
rag   → db, shared
db    → shared
shared → (外部ライブラリのみ)
```

`agent/memory/` は agent 内閉じ。`rag_pipeline_mcp_service.py` がメモリを参照しないことを確認済みのため `mcp/` から `agent/memory/` への依存は発生しない。

### OpenRC サービスのモジュール参照変更例

| サービス | 変更前 | 変更後 |
|---|---|---|
| `rag-pipeline-mcp` | `rag_mcp_server:app` | `rag.mcp.server:app` |
| `file-read-mcp` | `file_read_mcp_server:app` | `mcp.file.read_server:app` |
| `github-mcp` | `github_mcp_server:app` | `mcp.github.server:app` |
| `shell-mcp` | `shell_mcp_server:app` | `mcp.shell.server:app` |
| `web-search-mcp` | `web_search_mcp_server:app` | `mcp.web_search.server:app` |

### deploy.sh 変更方針

```bash
# 変更前: 個別 cp (75行)
cp "${REPO_ROOT}/scripts/agent_repl.py" "${DEPLOY_SCRIPTS}/"
...

# 変更後: rsync で scripts/ 以下を丸ごとコピー
rsync -av --delete \
  --include="*.py" --include="**/*.py" --include="*/" \
  --exclude="__pycache__/" --exclude="*.pyc" \
  "${REPO_ROOT}/scripts/" "${DEPLOY_SCRIPTS}/"
```

---

## Implementation steps

### Phase 1: 事前調査・準備 (破壊的変更なし)

1. `rag_pipeline_mcp_service.py` が `memory_layer` / `memory_store` を import するか確認
2. `mcp_installer.py` が動的 import を行うか確認 (U2 解消)
3. `[tool.importlinter]` セクションの設計: 依存方向ルールを `.importlinter` に記述
4. 移行スクリプト (`scripts/tools/rewrite_imports.py`) の雛形を用意 (libcst ベース)

### Phase 2: `db/` パッケージ移行

依存される側から移行する。`db/` は `shared/` のみに依存するため最初に安全に移行できる。

1. `scripts/db/` ディレクトリ作成、`__init__.py` 追加
2. `git mv` で 6 ファイル移動
3. import 書き換え: `from sqlite_helper import` → `from db.helper import` 等
4. `tests/test_sqlite_helper.py` 等のテスト import 更新
5. `ruff format`, `ruff check`, `mypy`, `pytest` で確認

### Phase 3: `shared/` パッケージ移行

1. `scripts/shared/` 作成
2. `git mv` で 8 ファイル移動
3. import 書き換え
4. テスト更新・バリデーション

### Phase 4: `rag/` パッケージ移行

1. `scripts/rag/` と `scripts/rag/ingestion/`, `scripts/rag/mcp/` 作成
2. `git mv` で 13 ファイル移動
3. import 書き換え
4. `init.d/rag-pipeline-mcp` の `command_args` 更新
5. テスト更新・バリデーション

### Phase 5: `mcp/` パッケージ移行

1. `scripts/mcp/` と各サブディレクトリ作成
2. `git mv` で 14 ファイル移動 (file/github/shell/web_search)
3. import 書き換え
4. `init.d/` の 4 サービス更新
5. `mcp/installer.py` テンプレート更新:
   - 生成先を `scripts/mcp/<name>/server.py` + `__init__.py` に変更
   - 生成する `init.d` の `command_args` を `mcp.<name>.server:app` 形式に変更
   - `_REPO_ROOT` からの出力パス計算を修正
6. テスト更新・バリデーション

### Phase 6: `agent/` パッケージ移行

1. `scripts/agent/` と `commands/`, `memory/` 作成
2. `git mv` で 16 ファイル移動
3. import 書き換え
4. `init.d/llama-agent` 確認 (agent.py はルートに残るため変更不要)
5. テスト更新・バリデーション

### Phase 7: インフラ・設定更新

1. `pyproject.toml`: `mypy.files`, `coverage.source`, `pyright.include` を新パスへ更新
2. `deploy/deploy.sh`: rsync ベースに書き換え
3. `[tool.importlinter]` セクション追加・`lint-imports` 通過確認
4. `CLAUDE.md`, `routing.md`, `rules/env.md`, 関連 `docs/*.md` 更新

### Phase 8: 最終バリデーション

`pre-commit run --all-files` + `diff-cover` 90% ゲート確認

---

## Validation plan

各フェーズ終了後に以下を必ず通過させてから次フェーズに進む。

```bash
ruff format scripts/ tests/
ruff check scripts/ tests/ --fix && ruff check scripts/ tests/
mypy scripts/ tests/
pytest tests/ -v
```

Phase 7 以降で追加:
```bash
lint-imports                     # 依存方向ルール検査
coverage run -m pytest tests/ && coverage xml
diff-cover coverage.xml --compare-branch=main --fail-under=90
pre-commit run --all-files
```

---

## Risks

| # | リスク | 深刻度 | 対処 |
|---|---|---|---|
| R1 | import 書き換え漏れで実行時 `ModuleNotFoundError` が発生する | 高 | Phase ごとに `pytest` を通過させる; `grep -rn "from sqlite_helper\|import sqlite_helper"` 等で機械的に漏れ検出 |
| R2 | `rag_pipeline_mcp_service.py` がモジュールレベルで `sqlite_helper._cfg` を上書きしている。移動後にモジュール参照先が変わると設定オーバーライドが効かなくなる | 高 | Phase 1 で動作を文書化し、`db.helper._cfg` を参照するよう import パスを統一する |
| R3 | `mcp_installer.py` のテンプレートが旧フラット構造を前提にしている。更新前に `/mcp install` を実行すると旧パスに生成されてしまう | 中 | Phase 5 でテンプレートを更新するまで `/mcp install` を使わないよう運用で制御する |
| R4 | `uvicorn` の `module:app` 参照 (例: `rag_mcp_server:app`) は `PYTHONPATH` に `scripts/` が通っていることが前提。サブパッケージへ移動後は `rag.mcp.server:app` 形式に変更が必要 | 高 | `init.d/` の全サービスを Phase 4–5 で一括更新; ステージング環境で実際に起動確認する |
| R5 | フェーズ数が多く (8フェーズ)、途中でブランチが長期化すると main との乖離が大きくなる | 中 | 各フェーズを独立コミットとし、Phase 2–3 完了時点でマージ可能な状態を保つ |
| R6 | `[tool.importlinter]` 設定が未定義のため `lint-imports` が現在 no-op。新構造で初めて依存ルールを定義するため、既存コードに違反が多数見つかる可能性がある | 低 | Phase 7 で `lint-imports` を初導入; 違反は Phase 6 までの import 整理で自然に解消されるはず |
