# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェックとドキュメント整形の一括処理スクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

## 継続的に利用するCI/検証ツール

| ファイル | 概要 |
|---|---|
| `check_docs_consistency.py` | RAGドキュメント品質のCIチェック。壊れた見出し、不正なMarkdownテーブル、閉じられていないコードブロック、JSON例のフェンス漏れ、廃止済みコマンド名、解決済みissueの記載漏れ等を検出する。`python -m scripts.checks.check_docs_consistency [--fix]` |
| `check_mcp_docs_consistency.py` | MCPドキュメントのドリフト検出CIチェック。`pyproject.toml` の `check-mcp-docs` エントリポイントとして登録済み(`uv run check-mcp-docs`)。startup mode妥当性、fail-open文言、ルーティング権威記述、既知issueへのクロスリファレンス、ツール数の一致など多数のチェック項目を `--skip` オプションで個別に無効化できる。 |
| `check_no_compat.py` | 後方互換性の残骸(re-exportスタブ、旧importパスである `rag.models`/`rag.llm`、モジュールレベルの `_cfg` キャッシュ参照等)を検出するCIチェック。`python -m scripts.checks.check_no_compat [--allowlist <path>]` |
| `validate_docs_structure.py` | `docs/*.md` の構造規約(ファイルサイズ、H1見出し数、Front Matter、Related Documents/Keywordsセクション、内部 `.md` リンクの到達可能性)を検証する。`uv run python tools/validate_docs_structure.py [glob ...]` |
| `gen_rag_reference.py` | `config/*.toml` の設定値からRAGリファレンスセクションを自動生成し `docs/` に反映する。`--dry-run` で標準出力のみへの出力も可能。 |

## ドキュメント整形補助スクリプト

| ファイル | 概要 |
|---|---|
| `dedupe_front_matter_lists.py` | `docs/*.md` のYAML Front Matterにあるリストフィールド(`tags`/`related`/`source`)から重複エントリを除去する。初出順は維持し、本文には手を加えない。 |
| `fix_d205.py` | D205(docstringサマリー行の直後に空行がない)を検出し、空行を挿入する一括修正スクリプト。 |
| `fix_d205_v2.py` | `fix_d205.py` の改良版。三重引用符文字列の判定をより堅牢にし、モジュールdocstring・関数docstring双方に対応する。 |
