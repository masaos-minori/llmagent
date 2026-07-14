# tools/ ディレクトリ概要

`tools/` には、ドキュメント整合性のCIチェック、ドキュメント整形の一括処理、および過去のドキュメント分割・復旧作業で使用したスクリプトが格納されている。`AGENTS.md` の方針(同じ操作を3回以上繰り返す場合はスクリプト化して `tools/` に置く)に従って作成されたものが中心。

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

## 過去のドキュメント移行・分割スクリプト(historical、再実行非推奨)

これらは特定時点のドキュメント再構成作業のために一度だけ実行されたスクリプトであり、現在のdocsの状態を前提にしていない。多くは実行済みの記録として残されているのみで、そのまま再実行するとファイル内容や参照関係を壊す可能性がある。

| ファイル | 概要 |
|---|---|
| `apply_policy.py` | 16件のrequireファイルに、Phase 1統合ポリシー(Orchestratorの扱い等)を説明する固定の注記ブロックを追加した一度限りのスクリプト。 |
| `renumber_split_families.py` | 分割済みファイル名に順序番号を挿入して `ls`/辞書順が意図した読み順と一致するようにし、`docs/` および `routing.md` 内の相互参照をあわせて書き換える。`--apply` を付けない限りドライランのみ。 |
| `split_01_arch.py` | `01_overview-arch.md` をH2/H3境界で3ファイルに分割する。 |
| `split_01_files.py` | `01_overview-files.md` をディレクトリ境界で6ファイルに分割する。 |
| `split_05_agent_03_04_06_08.py` | commit `d28e9fdc` のバイトオフセット分割で破損した `docs/05_agent_03/04/06/08` の分割済みファイルを、退避済みのクリーンな原文から再構築する復旧スクリプト。 |
| `split_05_agent_07.py` | 同上の破損を修復する、`docs/05_agent_07_*.md`(11ファイル)向けの復旧スクリプト。`07_01` はオリジナルに対応節がないため、他10ファイルへの短い章内インデックスとして合成する。 |
| `split_05_agent_09_10_11_12.py` | 同上の破損を修復する、`docs/05_agent_09/10/11/12` 向けの復旧スクリプト。 |
| `split_90_shared.py` | `90_shared_01/02/03/04/05` の肥大化したdocsをH2境界で8KB以下に分割し直す復旧スクリプト。 |
| `split_oversized_docs.py` | 8KBを超える任意の `docs/*.md` を、中間点に最も近いH2境界で2ファイルに分割する汎用スクリプト。Front Matterと相互参照を更新する。`uv run python tools/split_oversized_docs.py file1.md file2.md ...` |

**注意:** `split_05_agent_03_04_06_08.py`・`split_05_agent_07.py`・`split_05_agent_09_10_11_12.py`・`split_90_shared.py` はいずれも `ORIG_DIR` として実行当時のセッション固有の `/tmp` スクラッチパッドパスをハードコードしており、そのディレクトリは既に存在しない。再実行はできない。
