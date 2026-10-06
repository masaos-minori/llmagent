# deploy 時の Nuitka によるワンバイナリ化 改善要望書

## 概要

deploy 時に本エージェント本体および各 MCP サーバーを Nuitka で `--onefile` バイナリ化し、
`/opt/llm/` への配布方式を現行の `rsync` + `uv run` から単一バイナリ配布に切り替えたい。
本書は実装前の方針検討結果をまとめたものであり、コード変更は未着手。

> **最終検証（2026-10-05）**: 記載事実を現行コードで敵対的に検証し、ドリフトを文中に反映済み。
> 主要項目（エントリポイント・MCPサーバー構成10・plugin廃止・sqlite-vec/sudachi・現行deploy）は
> 現状と一致。`cmd` の `--no-sync` フラグとサーバー実ファイル名 `<server>_server.py` は検証後に
> 更新（元々は記載欠落／`server.py` 仮説）。
> ドリフト: `scripts/agent/repl.py` の `if __name__` は162→156行目、
> `pyproject.toml` の coverage omit は140→144行目に移動。

## Priority
Medium

## Summary
deploy 時にエージェント本体と MCP サーバー10種を Nuitka `--onefile` で個別バイナリ化し、
`/opt/llm/` への配布を `rsync` + `uv run` から単一バイナリ配布へ切り替える。
`config/`、Sudachi 辞書、`sqlite-vec` は外部データとして配置する。
Phase 0 の PoC で実現可能と判断済み（下記「Phase 0 検証結果」）。

## Background
現行デプロイは `deploy/deploy.sh` による rsync 同期と、実行時の `uv run` 依存解決。
詳細は「背景・目的」「現状調査結果（事実）」を参照。

## Problem
- `uv run` による起動オーバーヘッドと、配布物（ソース + venv 解決）の複雑さ。
- onefile 化すると `__file__` 基準のパス解決（config, workflows）と、
  Sudachi 組み込み辞書指定（`dict="core"`）が外部配置と両立しない。

## Reason for Change
起動高速化・配布物の単純化・依存解決の実行時オーバーヘッド削減。
Phase 0 でバイナリ化と外部データ参照の技術的成立を確認できたため、設計変更に着手できる状態。

## Implementation Intent
「設計方針（config ディレクトリ / Sudachi 辞書）」のとおり、パス解決を `scripts/shared/`
の1箇所に集約し、辞書パスを設定・環境変数で絶対パス指定できるようにする。
その後、PoC、ビルドスクリプト、デプロイ手順の順に段階導入する（「提案する作業計画」）。

## Target Files or Areas
- `scripts/shared/config_loader.py`, `scripts/agent/workflow/workflow_loader.py`,
  `scripts/agent/config_builders.py`, `scripts/agent/context.py`,
  `scripts/agent/commands/cmd_skill.py`（パス解決の集約）
- `scripts/rag/repository.py`, `scripts/rag/ingestion/chunk_splitter.py`（Sudachi 辞書パス）
- `scripts/agent/http_lifecycle_command_validator.py`, `scripts/agent/http_lifecycle.py`（コマンド許可リスト）
- `pyproject.toml`（`PyYAML` 本番依存の追加）
- `config/agent.toml`（MCP サーバー `cmd`、辞書パス設定）
- `deploy/deploy.sh`, `deploy/init_db.sh`, `deploy/setup_services.sh`, 新規 `deploy/build_binaries.sh`
- `skills/deploy/SKILL.md`, `.github/workflows/`

## Required Changes
- パス解決関数を `scripts/shared/` に新設し、config / workflows の解決箇所を置換する
  （優先順位: `LLMAGENT_CONFIG_DIR` > 実行ファイル隣接 > `__file__` 基準）。
- Sudachi 辞書パスを設定キーと `LLMAGENT_SUDACHI_DICT` で指定可能にする（既定 `/opt/llm/dict/system.dic`、
  未設定時のみ `dict="core"`、存在しないパスは起動時エラー）。
