[作業指示]

- `05_agent-impl-class.md` には現行仕様と旧仕様が混在する記述が残る
  `06_ref-*` ドキュメント群を現行設計仕様の正として、`05_agent-impl-class.md` を修正

- `docs/04_mcp-mdq.md` の下記の記載を確認し、必要であれば実装し、ドキュメント修正
  **注意:** `mcp/mdq/server.py` は現時点で未実装。HTTP サーバとして公開する場合は `MCPServer` サブクラスを実装してポート 8013 で起動すること。

- `scripts/mcp/mdq/*.py` と `scripts/mdq_*.py` の実装は重複ではないか確認
  重複であれば `scripts/mcp/mdq/*.py` を残し、`scripts/mdq_*.py` は削除

- `06_ref-agent-config.md` の下記指摘の修正
  SQLite 接続の不変設定を保持。`build_db_config()` で `_get_cfg()` (= `load_all()` キャッシュ) から生成。**注意: `common.toml` は `load_all()` の読み込み対象に含まれない**。`rag_db_path` / `session_db_path` / `sqlite_vec_so` などのキーが分割設定ファイルに存在しない場合は空文字列になり `__post_init__` で `ValueError` が発生する。実運用では `db/helper.py` や `rag/pipeline.py` が `ConfigLoader().load("common.toml")` を個別に呼ぶことでこれらの値を取得している。この `common.toml` 非統合問題は既知の設計上の非整合であり、将来的な統合を検討中。

- `scripts/` フォルダ以下に不要なファイルがあれば削除

- Python venv は使わない
  - `./deploy/deploy.sh` スクリプトを uv に置き換え
  - `./deploy/init_db.sh` スクリプトを uv に置き換え
  - `./deploy/setup_services.sh` スクリプトを uv に置き換え
  - `docs/02_deproyment.md` の Python venv 構築の記述を削除

- `docs/02_deproyment.md` を現在の実装に合わせ修正
