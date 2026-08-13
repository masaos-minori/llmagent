---
title: "Shared Runtime and Execution - Config and Logging"
category: shared
tags:
  - shared
  - runtime
  - config-loader
  - config-isolation
  - logger
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# 共有ランタイムと実行基盤

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 1. 目的

`shared/` におけるランタイム基盤とユーティリティを文書化する: 設定読み込み、ロギング、
トークンカウント、OTel トレーシング、git ヘルパー、フォーマッター、ToolExecutor、
および McpServerConfig。

---

## 2. `ConfigLoader` (`shared/config_loader.py`)

ConfigLoader は TOML/JSON ファイルを順に読み込み、`dict.update` で shallow マージする。`_` プレフィックス付きキーは除外される。`ConfigMissingError` / `ConfigParseError` / `ConfigReadError` はいずれも `ValueError` サブクラス。`restrict_to()` が呼ばれている場合、許可セット外のファイルアクセスは `ConfigPermissionError` を発生させる。`load_all()` は `agent.toml` のみを対象とし、`strict=True` で必須ファイル欠落時にエラーとする。

---

## 2a. プロセス分離方針 (Config Isolation Policy)

**各プロセスは自身の設定ファイルのみを読み込む。**

エージェント / 各 MCP サーバー / crawler / ingester / chunk_splitter はそれぞれ独立したプロセスとして動作し、各プロセスは起動時に自身に対応する設定ファイル 1 つだけを `ConfigLoader().load("xxx.toml")` で読み込む。他プロセスの設定ファイルは読み込まない。DB パス・外部サービス URL など複数プロセスが必要とする値は共通ファイルを作らず各プロセスの設定ファイルにそれぞれ記述する。`ConfigLoader.restrict_to(own_config_file)` をプロセス起動直後に呼ぶことでこのルールをランタイムで強制する。MCP サーバーは `MCPServer.run_http()` で `restrict_to()` を呼び出す。crawler/ingester/chunk_splitter は `if __name__ == "__main__"` で呼び出す。eventbus は独自ローダーを使用。

---

## 2b. `RagConfigValidator` / `ProductionConfigValidator` (`shared/config_validator.py`, `shared/production_config_validator.py`)

両バリデータとも `ConfigValidationResult(errors, warnings)` を返す（`ok` プロパティあり）。RAG バリデータは `rag` セクションのクロスファイル整合性（`embedding_dim`/`vec_dim` 不一致、`use_rrf=False`、キャッシュ閾値）を検証。本番バリデータは `security_profile == "production"` のみ違反を error にし、他は `[local/development]` prefix 付き warning に降格。検証項目: `_REQUIRED_STRICT_KEYS` が `False`、`tool_safety_tiers` とレジストリの双方向差分、`allowed_tools == []`。`known_tools` 省略時はレジストリから動的取得を試みる。

**Note:** `config_validator.py` と `production_config_validator.py` はそれぞれ独立した `ConfigValidationResult` データクラスを定義しており共通の型ではない。両者は責務が異なる (RAG 設定の整合性 vs 本番運用の厳格性) ため、混同しないこと。

---

## 3. `Logger` (`shared/logger.py`)

```python
class Logger:
    def __init__(self, name: str, log_file: str, *, structured_log: bool = False)
    def info(self, msg: str, *args, **kwargs) -> None
    def warning(self, msg: str, *args, **kwargs) -> None
    def error(self, msg: str, *args, **kwargs) -> None
    def set_context(self, **kwargs) -> None
    def clear_context(self) -> None
```

- コンストラクタ第2引数名は `log_file` (実装名。旧記載の `filepath` は誤り)
- `name` / `log_file` はいずれも非空文字列であることが必須で、違反時は `ValueError` を送出する (文字列検証関数)
- `FileHandler` + `StreamHandler` を自動設定する (`propagate=False` により重複を防止)
- 同一 `name` のロガーに既にハンドラが設定済みの場合、ロガー初期化処理は何もせず即座に return する (二重登録防止; 同名 `Logger` を複数回生成しても安全)
- `structured_log=True` → ログファイルは JSON Lines 形式になる (`_JsonFormatter`; フィールドは `ts`/`level`/`func`/`msg` に加え `turn_id`/`session_id`/`rag_query_id`/`workflow_id`/`task_id`/`exc` が値のあるもののみ出力される)
- コンテキスト注入: `set_context(turn_id="T001", session_id=42)` により、以降のすべてのログ行にフィールドが追加される。`_ContextFilter` は `contextvars.ContextVar` を使うため、同一ロガーを共有する並行 asyncio タスク間でコンテキストが混線しない
- ファイル書き込みエラー (`OSError`) → `shared.logger.fallback` ロガー経由で WARNING がログされ (stderr に表示される)、StreamHandler のみにフォールバックする; 例外は発生しない
- ログメッセージは**英語のみ**でなければならない (日本語不可) — `rules/coding.md` の規約

---
