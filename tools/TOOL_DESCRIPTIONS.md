# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェックとドキュメント整形の一括処理スクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

## 継続的に利用するCI/検証ツール

| ファイル | 概要 |
|---|---|
| `check_doc_quality.py` | ドキュメント品質のCIチェック。コアチェック（壊れた見出し、不正なMarkdownテーブル、閉じられていないコードブロック、JSON例のフェンス漏れ、重複見出し番号、Migration Notesの配置、解決済みissueの記載等）+ カスタムルール（`config/doc_quality_rules.json` から動的ロード）。`--core-only` でコアのみ、`--custom-only` でカスタムのみ、`--skip <check>` / `--only <check>` でフィルタリング。`python tools/check_doc_quality.py [--skip broken_headings] [--only stale_patterns] docs/*.md` |
| `validate_docs_structure.py` | `docs/*.md` の構造規約(ファイルサイズ、H1見出し数、Front Matter、Related Documents/Keywordsセクション、内部 `.md` リンクの到達可能性)を検証する。`uv run python tools/validate_docs_structure.py [glob ...]` |
| `gen_rag_reference.py` | `config/*.toml` の設定値からRAGリファレンスセクションを自動生成し `docs/` に反映する。`--dry-run` で標準出力のみへの出力も可能。 |

## ドキュメント整形補助スクリプト

| ファイル | 概要 |
|---|---|
| `add_missing_frontmatter.py` | `docs/*.md` にYAML Front Matterが存在しないファイルを自動検出し、ファイル名からカテゴリとタイトルを推定してテンプレートを追加する。`--dry-run` で変更内容を表示、`--fix` で実際に適用。 |
| `dedupe_front_matter_lists.py` | `docs/*.md` のYAML Front Matterにあるリストフィールド(`tags`/`related`/`source`)から重複エントリを除去する。初出順は維持し、本文には手を加えない。 |
| `fix_d205.py` | D205(docstringサマリー行の直後に空行がない)を検出し、空行を挿入する一括修正スクリプト。三重引用符文字列の判定を堅牢にし、SQL文字列リテラルの誤検出を回避する。`--dir` でスキャン対象ディレクトリを指定可能。 |

## モジュールドキュメント文字列チェックスクリプト

| ファイル | 概要 |
|---|---|
| `check_all_docstrings.py` | スクリプト配下のPythonファイルのdocstringフォーマットを検証する。em-dash(U+2014)の存在、`scripts/<path> — description`形式の正当性をチェック。docstringの**追加や修正は行わない**。 |

### docstringスクリプトの制限事項

docstringの追加・修正スクリプトは、正規表現によるソースコードの変換を行うため、以下の問題がある：

- **行番号シフト**: docstringの挿入により行番号がずれるため、既存のコードが壊れる
- **UTF-8エンコーディング破損**: em-dash(U+2014)のバイト列が壊れる場合がある
- **二重引用符の混在**: `"""` と `""""""` が混在する状態になる

安全にdocstringを操作するには、`ast` モジュールを使った構文木ベースのアプローチが必要。現在の実装ではdocstringの**追加**は行わず、**既存docstringのフォーマット検証**のみを推奨。
