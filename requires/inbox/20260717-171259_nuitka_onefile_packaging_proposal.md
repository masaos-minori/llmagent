# deploy 時の Nuitka によるワンバイナリ化 改善要望書

## 概要

deploy 時に本エージェント本体および各 MCP サーバーを Nuitka で `--onefile` バイナリ化し、
`/opt/llm/` への配布方式を現行の `rsync` + `uv run` から単一バイナリ配布に切り替えたい。
本書は実装前の方針検討結果をまとめたものであり、コード変更は未着手。

## 状態: 提案（未着手）

## 背景・目的

- 現行デプロイ (`skills/deploy/SKILL.md` 記載) は `deploy/deploy.sh` で `scripts/`, `config/`,
  `schemas/`, `tests/` を `rsync -av --delete` で `/opt/llm/` に同期し、`uv run` により
  実行時に依存解決する運用。
- 起動高速化・配布物の単純化・依存解決の実行時オーバーヘッド削減を目的として、
  Nuitka によるワンバイナリ化を検討する。

## 前提条件（確定事項）

検討の過程で以下の3点を前提として確定した。

1. **plugin 機構は廃止する**
   `scripts/shared/plugin_registry.py` による `plugins/` 配下の動的ロードを廃止し、
   静的 import 前提の構成に変更する。
2. **MCP サーバーも個別に単一バイナリ化する**
   メインエージェントとは別に、MCP サーバー1種につき1バイナリを作成する。
3. **`config/`, `sudachidict-core`, `sqlite-vec.so` は外部データとして配置する**
   バイナリに埋め込まず、`/opt/llm/` 配下の外部ファイル・ディレクトリとして
   実行時に参照する。

## 現状調査結果（事実）

### エントリポイント

- `scripts/agent.py` は既に削除済み（過去のレガシーエントリポイント）。
- 本番導線は `deploy/start_agent.sh:76` の `uv run python -m agent.repl` であり、
  `scripts/agent/repl.py:453` の `if __name__ == "__main__":` が起点。
- `scripts/agent/__main__.py`（`python -m agent`）は存在するが本番導線では未使用。
- `pyproject.toml:128-130`（coverage omit）に存在しない `scripts/agent.py` の記述が
  残存しており、ドキュメントドリフトがある（本件とは別問題として要整理）。

### MCP サーバー構成

`config/agent.toml` に10個の MCP サーバー定義があり、いずれも同一パターン。

| サーバー | セクション | 主な依存 |
|---|---|---|
| shell | `[mcp_servers.shell]` | 標準ライブラリ中心（`subprocess_runner.py`） |
| git | `[mcp_servers.git]` | `gitpython` |
| web_search | `[mcp_servers.web_search]` | `duckduckgo-search` |
| file_delete | `[mcp_servers.file_delete]` | 標準ライブラリ |
| file_write | `[mcp_servers.file_write]` | 標準ライブラリ |
| file_read | `[mcp_servers.file_read]` | 標準ライブラリ |
| github | `[mcp_servers.github]` | `PyGithub` |
| cicd | `[mcp_servers.cicd]` | `PyGithub`（GitHub Actions API 経由） |
| rag_pipeline | `[mcp_servers.rag_pipeline]` | `sqlite-vec`, `sudachipy` |
| mdq | `[mcp_servers.mdq]` | 標準ライブラリ + SQLite |

全て `transport = "http"`, `startup_mode = "subprocess"`,
`cmd = ["uv", "run", "--directory", "/opt/llm", "python", "/opt/llm/scripts/mcp_servers/.../server.py"]`
という構成で、`scripts/agent/http_lifecycle.py` の `HttpServerLifecycleManager` が
`subprocess` で個別プロセスとして起動する。HTTP 越しの独立プロセスであるため、
`cmd` をバイナリパスに差し替えるだけで移行できる。

### 動的ロード機構（廃止・確認対象）

- `scripts/shared/plugin_registry.py`: `plugins/` 配下の `*.py` を実行時にファイルシステム
  走査して import（呼び出し元 `scripts/agent/factory.py:393`）。→ 前提1により廃止。
- `scripts/mcp_launcher.py:36-51`: `pkgutil.walk_packages` + `importlib.import_module` で
  `mcp_servers.*` を動的発見。本番導線（`http_lifecycle.py` 経由の起動）では使用されて
  いない単体起動用ツールと判明しており、個別バイナリ化方式では影響しない。

### ネイティブ依存・外部データ化対象

- **sqlite-vec**: `scripts/db/helper.py:129-140` の `_load_vec_extension()` が
  `sqlite3.load_extension()` 経由でロード。パスは `config/agent.toml:9` に
  `sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"` と絶対パスで設定済み。
  Python の import 機構とは無関係のため **変更不要**、現状のまま外部データとして扱える。