- `config/agent.toml` の10個の `cmd` をバイナリパス形式へ変更する。
- `CommandValidator` の許可リストをバイナリ起動に対応させる（許可ディレクトリ配下の絶対パスのみ許可する等、検査を弱めない方式）。
- `PyYAML` を `pyproject.toml` の本番依存へ追加する（`mdq` が使用）。
- `uv run python -m ...` で起動している周辺経路（workflow.validate、create_schema、eventbus.app、rag.ingestion.*）の扱いを決める。
- `deploy/build_binaries.sh` を新設し、計11バイナリをビルドする。
- `deploy/deploy.sh` ほかをバイナリ配布 + 外部データ配置方式へ更新する。
- Nuitka ビルドには `--include-package-data=sudachipy` が必須。

## Constraints
- 外部データ（`config/`, `sqlite-vec/vec0.so`, 辞書）はバイナリに埋め込まない。
- `sudachidict-core` の版は `sudachipy` の版と対応させる。
- 開発時の `uv run` 実行は引き続き動作させる（フォールバック維持）。
- ビルドホストに `python3-dev`（または uv 管理 Python）と `patchelf` が必要。
- 低メモリ環境では `--onefile-no-compression` を要する。`/tmp`（tmpfs）の容量に注意。

## Acceptance Criteria
- 全11バイナリがビルドでき、`/opt/llm/bin/` から起動できる。
- REPL 起動、全 MCP サーバーの HTTP 疎通、RAG 検索（外部辞書読込・sqlite-vec ロード含む）が通る。
- `LLMAGENT_CONFIG_DIR` と実行ファイル隣接の双方で config を解決できる。
- 辞書パスが不正な場合、起動時に明示エラーとなる。
- `uv run` 方式への切り戻し手順が保持されている。
- 起動時間・配布サイズが計測され、記録されている。

## Testing Expectations
- パス解決関数・辞書パス解決の単体テスト（優先順位、不正パス、フォールバック）。
- 既存テストスイートの回帰確認（`rules/toolchain.md` の検証シーケンス）。
- 実バイナリでのスモークテスト（REPL、MCP HTTP 疎通、RAG 検索）。

## Documentation Impact
- `skills/deploy/SKILL.md` と `docs/` のデプロイ・設定関連記述の更新が必要
  （配布物構成、外部データ配置、環境変数、切り戻し手順）。
- `LLMAGENT_CONFIG_DIR` / `LLMAGENT_SUDACHI_DICT` の仕様と失敗時挙動を記載する。

## Out of Scope
- plugin 機構（既に廃止済み）。
- `pyproject.toml` の coverage omit に残る存在しない `scripts/agent.py` 記述の整理（別件）。
- `scripts/agent/config_builders.py` の `_CONFIG_DIR` の誤指定（`scripts/config`）の単独修正（別件。ただしパス集約時に結果的に解消してよい）。
- `scripts/mcp_launcher.py` の変更（本番導線で未使用）。

## Dependencies
N/A: none（Phase 3 のビルド時間対策として `ccache` 等のビルドホスト整備が必要だが、他 issue への依存ではない）。

## Unresolved Questions
- 実際のエージェント本体と MCP サーバー（`fastapi`, `uvicorn`, `trafilatura`, `duckduckgo-search`, `httpx` 等）の Nuitka ビルド可否。
- 動的 import（`mcp_servers.*`、遅延 import）に対する `--include-package` の要否。
- `eventbus` 等のパッケージ内データファイルの同梱要否。
- 11バイナリ合計の配布サイズとビルド時間（`ccache` / standalone 共有方式の要否）。
- `skills/` ディレクトリの配布要否（`cmd_skill.py` の `_skills_dir` が `__file__` 基準）。
- 現行 HEAD の `CommandValidator` が `cmd[0]="uv"` を拒否する件が、本番（旧版コード）でどう動いているか。
- `uv run python -m ...` 系の周辺経路と `eventbus.app` をバイナリ化の対象に含めるか。
- `rag.pipeline` 等の遅延 import に必要な Nuitka 明示 include の範囲。

## AI Implementation Instruction
- パス解決は `scripts/shared/` の1箇所に集約し、重複実装を作らない。
- 辞書パス不正時に黙って `dict="core"` へフォールバックしない。
- `AGENTS.md` Global Rule 5 に従い、無関係なリファクタリングは行わない。
- 実装は `skills/python-implementation` に従い、`rules/toolchain.md` の検証を通す。

## 状態: 提案（Phase 0 実施済み・実現可能と判断。コード変更は未着手）

## 背景・目的

