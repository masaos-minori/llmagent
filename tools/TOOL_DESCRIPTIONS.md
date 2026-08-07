# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェックとドキュメント整形の一括処理スクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

本ファイル自体の内容ドリフトは `check_tool_descriptions_sync.py` で検出できる(`tools/*.py` とここでの言及の突合)。

## ドメイン別ドキュメント整合性チェッカー

いずれも `_docs_consistency_lib.py` のDocFile/Issue/discover_md_files等を共有し、対象ドメインのdocs/配下のみを独自ロジックでチェックする。ソースコード(`config/agent.toml`、`scripts/mcp_servers/`、`scripts/db/config.py`等)を正本として突き合わせる。

| ファイル | 対象ドメイン | 主なチェック内容 |
|---|---|---|
| `_docs_consistency_lib.py` | (共通基盤、単体実行不可) | DocFile/Issueデータ型、ファイル探索、壊れた内部リンク・削除済みファイル参照・スラッシュコマンドドリフト・ディレクトリ一覧の網羅性・`scripts/`パス参照/関数参照の実在性の汎用チェック |
| `check_agent_docs_consistency.py` | `docs/05_agent_*.md` | DBスキーマ名ドリフト(`scripts/db/schema_sql.py`)、診断イベント名ドリフト(`scripts/agent/`) |
| `check_mcp_docs_consistency.py` | `docs/04_mcp_*.md` | MCPサーバーのポート番号ドリフト、ツール名ドリフト、`scripts/`パス参照・関数参照の実在性 |
| `check_rag_docs_consistency.py` | `docs/03_rag_*.md` | クローラーのmax_depth/max_pages主張と`config/crawler.toml`実値の一致、`[debug]`出力例の実在性、`scripts/`パス参照・関数参照の実在性 |
| `check_deployment_docs_consistency.py` | `docs/02_deployment*.md` | 「NつのSQLiteデータベース」等の個数主張、DB一覧表の網羅性、`*_db_path`設定キーの`agent.toml`実在性、MCPポート範囲の表記(`deploy/*.sh`も対象) |
| `check_overview_docs_consistency.py` | `docs/01_overview*.md` | `conf.d/`ディレクトリ一覧の網羅性(`check_directory_listing_completeness()`の実利用例) |
| `check_needs_confirmation_inventory.py` | `docs/*.md` 全体 | 「Needs confirmation」記載が`00_governance_07`の集中インベントリに登録されているか、resolved済みNC項目の該当箇所にマーカーが残っていないか、フィールド数宣言と実際のリスト項目数の一致 |
| `check_no_compat.py` | `scripts/`, `docs/`, `tests/`, `tools/` | 後方互換スタブ・shimの残存検出 |
| `check_suppression_justification.py` | `scripts/`, `tests/` | `# noqa`/`# type: ignore`/`# nosec` にルール/エラーコードとem-dash(` — `)区切りの正当化理由が伴っているかを検出。`DEFAULT_ALLOWLIST`で既存の非準拠行をベースライン許容 |
| `check_doc_quality.py` | `docs/*.md` 全体 | コアチェック(壊れた見出し、不正なMarkdownテーブル、閉じられていないコードブロック、JSON例のフェンス漏れ、重複見出し番号、Migration Notesの配置、解決済みissueの記載等)+ カスタムルール(`config/doc_quality_rules.json`から動的ロード)。`--core-only`/`--custom-only`/`--skip <check>`/`--only <check>`でフィルタリング可能 |

## リファレンス自動生成スクリプト

ソースコード・設定ファイルの値からdocs/内のリファレンス表を生成し、`<!-- AUTO-GENERATED: ... -->` ガードコメントの間に書き込む。再実行すれば内容が最新化されるため、この区間は手編集しない。`--dry-run` で標準出力のみへの出力も可能。

| ファイル | 生成元 | 反映先 |
|---|---|---|
| `gen_rag_reference.py` | `config/*.toml` | RAGリファレンスセクション(CLI引数ヘルプ等) |
| `gen_mcp_reference.py` | `config/agent.toml` + `scripts/mcp_servers/**/*.py`のTOOL_LIST | `docs/04_mcp_01_tool_ownership_matrix.md`のサーバーポート/ツール数/ツール名表 |
| `gen_deployment_reference.py` | `scripts/db/config.py` + `config/agent.toml` | `docs/02_deployment-part2.md`のDBパス/設定キー表 |

## ドキュメント構造検証・整形補助スクリプト

| ファイル | 概要 |
|---|---|
| `validate_docs_structure.py` | `docs/*.md` の構造規約(ファイルサイズ、H1見出し数、Front Matter、Related Documents/Keywordsセクション、内部 `.md` リンクの到達可能性)を検証する。`uv run python tools/validate_docs_structure.py [glob ...]` |
| `audit_docs.py` | ドキュメント構造検証・整形補助スクリプト: docs/*.md の構造規約を検証する。 |
| `add_missing_frontmatter.py` | `docs/*.md` にYAML Front Matterが存在しないファイルを自動検出し、ファイル名からカテゴリとタイトルを推定してテンプレートを追加する。`--dry-run` で変更内容を表示、`--fix` で実際に適用。 |
| `dedupe_front_matter_lists.py` | `docs/*.md` のYAML Front Matterにあるリストフィールド(`tags`/`related`/`source`)から重複エントリを除去する。初出順は維持し、本文には手を加えない。 |
| `fix_d205.py` | D205(docstringサマリー行の直後に空行がない)を検出し、空行を挿入する一括修正スクリプト。三重引用符文字列の判定を堅牢にし、SQL文字列リテラルの誤検出を回避する。`--dir` でスキャン対象ディレクトリを指定可能。 |
| `check_tool_descriptions_sync.py` | 本ファイル(`TOOL_DESCRIPTIONS.md`)に列挙されたファイル名と実際の`tools/*.py`を突合し、両方向のドリフト(未記載/削除済み参照)を検出する。 |

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