- **sudachidict-core**: `sudachipy` 経由で `rag/repository.py:37-70` の
  `_SudachiTokenizer` と `chunk_splitter.py:34-35,107,109` が使用。パッケージ内
  `resources/system.dic`（約217MB）を外部配置に変更する必要があり、
  `sudachipy.Dictionary()` に外部辞書パスを渡す API 仕様の確認が実装時に必要
  （未検証）。
- **`config/`**: `scripts/agent/config_builders.py:38` と
  `scripts/shared/config_loader.py:61-62` がいずれも `__file__` 基準の相対パスで
  解決している。onefile 展開後の一時ディレクトリでは崩れるため、実行ファイル隣接
  ディレクトリまたは環境変数（例: `LLMAGENT_CONFIG_DIR`）基準に変更する必要がある。

### 現行デプロイ方式

- `skills/deploy/SKILL.md`: `deploy/deploy.sh`（rsync 同期）→ `deploy/init_db.sh`
  （スキーマ初期化）→ `deploy/setup_services.sh`（サービス起動）の3段階。
  venv 自体は同梱せず `/opt/llm` 側で `uv run` により都度依存解決。
- `.github/workflows/` にバイナリビルド関連の記述は無し（lint/テスト/ドキュメント
  整合性チェックのみ）。

## 提案する作業計画

### Phase 0: 実現性の下調べ
- Nuitka の Python 3.13 対応、および `sudachipy` / `orjson` / `pydantic-core` /
  `lxml` / `PyGithub` / `gitpython` のビルド可否を PoC で確認。

### Phase 1: コード側の設計変更
1. plugin 廃止: `plugin_registry.py` 削除、`factory.py:393` の呼び出し除去
   （廃止前に `plugins/` 配下の現存プラグイン有無を確認）
2. `config_loader.py` / `config_builders.py` のパス解決を環境変数/実行ファイル
   隣接ディレクトリ基準に変更
3. `_SudachiTokenizer` を外部 `system.dic` パス指定方式に変更
4. `config/agent.toml` の10個の `cmd` をバイナリパス形式に書き換え

### Phase 2: PoC
- 依存の軽い `shell` サーバーで1本ビルドし、外部 config 読み込み・HTTP 起動を確認
- `rag_pipeline` サーバーで外部辞書パス指定・sqlite-vec 拡張ロードを検証
- メインエージェント本体をビルド

### Phase 3: ビルドスクリプト・CI整備
- `deploy/build_binaries.sh` で計11バイナリ（メインエージェント1 + MCP サーバー10）を
  ループビルド
- `.github/workflows/` へのビルド検証ジョブ追加を検討

### Phase 4: デプロイ手順の改修
- `deploy/deploy.sh` をバイナリ配布 + 外部データ配置
  （`config/`, `sqlite-vec/`, 辞書ディレクトリ）方式に変更
- `deploy/init_db.sh`, `deploy/setup_services.sh` の起動コマンドをバイナリ呼び出しに更新

### Phase 5: 検証・ロールバック
- REPL 起動・全 MCP サーバー HTTP 疎通・RAG 検索（外部辞書読み込み含む）の
  スモークテスト
- 起動時間・配布サイズの計測
- `uv run` 方式への切り戻し手順を保持

## 想定される配布物構成

```
/opt/llm/bin/agent
/opt/llm/bin/mcp_shell
/opt/llm/bin/mcp_git
/opt/llm/bin/mcp_web_search
/opt/llm/bin/mcp_file_delete
/opt/llm/bin/mcp_file_write
/opt/llm/bin/mcp_file_read
/opt/llm/bin/mcp_github
/opt/llm/bin/mcp_cicd
/opt/llm/bin/mcp_rag_pipeline
/opt/llm/bin/mcp_mdq
/opt/llm/config/            (外部データ、既存のまま)
/opt/llm/sqlite-vec/vec0.so (外部データ、既存のまま)
/opt/llm/dict/system.dic    (新規、sudachidict-core から抽出して外部配置)
```

## リスク・残課題

- `sudachipy.Dictionary()` が外部 `system.dic` 絶対パスを受け付ける API 仕様の
  確認が未実施（実装フェーズで要検証）。
- plugin 廃止対象の `plugins/` ディレクトリに現在有効なプラグインが存在するか未確認。
  削除前に中身の確認が必要。
- `pyproject.toml` の coverage omit に残る `scripts/agent.py` 等の存在しないパス
  記述は本件とは別に整理が必要（ドキュメントドリフト）。
- 11バイナリ分のビルド時間・CI 負荷は Phase 0 の PoC 結果を待って見積もる。

## 関連調査

- 本要望書は 2026-07-17 の Nuitka 化検討セッションでの調査・議論に基づく。
  関連ファイル: `scripts/agent/repl.py`, `scripts/db/helper.py`,
  `scripts/rag/repository.py`, `scripts/shared/config_loader.py`,
  `scripts/agent/config_builders.py`, `scripts/shared/plugin_registry.py`,
  `scripts/agent/factory.py`, `scripts/mcp_launcher.py`, `config/agent.toml`,
  `skills/deploy/SKILL.md`, `deploy/deploy.sh`
