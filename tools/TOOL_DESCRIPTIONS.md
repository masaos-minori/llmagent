# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェックとドキュメント整形の一括処理スクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

ファイル名は「動詞+対象」形式に統一している(`check_*` = 合否判定/検出、`fix_*` = 修正適用、`generate_*` = 生成、`manage_*` = 複数サブコマンドでの管理、`merge_*`/`rename_*` = 個別操作)。

本ファイル自体の内容ドリフトは `check_tool_descriptions_sync.py` で検出できる(`tools/*.py` とここでの言及の突合)。

## ドメイン別ドキュメント整合性チェッカー

いずれも `_docs_consistency_lib.py` のDocFile/Issue/discover_md_files等を共有し、対象ドメインのdocs/配下のみを独自ロジックでチェックする。ソースコード(`config/agent.toml`、`scripts/mcp_servers/`、`scripts/db/config.py`等)を正本として突き合わせる。

| ファイル | 対象ドメイン | 主なチェック内容 |
|---|---|---|
| `_docs_consistency_lib.py` | (共通基盤、単体実行不可) | DocFile/Issueデータ型、ファイル探索、壊れた内部リンク・削除済みファイル参照・スラッシュコマンドドリフト・ディレクトリ一覧の網羅性・`scripts/`パス参照/関数参照の実在性の汎用チェック |
| `check_docs_consistency.py` | `--domain agent\|mcp\|rag\|deployment\|overview` | 上記5ドメインのチェックを統合。`--skip <check>`で特定チェックをスキップ可能 |
| `check_needs_confirmation_inventory.py` | `docs/*.md` 全体 | 「Needs confirmation」記載が`00_governance_07`の集中インベントリに登録されているか、resolved済みNC項目の該当箇所にマーカーが残っていないか、フィールド数宣言と実際のリスト項目数の一致 |
| `check_known_deviation_sync.py` | `docs/adr/*.md`, `docs/*_90_inconsistencies_and_known_issues.md` | 各ADRの`## Known Deviations`(および`## Related Documents`→`### Known Issues`)が参照するKnown Issue ID(例: `MCP-004`)について、ADR側のresolved-like/open-likeシグナルと正本(`docs/*_90_inconsistencies_and_known_issues.md`)側のStatusフィールドの不一致、および正本側に該当IDの見出しが存在しないdangling参照を検出する。読み取り専用(検出のみで自動修正は行わない)。`--format json`で機械可読形式の出力にも対応 |
| `check_adr_invariant_matrix.py` | `docs/adr-index.md` | ADR Invariant Verification Matrixの`Verification Status`列に記載されたバッククォート付きpytestノードID(例: `` `tests/agent/test_startup.py::test_name` ``)について、対象ファイルが実在するかを検証する(テスト実行までは行わない)。「no test yet」等のテスト未実装行やコード参照(`.py`のみで`::`を含まないセル)は対象外。読み取り専用。`--format json`で機械可読形式の出力にも対応(GV-014) |
| `check_adr_reference.py` | `docs/adr-index.md`, `scripts/**/*.py` | ADR Invariant Verification Matrixが`scripts/<path>.py`形式でフルパス引用しているソースファイルについて、該当行のADR ID(例: `ADR-004`)への参照コメントがファイル内に存在するかを検証する。パスを伴わない単独のファイル名表記や`tests/*.py::test_name`形式のテストノード引用は対象外。読み取り専用。`--format json`で機械可読形式の出力にも対応(GV-014) |
| `check_workitem_traceability.py` | `issues/`, `plans/`, `implementations/`(各`done/`含む) | 各ドキュメントの`## Traceability`節をパースし、missing-source-file(`Source *`参照先ファイルの不在)・no-plan-yet(未紐付けissue)・no-procedure-yet(未紐付けplan)・stale-target-heuristic(issue記載後に更新された参照先ドキュメントの可能性、判定は候補提示のみ)の4種類を検出する。読み取り専用(`issues/`/`plans/`/`implementations/`配下への書き込み・改名・移動・削除は一切行わない)。`--format json\|csv`で機械可読形式の出力にも対応 |
| `check_compat_shims.py` | `scripts/`, `docs/`, `tests/`, `tools/` | 後方互換スタブ・shimの残存検出 |
| `check_suppression_justification.py` | `scripts/`, `tests/` | `# noqa`/`# type: ignore`/`# nosec` にルール/エラーコードとem-dash(` — `)区切りの正当化理由が伴っているかを検出。`DEFAULT_ALLOWLIST`で既存の非準拠行をベースライン許容 |
| `check_docs_quality.py` | `docs/*.md` 全体 | コアチェック(壊れた見出し、不正なMarkdownテーブル、閉じられていないコードブロック、JSON例のフェンス漏れ、重複見出し番号、Migration Notesの配置、解決済みissueの記載等)+ カスタムルール(`config/doc_quality_rules.json`から動的ロード)。`--core-only`/`--custom-only`/`--skip <check>`/`--only <check>`でフィルタリング可能 |
| `check_docs_japanese.py` | `docs/*.md` 全体 | ひらがな・カタカナ・漢字(`U+3040`-`U+9FFF`)を含むMarkdownファイルを列挙する。`skills/DESIGN.md` §Output language の英語化ポリシー(`docs/`配下は常に英語)への違反箇所を洗い出す用途。 |

## リファレンス自動生成スクリプト

ソースコード・設定ファイルの値からdocs/内のリファレンス表を生成し、`<!-- AUTO-GENERATED: ... -->` ガードコメントの間に書き込む。再実行すれば内容が最新化されるため、この区間は手編集しない。`--dry-run` で標準出力のみへの出力も可能。

