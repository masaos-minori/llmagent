# Deployment領域 設計文書レビュー報告書

対象: docs/02_deployment-part1.md, docs/02_deployment-part2.md(計2ファイル)
方式: 全文精読 + 実コード(deploy/*.sh, config/agent.toml, scripts/db/*.py, pyproject.toml等)との突合

---

## 1. 全体評価

- 連結文書としての問題
  - 両ファイルとも H1 見出し「# 導入手順・デプロイ」が重複しており、統合ビュー生成時に見出し衝突が起きる構造になっている。
  - docs/02_deployment-part2.md のfrontmatter `source` がpart1自身を指しており、自己参照になっていない(コピー時の修正漏れの可能性)。
  - part1(環境構築・起動)とpart2(DB初期化・失敗モード)の間で、DB構成・ホスト構成の前提が食い違っている(後述)。分割自体は妥当だが、両ファイルを跨ぐ「このデプロイガイドが単一ホスト完結を前提としているのか、複数ホスト構成(embed-llm/agent-llmは別ホスト)を前提としているのか」という上位の設計前提がどちらにも明記されていない。

- 重複している情報の傾向
  - スクリプトのコメント・処理内容をほぼ逐語的に本文へ転記している箇所が複数ある(依存パッケージ一覧、deploy.shの処理列挙、init_db.shの責務列挙)。これらは実装が変わるたびに文書が追随できず陳腐化するリスクが高い。

- コード説明に寄りすぎている領域
  - part1 §1.2 の requirements.txt全文列挙、§1.1/§1.3 のOSパッケージ導入・cmakeビルド手順、§2.2 のdeploy.sh処理列挙。いずれも「コードを読めば分かる」水準の情報であり、設計判断を含まない。

- 意図・境界・運用注意として残すべき領域
  - part1: sqlite-vec配置パスと`agent.toml`キーの一致制約、ワークフロー成果物のfail-closed設計(disable/fallbackなし)、setup_services.shの起動前チェック順序、MCPサーバのsubprocess自動起動という責務境界。
  - part2: デプロイメントチェックリスト、失敗モード表とRunbook/ADRへの参照導線。

- 再構成の基本方針
  - 「手順・一覧」はコード側コメントやRunbookに委譲し、本文には「何が正本か」「どこで失敗が止まるか」「別ホスト前提などの隠れた運用前提」だけを残す。
  - 特に今回発見した実コードとの不一致(誤記・欠落)は、通常の要約・削除判断より優先して先に是正する必要がある。文書の再構成より前に、事実誤りの修正を先行させるべき。

---

## 2. 削除候補

### 削除候補: docs/02_deployment-part1.md / §1.2 requirements.txt全文列挙(41〜55行目)

- 現在の記述の問題: `/opt/llm/venv/requirements.txt` の内容を本文に丸ごと転記しているが、リポジトリ内に `requirements.txt` は存在しない。依存管理は `pyproject.toml`/`uv.lock` に一本化されており、`deploy/deploy.sh` も `requirements.txt` には一切触れない。
- 削除理由: **推測ではなく確認済みの誤り**である。存在しないファイルの内容を提示しており、読者を誤った運用(pip install -r requirements.txt等)に導くリスクがある。列挙されている `langdetect` も未使用パッケージ。
- 削除しても失われない情報: 直前の `uv sync --dev --system-certs` の記述で依存導入の手順は完結しており、実質的な情報損失はない。
- 移動先: 不要(誤情報のため削除)。もし過去のpip運用の名残であれば、Known Issues等に「廃止済み」として一行のみ記録する。

### 削除候補: docs/02_deployment-part1.md / §2.2「deploy.sh does:」箇条書き(106〜110行目)

- 現在の記述の問題: `deploy/deploy.sh` のコピー処理を逐語的に列挙しているだけで、grep一発で分かる内容。
- 削除理由: コードの説明であり設計判断を含まない。スクリプト変更時に文書側の追随漏れが発生しやすい。
- 削除しても失われない情報: なし。詳細はdeploy.sh自身のコメントに既に同等の記述がある。
- 移動先: 本文には「ランタイム成果物(スクリプト・設定・スキーマ)をコピーし、必要ディレクトリを作成する」の一文要約のみ残し、詳細は deploy/deploy.sh のコメントを正とする。

### 削除候補: docs/02_deployment-part1.md / §1.1 Gentooパッケージ一覧・emergeコマンド、§1.3 cmakeビルドコマンド

- 現在の記述の問題: OS依存のインストール手順であり、設計判断ではなくプロビジョニング手順。バージョンアップ等で陳腐化しやすい。
- 削除理由: 設計書としての性質(判断・境界・制約の伝達)に寄与しない純粋な手順情報。
- 削除しても失われない情報: 「Pythonのsqlite3がロード拡張非対応の場合のUSEフラグ対応」という、sqlite-vec採用の設計判断に直結する注記は残す必要があるため、これは削除対象から除外する。
- 移動先: セットアップ/プロビジョニング用Runbook。

---

## 3. 要約候補

### 要約候補: docs/02_deployment-part1.md / §1.4 LLMモデル取得テーブル(77〜81行目)

- 現在の問題: モデル名とファイル名の対応を機械的に列挙しているのみで、かつ内部に不整合がある(後述Needs confirmation参照)。
- 要約方針: 「埋め込み用・LLM用のモデルは `/opt/llm/models/` に配置し、`agent.toml` の対応キーと一致させる」という原則のみ本文に残し、具体的なファイル名一覧は別表またはReference APIに切り出す。
- 要約後のサンプル:
  > モデルファイルは `/opt/llm/models/` 配下に配置し、ファイル名は `agent.toml` の `embed_model_path`/`llm_model_path`(キー名は要確認)と一致させること。現行の対応表には用途とファイル名の不一致が確認されているため、詳細は別途モデル管理表を参照(Needs confirmation: モデル対応表参照)。

### 要約候補: docs/02_deployment-part1.md / §2.3 起動手順コマンド群・ヘルスチェックcurlコマンド(133〜140行目)

- 現在の問題: 逐語コマンドが並び、設計意図(なぜこの順序で起動確認するか)が埋もれている。
- 要約方針: 詳細な逐語コマンドは運用Runbookへ寄せ、本文には起動確認の目的・対象のみを残す。
- 要約後のサンプル:
  > サービス起動後、embed-llm/agent-llmそれぞれについてヘルスチェックエンドポイントへの疎通を確認する。具体的なコマンド例は運用Runbookを参照。

### 要約候補: docs/02_deployment-part2.md / §3.1「init_db.shの責務」箇条書き(36〜40行目)

- 現在の問題: スクリプトのコメントとほぼ同一の逐語列挙になっている。ただし冪等性・全5テーブル確認・スキーマバージョン記録という判断根拠を含むため全削除は不適切。
- 要約方針: 「何を確認し、何が欠けたら中止するか」という判断基準だけ残し、確認手順の詳細(`sqlite3 .tables`の出力例など)はRunbookに委ねる。
- 要約後のサンプル:
  > init_db.sh は冪等に実行可能で、各DBの必須テーブルとスキーマバージョンを確認したうえで、欠落があれば処理を中止する(fail-closed)。確認対象テーブルの詳細はRunbook参照。

---

## 4. 残す・強化する記述

### 強化候補: docs/02_deployment-part1.md / §2.1 sqlite-vec配置パスの制約

- 残す理由: `config/agent.toml` 9行目の `sqlite_vec_so` キーと実在一致を確認済み。正本(配置パスと設定キーの一致という制約)を明示した重要な記述。
- 強化すべき観点: `deploy/build_sqlite_vec.sh` のコメントが「common.toml」という**存在しないファイル**を参照している誤りがある(config/common.tomlは存在せず、実際はagent.toml)。設計書側の記述(agent.tomlとの一致)は正しいため、この整合性を「設計書が正、スクリプト側コメントは要修正」と明記し、スクリプト修正の起票につなげる注記を追加するとよい。
- 追記例:
  > vec0.so の配置パスは `config/agent.toml` の `sqlite_vec_so` と一致させること(agent.tomlが正)。なお `deploy/build_sqlite_vec.sh` のコメントは古い記述(`common.toml`)を参照しており誤りである(別issue管理)。

### 強化候補: docs/02_deployment-part1.md / §2.2 Workflow artifact responsibilities(fail-closed設計)

- 残す理由: 「disable/fallback/workflow-optionalモードは存在しない」という明文化は、`deploy.sh` の実装(存在チェック・バリデーション・チェックサム照合・失敗時exit 1)と完全一致を確認済み。まさに設計判断を伝える文書の核。
- 強化すべき観点: 現状すでに十分だが、失敗時のexit codeやログ文字列(part2 §3.3参照)への相互参照リンクを追加すると、読者が失敗モード表に迷わず辿れる。
- 追記例:
  > ワークフロー定義の検証・チェックサム照合に失敗した場合の挙動・ログ文字列は「失敗モードと復旧」(docs/02_deployment-part2.md)を参照。

### 強化候補: docs/02_deployment-part1.md / §2.3 冒頭「deploy/setup_services.sh initializes the LLM services.」

- 残す理由: setup_services.shが何をするかは本来重要な記述だが、現状の一文は実装と一致しない。
- 強化すべき観点: **確認済みの実装不一致**。`setup_services.sh` の該当処理(74〜83行目)は
  ```bash
  for svc in embed-llm agent-llm; do
      echo "  起動: ${svc}"
  done
  ```
  という同一内容のecho文が重複しているだけで、実際にプロセスを起動する処理は存在しない。さらに `config/agent.toml` では `embed_url = "http://192.168.11.238:8081"`、`llm_url = "http://192.168.11.197:8080"` となっており、embed-llm/agent-llmは**別ホスト上で動く外部サービス**である。つまりこのデプロイパイプラインはLLMサーバをローカルで起動していない。この事実がpart1のどこにも説明されておらず、読者は「setup_services.shを実行すればLLMも起動する」と誤解しかねない。
- 追記例:
  > embed-llm/agent-llmの起動・プロセス管理はこのデプロイパイプラインの範囲外であり、`agent.toml` の `embed_url`/`llm_url` が指す別ホスト上で個別に起動・運用する(起動手順は別途Runbook参照)。`setup_services.sh` はローカルでLLMプロセスを起動しない(ログ出力のみ)。

### 強化候補: docs/02_deployment-part2.md / §3.0 DB一覧・パス管理の前提

- 残す理由: 「DBパスはagent.tomlで一元管理」という前提は運用上重要な設計判断であり残すべきだが、現状の記述は不正確。
- 強化すべき観点(2点、いずれも確認済み):
  1. 「All paths are configured in `agent.toml`」とあるが、`rag_db_path`・`session_db_path`・`eventbus_db_path` はagent.tomlに実在する一方、`workflow_db_path` はagent.tomlに一切記載がなく、`scripts/db/config.py` のデータクラスのデフォルト値(`"/opt/llm/db/workflow.sqlite"`)にのみ依存している。
  2. 「The agent uses three SQLite databases」とあるが、`config/agent.toml`の`eventbus_db_path`、`scripts/db/create_schema.py`の`create_eventbus_schema()`、`deploy/init_db.sh`58行目のeventbus.sqliteテーブル確認(`events`テーブル)の存在から、実質4つ(rag/session/workflow/eventbus)である。
- 追記例:
  > エージェントは4種類のSQLiteデータベース(rag.sqlite / session.sqlite / workflow.sqlite / eventbus.sqlite)を使用する。このうち `workflow_db_path` のみ agent.toml に明示設定がなく、`scripts/db/config.py` のデフォルト値(`/opt/llm/db/workflow.sqlite`)が正となる。deploy先のDBディレクトリとこのデフォルト値がずれた場合、サイレントに別パスを参照する点に注意。

### 強化候補: docs/02_deployment-part2.md / §3.3 失敗モード表の「症状」列

- 残す理由: 失敗モード表自体とRunbook/ADRへのリンク導線(59〜62行目)は「詳細を本文に持たず参照先に逃がす」という理想的な構成であり、残すべき。リンク先アンカーの実在は確認済み。
- 強化すべき観点: **確認済みの不一致**。表中の症状文字列(例: 「[FATAL] Invalid workflow definition」「[FATAL] Checksum does not match source」「[FATAL] Schema is missing or incomplete」「[FATAL] Schema version mismatch」)は実際のスクリプトのログ文字列と一致しない。実際の文字列は以下の通り。
  - `deploy.sh`: `[FATAL] Workflow definition failed validation; aborting deployment.`
  - `deploy.sh`: `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.`
  - `init_db.sh`/`setup_services.sh`: `[FATAL] Workflow database schema is missing or incomplete.`
  - `setup_services.sh`: `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.`

  表がコードブロック風の表記になっているため、運用者が「この文字列でgrepすれば見つかる」と誤解する恐れがある。
- 追記例:
  > 下表の「症状」列は要約ラベルであり、grep用の完全一致文字列ではない。実際のログ文字列は各スクリプト([deploy.sh](../deploy/deploy.sh) 等)を参照するか、正確な文字列を表に転記して同期する。

---

## 5. Before / After 書き換え例

### 例1: requirements.txt全文列挙の削除

- Before(docs/02_deployment-part1.md §1.2、41〜55行目相当):
  ```
  requirements.txt には以下を記載する:
  fastapi==...
  langdetect==...
  ...(全文列挙)
  ```
- After:
  > 依存パッケージは `pyproject.toml`/`uv.lock` に一本化して管理する(`uv sync --dev --system-certs` で導入完結)。
- 書き換え理由: 記載されている `requirements.txt` はリポジトリに存在せず、確認済みの誤り。存在しないファイルを正本のように示すことは実装者を誤った運用に導くため、正しい依存管理方式(uv)の一文に置き換える。

### 例2: setup_services.shのLLM起動記述の是正

- Before(docs/02_deployment-part1.md §2.3):
  > `deploy/setup_services.sh` initializes the LLM services.
- After:
  > `deploy/setup_services.sh` はワークフロー成果物の検証・DB/スキーマの事前確認を行った後、agent-managedなMCPサーバ(port 8004-8014)を起動する。embed-llm/agent-llmは `agent.toml` の `embed_url`/`llm_url` が指す別ホスト上で個別に起動・運用されるプロセスであり、このスクリプトはローカルでLLMプロセスを起動しない。
- 書き換え理由: 実装(echoのみで実起動なし)とagent.tomlの別ホストURLから、LLMサーバの起動責務がこのデプロイパイプラインの範囲外であることが確認済み。読者の誤解(「このスクリプトでLLMも起動する」)を防ぐため。

### 例3: DB一覧「3つ」の是正

- Before(docs/02_deployment-part2.md §3.0):
  > The agent uses three SQLite databases. All paths are configured in `agent.toml`.
- After:
  > The agent uses four SQLite databases: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite. Paths for rag/session/eventbus are configured in `agent.toml`; `workflow_db_path` has no explicit entry in `agent.toml` and instead falls back to the code-side default (`scripts/db/config.py`, `/opt/llm/db/workflow.sqlite`) — a mismatch here is silent.
- 書き換え理由: eventbus.sqliteの存在(agent.tomlのキー、create_schema.pyの生成関数、init_db.shのテーブル確認)およびworkflow_db_pathの設定不在は、いずれもコード側で確認済みの事実であり、本文の前提と食い違っている。

### 例4: 失敗モード表の症状列の是正

- Before(docs/02_deployment-part2.md §3.3、表内):
  > `[FATAL] Invalid workflow definition`
- After:
  > `[FATAL] Workflow definition failed validation; aborting deployment.`(deploy.sh の実際のログ文字列。表の他の症状文字列も同様に実文字列へ揃えるか、「要約ラベルでありgrep用ではない」と明記する)
- 書き換え理由: 運用者が障害調査時にログをgrepする際、表記載の文字列では一致せず調査が滞るおそれがある。実際の文字列と揃えることで障害対応の実効性を担保する。

### 例5: deploy.sh処理列挙の要約

- Before(docs/02_deployment-part1.md §2.2、106〜110行目):
  > deploy.sh does:
  > - Copies pyproject.toml to /opt/llm/
  > - Copies uv.lock to /opt/llm/
  > - Copies scripts/ to /opt/llm/scripts/
  > - Copies config/ to /opt/llm/config/
  > - Creates required directories
- After:
  > deploy.sh は本番稼働に必要なランタイム成果物(依存定義・スクリプト・設定・スキーマ)を `/opt/llm/` 配下にコピーし、必要なディレクトリ構成を作成する。詳細な対応関係は `deploy/deploy.sh` のコメントを正とする。
- 書き換え理由: コードを読めば分かる内容を逐語転記しており、スクリプト変更時に追随できず陳腐化する。要点(何のためにコピーするか)のみ残し、詳細はコード側に委譲する。

---

## 6. Needs confirmation 一覧

### 確認済みの事実誤り(推測ではなく、コード突合により確定)

これらは通常の「著者の意図確認」より優先度が高い。文書の是正が必要であることは確定しており、確認すべきは「正しい値・意図は何か」のみである。

#### Needs confirmation: requirements.txt全文列挙(docs/02_deployment-part1.md §1.2)
- 確認したいこと: このrequirements.txt記述がいつの時点の運用の名残か、削除して問題ないか。
- 現在の根拠: リポジトリ内に `requirements.txt` が存在しないこと、`deploy.sh` がこのファイルに一切触れないことをファイル検索・grepで確認済み。
- 不確実な理由: 誤りである確度は高いが、CI等の別経路で今も使われている可能性はゼロではないため著者確認が必要。
- 誤っていた場合の影響: 実装者が存在しないファイルの編集や `pip install -r requirements.txt` 実行を試み、環境構築に失敗する。
- 推奨対応: 該当ブロックを削除し、依存管理はuv(pyproject.toml/uv.lock)に一本化されている旨を一文で残す。

#### Needs confirmation: モデル対応表の内部矛盾(docs/02_deployment-part1.md §1.4)
- 確認したいこと: 「Qwen2.5-Coder-7B (LLM)」という用途表記と、ファイル名「Qwen3.6-Instruct-Q4_K_M.gguf」のどちらが実際にデプロイされるモデルか。
- 現在の根拠: 文書内の表自体でモデル系統・バージョン・用途(Coder vs Instruct)が一致していないことを確認済み(ドキュメント内在の矛盾であり実装との突合ではない)。
- 不確実な理由: 実際に配置されているモデルファイルを実環境で確認できていないため、どちらが正か断定できない。
- 誤っていた場合の影響: 実装者が誤ったモデルファイルを取得・配置し、埋め込み/生成品質の劣化や起動時のモデル不一致エラーにつながる。
- 推奨対応: 著者に実際に `/opt/llm/models/` へ配置されているファイル名を確認してもらい、表を修正する。

#### Needs confirmation: LLMサーバ(embed-llm/agent-llm)起動責務の欠落(docs/02_deployment-part1.md §2.3)
- 確認したいこと: embed-llm/agent-llmの起動・運用は本当にこのデプロイパイプラインの範囲外(別ホスト・別手順)なのか、その場合の起動手順書はどこにあるか。
- 現在の根拠: `setup_services.sh` の該当処理がecho文のみで実起動処理を持たないこと、`agent.toml` の `embed_url`/`llm_url` が本デプロイ対象ホストとは異なるIPアドレスを指していることを確認済み。
- 不確実な理由: 「別ホストで運用される」という設計自体はコードから読み取れるが、その運用手順・起動責任者・監視方法についての記述がリポジトリ内に見当たらず、意図的な省略か記載漏れか不明。
- 誤っていた場合の影響: 実装者が「setup_services.shを流せばLLMも起動する」と誤解し、本番投入時にLLMサーバ未起動のまま運用開始してしまう。
- 推奨対応: embed-llm/agent-llmの起動手順・責任範囲を明記した節(またはRunbookへのリンク)を追加する。

#### Needs confirmation: 失敗ログ文字列の不一致(docs/02_deployment-part2.md §3.3)
- 確認したいこと: 失敗モード表の症状列は意図的な要約表記なのか、実際のログ文字列と揃えるべきなのか。
- 現在の根拠: 表記載の文字列(`[FATAL] Invalid workflow definition` 等)と、`deploy.sh`/`init_db.sh`/`setup_services.sh` の実際のログ出力文字列が異なることをgrepで確認済み。
- 不確実な理由: 表がコードブロック風表記のため「完全一致文字列」に見えるが、著者の意図が要約なのか引用なのか文書からは判断できない。
- 誤っていた場合の影響: 障害対応時に運用者がログをgrepしても該当行がヒットせず、調査が遅延する。
- 推奨対応: 実際のログ文字列に揃えるか、「要約ラベルでありgrep用の完全一致文字列ではない」と明記する。

#### Needs confirmation: DB台数「3つ」記述とeventbus.sqliteの欠落(docs/02_deployment-part2.md §3.0)
- 確認したいこと: Event Busのデータベース(eventbus.sqlite)をDB一覧から意図的に除外しているのか(別サブシステム扱い)、単なる更新漏れか。
- 現在の根拠: `config/agent.toml` の `eventbus_db_path`、`scripts/db/create_schema.py` の `create_eventbus_schema()`、`deploy/init_db.sh` 58行目のeventbus.sqliteテーブル確認処理の存在を確認済み。本章が対象とする `init_db.sh` 自体がeventbus.sqliteを初期化している。
- 不確実な理由: Event Busを意図的に別文書の管轄とする設計判断がどこかに存在する可能性はあるが、part1/part2のいずれにもその説明がない。
- 誤っていた場合の影響: 運用者がDB復旧・バックアップ対象を「3つ」と誤認し、eventbus.sqliteを復旧対象から漏らす。
- 推奨対応: 表に第4行(eventbus.sqlite)を追加するか、除外が意図的である場合はその理由を明記する。

#### Needs confirmation: `workflow_db_path`のagent.toml不記載(docs/02_deployment-part2.md §3.0)
- 確認したいこと: workflow.sqliteのパスをagent.tomlに明示しない運用が意図的な設計(コード側デフォルトを正とする)か、設定ファイルへの追記漏れか。
- 現在の根拠: `config/agent.toml` に `workflow_db_path` キーが存在しないこと、`scripts/db/config.py` がデフォルト値 `/opt/llm/db/workflow.sqlite` にフォールバックする実装であることを確認済み。
- 不確実な理由: 意図的な省略(他の3DBと異なる管理方針)である可能性を排除できない。
- 誤っていた場合の影響: deploy先のDBディレクトリ構成を変更した場合、workflow.sqliteだけがサイレントに別パスを参照し、他のDBとの不整合(参照エラー・データ分断)に気づきにくい。
- 推奨対応: 著者に意図を確認のうえ、「workflow_db_pathはコード側デフォルトが正本」である旨を明記するか、agent.tomlに明示設定を追加する。

---

### 通常の確認事項(著者の意図確認が必要な項目)

#### Needs confirmation: GitHub操作のAPIキー設定手順(docs/02_deployment-part1.md §2.3)
- 確認したいこと: 「GITHUB_TOKENを`conf.d/github-mcp`に設定」という手順が実際に存在するか。
- 現在の根拠: リポジトリ全体を検索したが `conf.d` への参照は見当たらず、`scripts/mcp_servers/github/service_init.py`・`scripts/mcp_servers/cicd/service_init.py` は `os.environ.get("GITHUB_TOKEN", ...)` による環境変数直接参照のみを確認。
- 不確実な理由: Gentoo/OpenRCの `conf.d` 慣習を指している可能性があるが、対応するinitスクリプトが本リポジトリに存在しないため未確認。
- 誤っていた場合の影響: 実装者が存在しない設定ファイルを探して設定に失敗し、GitHub連携機能が動作しない。
- 推奨対応: 実際の設定手順(環境変数か、外部のOpenRC設定か)を著者に確認し、正確な設定方法に修正する。

#### Needs confirmation: MCPポート範囲の表記ゆれ(docs/02_deployment-part1.md §2.3 / deploy/setup_services.sh)
- 確認したいこと: MCPサーバのポート範囲は「8004-8014」(part1本文、agent.tomlの実測ポートと一致)が正しいか、`setup_services.sh` コメントの「8004-8016」(Event Bus・未使用ポート8016を含む)が正しいか。
- 現在の根拠: `config/agent.toml` の各MCPサーバセクションのURLポートは8004〜8014の範囲に収まることを確認済み。
- 不確実な理由: コメント側の意図(将来の拡張予定を含めているのか、単なる書き間違いか)が不明。
- 誤っていた場合の影響: 運用者がファイアウォール設定等でポート範囲を誤って開放・制限する。
- 推奨対応: 著者に確認のうえ、ドキュメントとスクリプトコメントの表記を一致させる(現状は設計書側の記述が実態に近いと考えられる)。

#### Needs confirmation: build_sqlite_vec.shコメントの参照ファイル誤り(deploy/build_sqlite_vec.sh 41行目、part1と関連)
- 確認したいこと: `common.toml: sqlite_vec_so = ...` というコメントが指すファイルは実際には何か。
- 現在の根拠: `config/common.toml` というファイルは存在せず、実際の該当キーは `config/agent.toml` にあることを確認済み。part1本文の記述(agent.tomlと一致)はこちらが正しいと考えられる。
- 不確実な理由: スクリプト側コメントが古い設計(common.tomlという名前が過去に存在した可能性)の名残か、単純な書き間違いか不明。
- 誤っていた場合の影響: 実装者がconfig/common.tomlを探して見つからず混乱する程度で、実害は限定的だが保守性を損なう。
- 推奨対応: deploy/build_sqlite_vec.sh側のコメントを `agent.toml` に修正する別issueを起票する。

---

## 複数ファイルにまたがる重複・矛盾(横断確認事項)

- part2のfrontmatter `source` がpart1を指しており自己参照になっていない(コピー時の修正漏れの疑い)。
- 両ファイルのH1見出し重複(統合ビュー生成時の見出し衝突リスク)。
- part1(embed-llm/agent-llmは別ホスト前提)とpart2(DB構成)の双方に共通する上位の欠落として、「このデプロイガイドが単一ホスト完結を前提とするか、複数ホスト構成を前提とするか」という設計前提がpart1/part2いずれにも明記されていない。関連文書としてリンクされている docs/01_overview.md で扱うべき内容の可能性があるが、少なくとも本レビュー対象の2ファイルには複数ホスト構成の説明が存在しない。著者に、この前提をどの文書に明記すべきか確認することを推奨する。