- 現行デプロイ (`skills/deploy/SKILL.md` 記載) は `deploy/deploy.sh` で `scripts/`, `config/`,
  `schemas/`, `tests/` を `rsync -av --delete` で `/opt/llm/` に同期し、`uv run` により
  実行時に依存解決する運用。
- 起動高速化・配布物の単純化・依存解決の実行時オーバーヘッド削減を目的として、
  Nuitka によるワンバイナリ化を検討する。

## 前提条件（確定事項）

検討の過程で以下の2点を前提として確定した。

1. **MCP サーバーも個別に単一バイナリ化する**
   メインエージェントとは別に、MCP サーバー1種につき1バイナリを作成する。
2. **`config/`, `sudachidict-core`, `sqlite-vec.so` は外部データとして配置する**
   バイナリに埋め込まず、`/opt/llm/` 配下の外部ファイル・ディレクトリとして
   実行時に参照する。

plugin 機構（`scripts/shared/plugin_registry.py` による `plugins/` 配下の動的ロード）は
本提案とは別の作業により既に廃止されており、静的 import 前提の構成になっている
（`scripts/` 配下に "plugin" 関連の参照は残っていない）。Nuitka 化にあたって
追加対応は不要。

## 現状調査結果（事実）

### エントリポイント

- `scripts/agent.py` は既に削除済み（過去のレガシーエントリポイント）。
- 本番導線は `deploy/start_agent.sh:76` の `uv run python -m agent.repl` であり、
  `scripts/agent/repl.py:156` の `if __name__ == "__main__":` が起点
  （`main()` → `AgentREPL().run()`）。
- `scripts/agent/__main__.py`（`python -m agent`）は存在するが本番導線では未使用。
- `pyproject.toml:144`（coverage omit）に存在しない `scripts/agent.py` の記述が
  残存しており、ドキュメントドリフトがある（本件とは別問題として要整理）。

### MCP サーバー構成

`config/agent.toml` に10個の MCP サーバー定義があり、いずれも同一パターン。

| サーバー | セクション | 主な依存 |
|---|---|---|
| shell | `[mcp_servers.shell]` | `fastapi`, `pydantic`（`subprocess_runner.py` は標準ライブラリ） |
| git | `[mcp_servers.git]` | `gitpython`, `fastapi`, `pydantic` |
| web_search | `[mcp_servers.web_search]` | `duckduckgo-search`, `beautifulsoup4`, `httpx`, `fastapi` |
| file_delete | `[mcp_servers.file_delete]` | `fastapi`, `pydantic` |
| file_write | `[mcp_servers.file_write]` | `fastapi`, `pydantic` |
| file_read | `[mcp_servers.file_read]` | `fastapi`, `pydantic` |
| github | `[mcp_servers.github]` | `PyGithub`, `fastapi` |
| cicd | `[mcp_servers.cicd]` | `httpx`, `orjson`, `fastapi`（`PyGithub` は import しておらず、GitHub Actions API を `httpx` で直接呼ぶ） |
| rag_pipeline | `[mcp_servers.rag_pipeline]` | `httpx`, `orjson`, `fastapi`。`sudachipy`/`sqlite-vec` は `rag.pipeline` の遅延 import（`rag_pipeline_service.py`）経由で、静的解析で検出されにくい |
| mdq | `[mcp_servers.mdq]` | `fastapi`, `pydantic`, `PyYAML`（`mdq/parser.py`）+ SQLite。PyYAML は `pyproject.toml` の本番依存に未記載（後述） |

全て `transport = "http"`, `startup_mode = "subprocess"`,
`cmd = ["uv", "run", "--no-sync", "--directory", "/opt/llm", "python", "/opt/llm/scripts/mcp_servers/<server>/<server>_server.py"]`
という構成（`--no-sync` は実行時の uv sync オーバーヘッド抑制のため全定義に付与）。
サーバー実ファイルは `<server>/<server>_server.py`（例: `shell/shell_server.py`, `mdq/mdq_server.py`）
だが、`file_*` の3つはディレクトリ名・ファイル名ともに異なる（`file_delete` -> `file/delete_server.py`、
`file_write` -> `file/write_server.py`、`file_read` -> `file/read_server.py`）。
`scripts/agent/http_lifecycle.py` の `HttpServerLifecycleManager` が `subprocess` で
個別プロセスとして起動する。HTTP 越しの独立プロセスであるため、`cmd` をバイナリパスに
差し替えるだけで移行できる。