| ファイル | 生成元 | 反映先 |
|---|---|---|
| `generate_reference_table.py` | `--type rag\|mcp\|deployment` で指定 | RAG/MCP/デプロイメントのリファレンスセクション |
| `generate_mcp_inventory.py` | `--format json\|csv` で指定 | エージェント設定からMCPサーバー一覧をJSON/CSVで出力 |
| `generate_workitem.py` | `--kind issue\|plan\|implementation-procedure\|unknowns\|risks` で指定 | 対応する`templates/*.md`からプレースホルダーのみのスケルトンを抽出し、命名規則に沿ったパスで`issues/`・`plans/`・`implementations/`に出力(実質的な内容は生成しない)。`unknowns`/`risks`は衝突時`--seq`でゼロパッド連番を明示指定して再試行する(自動連番なし、reject-only) |

## ドキュメント構造検証・整形補助スクリプト

| ファイル | 概要 |
|---|---|
| `check_docs_structure.py` | `docs/*.md` の構造規約(ファイルサイズ、H1見出し数、Front Matter、Related Documents/Keywordsセクション、内部 `.md` リンクの到達可能性)を検証する。`uv run python tools/check_docs_structure.py [glob ...]` |
| `manage_frontmatter.py` | `add-missing` サブコマンドでFront Matter欠落を検知・追加、`dedupe-lists` サブコマンドでリストフィールドの重複エントリを除去 |
| `manage_workitem_stage.py` | `close-issue`/`close-plan`/`close-implementation` の3サブコマンドで、`issues/`→`issues/done/`、`plans/`→`plans/done/`、`implementations/`→`implementations/done/`のアーカイブ移動を`git mv`(GitPython経由)で実行する。`close-implementation`は対象ファイルの`### Execution Status`テーブルに`Pending`行が残っている場合は移動をブロックし、`--force`と`--reason <理由>`を両方指定した場合のみ強制移動する。いずれのサブコマンドもファイル移動のみを行い、ファイル内容(Execution Status行等)の編集は行わない。 |
| `fix_docstring_blank_line.py` | D205(docstringサマリー行の直後に空行がない)を検出し、空行を挿入する一括修正スクリプト。三重引用符文字列の判定を堅牢にし、SQL文字列リテラルの誤検出を回避する。`--dir` でスキャン対象ディレクトリを指定可能。 |
| `fix_docs_section_marks.py` | `docs/`・`skills/` 配下の Markdown ファイルから節記号 `§`(表示崩れの原因)を除去し、平易な英語表現(`section N`、`sections N-M` 等)に置き換える。`--dir <path...>` でスキャン対象を変更可能(デフォルト `docs skills`)。`--apply` を付けない限り dry-run。 |
| `fix_docstring_paths.py` | `scripts/**/*.py` のモジュールレベルdocstringヘッダーパスをリポジトリルートからの相対パス（scripts/<relpath>形式）に書き換える。--dry-run で変更内容を表示、--apply で実際に適用。 |
| `check_tool_descriptions_sync.py` | 本ファイル(`TOOL_DESCRIPTIONS.md`)に列挙されたファイル名と実際の`tools/*.py`を突合し、両方向のドリフト(未記載/削除済み参照)を検出する。 |
| `merge_part_files.py` | `docs/` 内の `-partN.md` 形式分割ファイルを統合する。`find_groups()` で単純ペア(2ファイル)と多パートシリーズ(3ファイル以上)の両方を検出し、それぞれ適切なマージ戦略を適用。`update_internal_refs_for_multi()` でマージ後の内部リンクを更新。 |
| `fix_part_refs.py` | マージ後のドキュメント間で壊れた `-part*.md` 参照を修正する。8つの正規表現パターンでmarkdownリンクURL/テキスト、バッククォート、プレーンテキスト、アンカー、セクション名の各形式に対応。 |
| `rename_mcp_modules.py` | `mcp_servers/<server>/` 配下のモジュール名を一括リネームするためのスクリプト。絶対インポート・相対インポート・patchターゲット・ドキュメント文字列の更新を自動処理。 |
| `rename_doc.py` | `docs/*.md`(`docs/adr/*.md`含む)を`<old-path> <new-path>`引数で`git mv`し、`docs/`配下の全Markdownファイルを走査して該当ファイルへのMarkdownリンクパスを書き換える。オプションの`--old-title`/`--new-title`を両方指定した場合はリンクテキストも置換(非リンクのプレーンテキスト言及は書き換えず報告のみ)。書き込みは`docs/`配下に限定。`--apply`を付けない限り`--dry-run`相当(デフォルト)で変更内容の表示のみ。 |

## モジュールドキュメント文字列チェックスクリプト

| ファイル | 概要 |
|---|---|
| `check_docstrings.py` | スクリプト配下のPythonファイルのdocstringフォーマットを検証する。em-dash(U+2014)の存在、`scripts/<path> — description`形式の正当性をチェック。docstringの**追加や修正は行わない**。 |

### docstringスクリプトの制限事項

docstringの追加・修正スクリプトは、正規表現によるソースコードの変換を行うため、以下の問題がある：

- **行番号シフト**: docstringの挿入により行番号がずれるため、既存のコードが壊れる
- **UTF-8エンコーディング破損**: em-dash(U+2014)のバイト列が壊れる場合がある
- **二重引用符の混在**: `"""` と `""""""` が混在する状態になる

安全にdocstringを操作するには、`ast` モジュールを使った構文木ベースのアプローチが必要。現在の実装ではdocstringの**追加**は行わず、**既存docstringのフォーマット検証**のみを推奨。
