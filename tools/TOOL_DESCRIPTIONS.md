# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェックとドキュメント整形の一括処理スクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

本ファイル自体の内容ドリフトは `check_tool_descriptions_sync.py` で検出できる(`tools/*.py` とここでの言及の突合)。

## ドメイン別ドキュメント整合性チェッカー

いずれも `_docs_consistency_lib.py` のDocFile/Issue/discover_md_files等を共有し、対象ドメインのdocs/配下のみを独自ロジックでチェックする。ソースコード(`config/agent.toml`、`scripts/mcp_servers/`、`scripts/db/config.py`等)を正本として突き合わせる。

| ファイル | 対象ドメイン | 主なチェック内容 |
|---|---|---|
| `_docs_consistency_lib.py` | (共通基盤、単体実行不可) | DocFile/Issueデータ型、ファイル探索、壊れた内部リンク・削除済みファイル参照・スラッシュコマンドドリフト・ディレクトリ一覧の網羅性・`scripts/`パス参照/関数参照の実在性の汎用チェック |
| `check_docs_consistency.py` | `--domain agent\|mcp\|rag\|deployment\|overview` | 上記5ドメインのチェックを統合。`--skip <check>`で特定チェックをスキップ可能 |
| `check_needs_confirmation_inventory.py` | `docs/*.md` 全体 | 「Needs confirmation」記載が`00_governance_07`の集中インベントリに登録されているか、resolved済みNC項目の該当箇所にマーカーが残っていないか、フィールド数宣言と実際のリスト項目数の一致 |
| `check_no_compat.py` | `scripts/`, `docs/`, `tests/`, `tools/` | 後方互換スタブ・shimの残存検出 |
| `check_suppression_justification.py` | `scripts/`, `tests/` | `# noqa`/`# type: ignore`/`# nosec` にルール/エラーコードとem-dash(` — `)区切りの正当化理由が伴っているかを検出。`DEFAULT_ALLOWLIST`で既存の非準拠行をベースライン許容 |
| `check_doc_quality.py` | `docs/*.md` 全体 | コアチェック(壊れた見出し、不正なMarkdownテーブル、閉じられていないコードブロック、JSON例のフェンス漏れ、重複見出し番号、Migration Notesの配置、解決済みissueの記載等)+ カスタムルール(`config/doc_quality_rules.json`から動的ロード)。`--core-only`/`--custom-only`/`--skip <check>`/`--only <check>`でフィルタリング可能 |

## リファレンス自動生成スクリプト

ソースコード・設定ファイルの値からdocs/内のリファレンス表を生成し、`<!-- AUTO-GENERATED: ... -->` ガードコメントの間に書き込む。再実行すれば内容が最新化されるため、この区間は手編集しない。`--dry-run` で標準出力のみへの出力も可能。

| ファイル | 生成元 | 反映先 |
|---|---|---|
| `gen_reference_table.py` | `--type rag\|mcp\|deployment` で指定 | RAG/MCP/デプロイメントのリファレンスセクション |
| `generate_mcp_inventory.py` | `--format json\|csv` で指定 | エージェント設定からMCPサーバー一覧をJSON/CSVで出力 |

## ドキュメント構造検証・整形補助スクリプト

| ファイル | 概要 |
|---|---|
| `validate_docs_structure.py` | `docs/*.md` の構造規約(ファイルサイズ、H1見出し数、Front Matter、Related Documents/Keywordsセクション、内部 `.md` リンクの到達可能性)を検証する。`uv run python tools/validate_docs_structure.py [glob ...]` |
| `manage_frontmatter.py` | `add-missing` サブコマンドでFront Matter欠落を検知・追加、`dedupe-lists` サブコマンドでリストフィールドの重複エントリを除去 |
| `fix_d205.py` | D205(docstringサマリー行の直後に空行がない)を検出し、空行を挿入する一括修正スクリプト。三重引用符文字列の判定を堅牢にし、SQL文字列リテラルの誤検出を回避する。`--dir` でスキャン対象ディレクトリを指定可能。 |
| `fix_section_mark.py` | `docs/`・`skills/` 配下の Markdown ファイルから節記号 `§`(表示崩れの原因)を除去し、平易な英語表現(`section N`、`sections N-M` 等)に置き換える。`--dir <path...>` でスキャン対象を変更可能(デフォルト `docs skills`)。`--apply` を付けない限り dry-run。 |
| `fix_scripts_docstring_paths.py` | `scripts/**/*.py` のモジュールレベルdocstringヘッダーパスをリポジトリルートからの相対パス（scripts/<relpath>形式）に書き換える。--dry-run で変更内容を表示、--apply で実際に適用。 |
| `check_tool_descriptions_sync.py` | 本ファイル(`TOOL_DESCRIPTIONS.md`)に列挙されたファイル名と実際の`tools/*.py`を突合し、両方向のドリフト(未記載/削除済み参照)を検出する。 |
| `detect_japanese.py` | `docs/` 配下を再帰的に走査し、ひらがな・カタカナ・漢字(`U+3040`-`U+9FFF`)を含むMarkdownファイルを列挙する。`skills/DESIGN.md` §Output language の英語化ポリシー(`docs/`配下は常に英語)への違反箇所を洗い出す用途。 |
| `merge_part_files.py` | `docs/` 内の `-partN.md` 形式分割ファイルを統合する。`find_groups()` で単純ペア(2ファイル)と多パートシリーズ(3ファイル以上)の両方を検出し、それぞれ適切なマージ戦略を適用。`update_internal_refs_for_multi()` でマージ後の内部リンクを更新。 |
| `fix_broken_part_refs.py` | マージ後のドキュメント間で壊れた `-part*.md` 参照を修正する。8つの正規表現パターンでmarkdownリンクURL/テキスト、バッククォート、プレーンテキスト、アンカー、セクション名の各形式に対応。 |
| `apply_fixes.py` | テスト固有の修正スクリプト: `tests/rag/ingestion/test_rag_ingester.py` の行番号ベースの置換を適用。 |
| `rename_modules.py` | `mcp_servers/<server>/` 配下のモジュール名を一括リネームするためのスクリプト。絶対インポート・相対インポート・patchターゲット・ドキュメント文字列の更新を自動処理。 |
| `fix_mocks.py` | テスト固有の修正スクリプト: `tests/rag/ingestion/test_rag_ingester.py` のmock関連修正を正規表現で適用。 |

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