### 動的ロード機構（確認対象）

- `scripts/mcp_launcher.py:36-51`: `pkgutil.walk_packages` + `importlib.import_module` で
  `mcp_servers.*` を動的発見。本番導線（`http_lifecycle.py` 経由の起動）では使用されて
  いない単体起動用ツールと判明しており、個別バイナリ化方式では影響しない。

### ネイティブ依存・外部データ化対象

- **sqlite-vec**: `scripts/db/helper.py:140` の `_load_vec_extension()` が
  `sqlite3.load_extension()` 経由でロード。パスは `config/agent.toml:9` に
  `sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"` と絶対パスで設定済み。
  Python の import 機構とは無関係のため **変更不要**、現状のまま外部データとして扱える。
- **sudachidict-core**: `sudachipy` 経由で `rag/repository.py` の
  `_SudachiTokenizer`（クラスは37行目、`Dictionary(dict="core")` 呼び出しは55行目）と
  `scripts/rag/ingestion/chunk_splitter.py`（import が33-34行目、
  `Dictionary(dict="core")` 呼び出しは81行目のみ。83行目は `SplitMode.C` 取得）が使用。
  `chunk_japanese.py` は注入されたトークナイザを使うだけで、辞書生成は行わない。呼び出し箇所は計2つ。パッケージ内 `resources/system.dic`（約217MB）を外部配置に
  変更する必要があり、現在も組み込み辞書指定方式（`dict="core"`）のままである。
  `sudachipy.Dictionary()` に外部辞書パスを渡す API 仕様の確認が実装時に必要
  （未検証）。
- **`config/`**: `scripts/agent/config_builders.py:59` （`__file__` 基準で
  `_CONFIG_DIR` を解決）と `scripts/shared/config_loader.py:74`（`__file__` 基準で
  `repo_root` を解決）がいずれも `__file__` 基準の相対パスで解決している。onefile
  展開後の一時ディレクトリでは崩れるため、実行ファイル隣接ディレクトリまたは環境変数
  （例: `LLMAGENT_CONFIG_DIR`）基準に変更する必要がある。

### 現行デプロイ方式

- `skills/deploy/SKILL.md`: `deploy/deploy.sh`（rsync 同期）→ `deploy/init_db.sh`
  （スキーマ初期化）→ `deploy/setup_services.sh`（サービス起動）の3段階。
  venv 自体は同梱せず `/opt/llm` 側で `uv run` により都度依存解決。
- `.github/workflows/` にバイナリビルド関連の記述は無し（lint/テスト/ドキュメント
  整合性チェックのみ）。

## 提案する作業計画

### Phase 0: 実現性の下調べ（実施済み。結果は「Phase 0 検証結果」参照）
- Nuitka の Python 3.13 対応、および `sudachipy` / `orjson` / `pydantic-core` /
  `lxml` / `PyGithub` / `gitpython` のビルド可否を PoC で確認。

### Phase 1: コード側の設計変更
1. `config_loader.py` / `config_builders.py` のパス解決を環境変数/実行ファイル
   隣接ディレクトリ基準に変更
2. `_SudachiTokenizer` を外部 `system.dic` パス指定方式に変更
3. `config/agent.toml` の10個の `cmd` をバイナリパス形式に書き換え

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

## 設計方針（config ディレクトリ / Sudachi 辞書）

### config ディレクトリの解決（現状の問題）

`__file__` 基準で解決している箇所は以下。onefile 実行時 `__file__` は一時展開先
（`/tmp/onefile_*/`）を指すため、いずれも外部 `/opt/llm/config/` を見失う（Phase 0 で確認）。

| 箇所 | 用途 | 影響 |
|---|---|---|
| `scripts/shared/config_loader.py` `ConfigLoader.__init__` | 全 TOML/JSON 設定の読込（agent・全 MCP サーバー共通の唯一の入口） | 致命的。必ず修正 |
| `scripts/agent/workflow/workflow_loader.py` `WORKFLOWS_DIR` | `config/workflows/` 読込 | 致命的 |
| `scripts/agent/config_builders.py` `_CONFIG_DIR` | `/config` コマンドの表示のみ | 表示のみ。なお `parent.parent` が `scripts/config` を指しており現行でも誤り（別件のドリフト） |
| `scripts/agent/context.py` | 設定読込失敗時のエラーメッセージ用パス | メッセージのみ |
| `scripts/agent/commands/cmd_skill.py` `_skills_dir` | `/skill` 用の `skills/` | `skills/` は配布対象外のため別途要判断 |

### 実装方針（提案）

- 新規モジュール `scripts/shared/paths.py`（名称は実装時に確定）に解決関数を1つ集約し、
  上記全箇所をそこへ寄せる（パス解決ロジックの重複排除）。
- `get_config_dir()` の優先順位:
  1. 環境変数 `LLMAGENT_CONFIG_DIR`（絶対パス。存在しなければ起動時に明示エラー）
  2. 実行ファイル隣接: `Path(sys.argv[0]).resolve().parent.parent / "config"`
     （`/opt/llm/bin/agent` -> `/opt/llm/config`。Phase 0 で onefile 内でも `sys.argv[0]` が
     元バイナリを指すことを確認）
  3. 従来の `__file__` 基準（`uv run` 開発時のフォールバック。リポジトリ直下 `config/`）
- 本番は `/opt/llm/config` が既存のままなので、1 または 2 で互換。
- MCP サーバーはサブプロセス起動のため、`http_lifecycle.py` が `LLMAGENT_CONFIG_DIR` を
  子プロセス環境へ継承する（または親の値をそのまま継承）ことを実装時に確認する。
- `ConfigLoader.__init__(config_dir=...)` の明示引数は従来どおり最優先（テスト互換）。

### Sudachi 辞書の外部配置と絶対パス指定

- 対象: `scripts/rag/repository.py` `_SudachiTokenizer` と
  `scripts/rag/ingestion/chunk_splitter.py` の `Dictionary(dict="core")` 2 箇所。
- 設定キー（例: `rag.sudachi_dict_path`、`config/agent.toml` もしくは
  `rag_pipeline_mcp_server.toml`）に絶対パスを持たせ、環境変数
  `LLMAGENT_SUDACHI_DICT` で上書き可能にする。
  既定値は `/opt/llm/dict/system.dic`。
- 解決は `shared` 側の関数 1 箇所に集約し、未設定または空の場合のみ従来の
  `dict="core"`（開発時 `uv run` 互換）にフォールバックする。
- 指定パスが存在しない場合は起動時に明示エラー（黙って `core` へフォールバックしない。
  onefile では `sudachidict_core` を同梱しないため黙ったフォールバックは失敗を遅延させる）。
- 辞書は `sudachidict-core` の版が `sudachipy` の版と対応している必要がある
  （Phase 0 で版不一致の辞書は `Invalid header version` で失敗することを確認）。
  `deploy` で辞書を抽出する際は、ビルドに使った venv の `sudachidict_core/resources/system.dic`
  を使うこと。

## Phase 0 検証結果（2026-10-06 実施）

環境: WSL2 / Linux、gcc 15、Nuitka 4.2.2、Python 3.13.1（uv 管理の python-build-standalone）。
PoC は scratchpad 内の最小スクリプトで実施し、リポジトリのコードは変更していない。

### 事実（実測）

- Nuitka 4.2.2 は Python 3.13 で `--onefile` ビルドに成功した。
- PoC が import した依存はすべてビルド・実行できた:
  `sudachipy`(0.6.11), `orjson`, `pydantic_core`, `lxml.etree`, `PyGithub`(`github`), `gitpython`(`git`)。
  生成バイナリは約 98MB（`--onefile-no-compression`、辞書・config は含まず）、起動約 1.1 秒。
- `sudachipy.Dictionary(dict=<絶対パス>)` で外部 `system.dic` を指定でき、形態素解析が動作した
  （`config_path` JSON 方式でも可）。存在しないパスはエラーになる。
- ただし外部辞書を絶対パス指定しても、sudachipy は既定の
  `sudachipy/resources/sudachi.json`（および `char.def`/`unk.def`/`rewrite.def`）を常に参照する。
  `resource_dir` を外部に向けても同様に失敗した。このため Nuitka では
  `--include-package-data=sudachipy` が必須（数 KB）。`system.dic`(約 217MB) は
  同梱不要で外部のまま動作した。
- 外部 config: onefile 内の `__file__` は一時展開先を指す。`sys.argv[0]` は元バイナリの
  パスを指すため、実行ファイル隣接 `config/` と環境変数 `LLMAGENT_CONFIG_DIR` による上書きの
  両方が動作した。
- 外部 `/opt/llm/sqlite-vec/vec0.so` を `sqlite3.load_extension()` で onefile 内からロードでき、
  `vec_version()` が返った。

### ビルド環境の注意（事実）

- システム Python（Debian 版）は `python3-dev` 未導入（`Python.h` 無し）のため
  Nuitka でビルドできない。`patchelf` も未導入。今回は sudo 無しで
  uv 管理 Python と pip 版 `patchelf` で回避した。ビルド用ホストに必要な前提として
  `deploy/build_binaries.sh` 側で整備する必要がある。
- 1 バイナリのビルドに約 10 分（ccache 無し、4GB RAM 環境）。11 バイナリの単純な逐次ビルドは
  約 2 時間規模になる。共通依存が重複コンパイルされるため、`ccache` 導入または
  `--onefile` の代わりに standalone 1 ディレクトリ共有方式の検討が必要。
- デフォルトの zstd 圧縮は低メモリ環境（約 3.7GB）で `not enough memory` により失敗した。
  `--onefile-no-compression` で回避。
- `/tmp`（tmpfs 1.9GB）はビルド中間物で枯渇し得る（実際に 1 度 `No space left on device`）。
  `--output-dir` を十分な容量のあるディスクにすること。

### 未検証（不明）

- 実際のエージェント本体および各 MCP サーバー（`fastapi`, `uvicorn`, `trafilatura`,
  `duckduckgo-search`, `httpx` 等を含む）の Nuitka ビルド可否。PoC は上記 6 依存のみ。
  動的 import（`mcp_servers.*`、`agent` 内の遅延 import）に対する `--include-package` の要否は
  Phase 2 で確認が必要。
- `eventbus` 等のパッケージ内データファイル同梱要否。
- 本番相当の起動時間・配布サイズ（11 バイナリ合計）。

### 結論

- 外部 config、外部 Sudachi 辞書（絶対パス）、外部 sqlite-vec の 3 点は技術的に実現可能。
- Phase 1（パス解決の集約、辞書パス設定化）に着手できる。
- ただし 11 バイナリのビルド時間とビルドホストの前提整備（`python3-dev`/`patchelf`/`ccache`）が
  Phase 3 の主要課題になる。

## 敵対的検証結果（2026-10-06）

本書の記載事実を現行コード（master）で再検証した。上記本文は訂正済み。以下は検証で判明した
訂正と、本書が見落としていた論点。

### 訂正した記載（ドリフト）

- 行番号: `repl.py` の `__main__` は156行目（旧162）、`pyproject.toml` の coverage omit は144行目（旧140）。
- Sudachi: `Dictionary(dict="core")` の呼び出しは `repository.py` 55行目と `chunk_splitter.py` 81行目の2箇所のみ
  （旧記載の「81・83行目」の83は `SplitMode.C`）。
- MCP サーバー実ファイル: `file_write`/`file_read` も `file/write_server.py`/`file/read_server.py`
  （`file_delete` だけでない）。
- 依存: shell・file_*・mdq は「標準ライブラリ中心」ではなく全サーバーが `fastapi`/`pydantic` に依存。
  `cicd` は `PyGithub` を使っていない（`httpx` + `orjson`）。Phase 0 の対象依存リストにも `fastapi`,
  `uvicorn`, `httpx`, `trafilatura`, `beautifulsoup4`, `PyYAML` を加える必要がある。

### 新規に判明した阻害要因（事実）

1. **`CommandValidator` の許可リストがバイナリ移行を阻害する。**
   `scripts/agent/http_lifecycle_command_validator.py` は `cmd[0]` を `shutil.which` で解決し、
   実体 basename が許可リスト（`node/npm/npx/uvx/python/pipx/uvicorn` と `python3(.N)`）にあるかを検査する。
   `/opt/llm/bin/mcp_shell` のような名前は拒否され、`bin/` が PATH 上に無い場合は「not found in PATH」でも
   失敗する（dev 環境で直接実行して確認）。バイナリ名の許可方式（例: 許可ディレクトリ配下の絶対パスのみ許可）を
   設計し、セキュリティ検査の弱体化にならないようにする必要がある。
2. **現行 HEAD の検証でも `cmd[0]="uv"` は許可リスト外で拒否される**（dev 環境で直接実行して確認）。
   本番 `/opt/llm/scripts/` は旧版コードで検証経路が異なり、本番での挙動は不明。
   現行構成そのものが検証を通るかは別途確認が必要（本件の前提に影響するため要確認）。
3. **`PyYAML` が本番依存に未宣言。** `mdq/parser.py` が `import yaml` するが、`pyproject.toml` の
   `dependencies` に無く、`uv.lock` 上は `bandit`/`libcst`/`pre-commit` 等の開発依存の推移依存としてのみ存在する。
   本番 `uv sync`（`--no-dev`）や、メイン依存のみで作る Nuitka ビルド環境では欠落してビルド・起動が失敗し得る。
4. **「11バイナリ」に含まれない起動経路が存在する。** 現行デプロイは `uv run python -m ...` を次にも使う:
   `agent.workflow.validate`（`deploy.sh`, `start_agent.sh`, `setup_services.sh`）、
   `db/create_schema.py`（`init_db.sh`）、`python -c`（スキーマ版確認、`setup_services.sh`）、
   `eventbus.app`（`setup_services.sh`、port 8015 の独立サービス）、
   `rag.ingestion.crawler`/`chunk_splitter`/`ingester`（手動実行）。バイナリ化するか、
   `uv run` を残すか、サブコマンド化して本体に統合するかの方針が必要。
5. **`rag_pipeline` の依存は遅延 import。** `sudachipy`/`sqlite-vec` 経路は `rag_pipeline_service.py` 内の
   関数内 import（`rag.pipeline`）で、Nuitka の静的解析で拾われない可能性がある。`--include-package=rag` 等の
   明示が必要になり得る（Phase 2 で検証）。

### 確認できた記載（事実と一致）

- 本番導線 `deploy/start_agent.sh:76` の `uv run python -m agent.repl`、`scripts/agent.py` 削除済み、
  `scripts/agent/__main__.py` の存在。
- MCP サーバー10個、全て `transport="http"`・`startup_mode="subprocess"`・`--no-sync` 付き `cmd`。
- `sqlite_vec_so` が絶対パス設定で、`db/helper.py` の `load_extension` 経由のため変更不要。
- `config_loader.py:74` / `config_builders.py:59` が `__file__` 基準。
- `deploy.sh` が `pyproject.toml`/`uv.lock`/`scripts/`/`config/*.toml`/`schemas/`/`config/workflows/` を配置する構成
  （`config/` は個別 `cp`。onefile 化後も外部配置対象のファイル列挙を維持する必要がある）。
- `mcp_launcher.py` は `walk_packages` で動的発見する単体起動用で、本番導線では未使用。

### Required Changes / Unresolved Questions への反映

- 上記 1〜5 を `## Required Changes` と `## Unresolved Questions` に追記した。

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

- `sudachipy.Dictionary()` の外部 `system.dic` 絶対パス指定は Phase 0 で動作確認済み
  （詳細は「Phase 0 検証結果」）。ただし `sudachipy/resources/*` の同梱が必須。
- `pyproject.toml` の coverage omit に残る `scripts/agent.py` 等の存在しないパス
  記述は本件とは別に整理が必要（ドキュメントドリフト）。
- 11バイナリ分のビルド時間・CI 負荷は Phase 0 の PoC 結果を待って見積もる。

## 関連調査

- 本要望書は 2026-07-17 の Nuitka 化検討セッションでの調査・議論に基づく。
  関連ファイル: `scripts/agent/repl.py`, `scripts/db/helper.py`,
  `scripts/rag/repository.py`, `scripts/shared/config_loader.py`,
  `scripts/agent/config_builders.py`, `scripts/agent/factory.py`,
  `scripts/mcp_launcher.py`, `config/agent.toml`,
  `skills/deploy/SKILL.md`, `deploy/deploy.sh`

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260717-171801 (inferred from git history — first commit adding this file; predates this template's timestamp-prefixed naming convention)
- **Related target files**: see `## Target Files or Areas` above
