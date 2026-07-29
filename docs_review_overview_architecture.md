# Overview/Architecture領域 設計文書レビュー報告書

## 1. 全体評価

### 連結文書としての問題
- Overview/Architecture領域15ファイルは「アーキテクチャ設計文書(arch-01〜03)」と「ファイル構成カタログ(files-01〜06)」の2系統に大別されるが、後者(特に`files-03-scripts-part2`, `part4`, `part5`, `files-04-shared-part2`)は手動更新のファイル名・ディレクトリツリー転記が中心であり、実コードとの乖離が**推測ではなく確認済みの事実として複数箇所**で発見された。これは「陳腐化しやすい」という一般論ではなく、既に陳腐化している具体的証拠である。
- `01_overview.md`(索引)へのリンク行が各詳細ファイルに重複して存在しており、索引の一元性が崩れている。

### 重複している情報の傾向
- MCPサーバーのポート番号が`01_overview-arch-01-process.md`・`01_overview-files-03-scripts-part5.md`・`01_overview-files-05-config.md`の3箇所に分散重複している。
- 「ワークフロー定義必須・検証失敗で起動/デプロイ中断」という設計判断が`arch-02`・`files-01-build`・`files-03-scripts-part3`(validate.py)の3箇所で異なる角度から説明されている。これは相互補完として妥当な重複だが、根拠レベル(検証済みかどうか)を揃える必要がある。

### コード説明に寄りすぎている領域
- `files-03-scripts-part1〜5`、`files-04-shared-part1〜2`、`files-05-config`、`files-06-misc`の「ファイル名+一言コメント」形式のディレクトリツリーは、設計判断をほとんど伝えておらず、grep一発で得られる情報を長々と転記しているに過ぎない。加えてこの領域こそが実装との乖離が集中的に見つかった箇所であり、維持コストに見合っていないことが裏付けられた。
- `arch-03`の実装済み機能サマリ表(ファイルパス列挙)も同様の性質を持つ。

### 意図・境界・運用注意として残すべき領域
- `arch-01`の設定ファイル分離方針、`arch-02`のターン内処理順序・MCP起動モード(fail-fast/fail-open分岐)、`arch-03`のメモリレイヤー4モード・sqlite-vec適用範囲、`files-01-build`のデプロイ時fail-fastチェック、`files-06-misc`のconf.dセキュリティデフォルトは、いずれも実装者が誤解すると障害・セキュリティ事故に直結する設計判断であり、コードで裏付けが取れたものは正確に残すべきである。

### 再構成の基本方針
1. 手動維持のファイル名・ディレクトリツリーは本文から排除し、「実装ツリーを参照する」旨の一文に統一する(既に一部ファイルで実践済みの方針を全ファイルに拡大)。
2. ポート番号・サーバー台数などの「代表値」は正本を1箇所(`agent.toml`/`files-05-config.md`)に定め、他ファイルは数値を書かず参照のみとする。
3. 実コードと矛盾する断定的記述(ツールルーティング二段階説明、`_FORBIDDEN_KEYS`等)は最優先で修正または「Needs confirmation」化する。
4. dataclassフィールド逐語列挙など、コードの単純転写はReference API/コードdocstringへ移し、本文には設計意図の要約のみ残す。

---

## 2. 削除候補

### 削除候補: docs/01_overview-files-03-scripts-part2.md / L27-63 commandsディレクトリツリー全体
- 現在の記述の問題: `db_help_display.py`・`db_stats_display.py`・`db_rag_ops.py`が現行コードに存在しない(`__pycache__`の`.pyc`のみ残存、コミット`846dc93b`で削除)。`registry.py`の「15 mixins」は誤りで実際は12個。`cmd_tooling.py`の「/tool」コマンド、`cmd_rag_export.py`の「/rag, /export」コマンドも実装に存在しない。**これらは推測ではなく確認済みの誤り**である。
- 削除理由: 機械的ファイル一覧であり、かつ既に複数箇所で事実と食い違っている。誤情報を残すことの害の方が大きい。
- 削除しても失われない情報: mixin構造による責務分割という設計意図(「/help, /config, /stats等の主要コマンドと対応するmixin構造」)。
- 移動先: 実装ツリー参照に委ね、本文にはmixin構造の設計意図のみ残す。

### 削除候補: docs/01_overview-files-03-scripts-part4.md / L36-42(web_search)、L63-93(github)
- 現在の記述の問題: web_searchは文書の`server.py`/`tools.py`/`models.py`が実際には`web_search_server.py`/`web_search_tools.py`/`web_search_models.py`/`web_search_service.py`であり、さらに`web_search_service.py`・`health.py`・`metrics.py`の3ファイルが未掲載。githubも`server.py`→`github_server.py`等、3ファイルで同様の乖離。**確認済みの誤り**。
- 削除理由: リネームが文書に反映されないまま放置されている機械的一覧。
- 削除しても失われない情報: 共通基盤(models.py/dispatch.py/tool_validators.py)の拡張ポイントとしての役割説明。
- 移動先: 実装ツリー参照。共通基盤部分のみ設計意図として本文に残す(4章参照)。

### 削除候補: docs/01_overview-files-03-scripts-part5.md / L27-82 ディレクトリツリー全体
- 現在の記述の問題: shell/rag_pipeline/cicd/mdq/gitの各MCPサーバーで文書は`server.py`/`service.py`/`tools.py`/`models.py`という汎用名だが、実際は`shell_server.py`/`cicd_server.py`/`mdq_server.py`/`git_server.py`/`rag_pipeline_server.py`のようにサービス名接頭辞付き。`db_fts.py`はpycacheの残骸のみで実在しない。**確認済みの誤り**。
- 削除理由: 命名規則そのものが実態と乖離しており、誤情報として害が大きい機械的列挙。
- 削除しても失われない情報: MCPサーバー名⇔ポート対応(要約候補として05-configへ集約)。
- 移動先: 実装ツリー参照。ポート対応は`files-05-config.md`に一元化。

### 削除候補: docs/01_overview-files-03-scripts-part3.md / L52-58 dataclassフィールド逐語列挙
- 現在の記述の問題: `ServiceWarning`, `ToolApprovalEvent`等のdataclass全フィールドを本文に列挙している。これは方針書が明示的に禁止する「コードに書いてあるだけの内容」の典型例。
- 削除理由: 設計判断ではなく、フィールド追加のたびに陳腐化する機械的情報。
- 削除しても失われない情報: 「監査イベント系のデータモデル(承認イベント・ツール実行イベント)が`agent/shared/models.py`に集約されている」という責務境界の要約。
- 移動先: Reference API/コードdocstring。本文は1文要約に圧縮。

### 削除候補: docs/01_overview-files-04-shared-part2.md / L26-71 ファイルツリー全体
- 現在の記述の問題: `config_utils.py`・`runtime_tool.py`・`runtime_tool_registry.py`の3ファイルが実在するにもかかわらず記載がなく、既に更新漏れが生じている。
- 削除理由: 手動維持ファイル一覧の維持コストが実証的に見合っていない。
- 削除しても失われない情報: ドリフト検証・ヘルスゲート・キャッシュ戦略という設計意図(3章参照)。
- 移動先: 実装ツリー参照。

### 削除候補: docs/01_overview-files-04-shared-part1.md / L33-46、docs/01_overview-files-05-config.md / L27-45、docs/01_overview-files-06-misc.md / L27-45(ファイル名列挙部分)
- 現在の記述の問題: 実コードと完全一致は確認できたが(現時点では陳腐化していない)、grep代替可能な機械的列挙であることに変わりはない。
- 削除理由: 対象範囲が狭く現状は正確だが、更新のたびに同様の乖離リスクを抱える。
- 削除しても失われない情報: DB分割意図・設定ファイルとポート対応・eventbus復旧フロー(3章で要約候補として扱う)。
- 移動先: 実装ツリー参照+要約文への置き換え。

---

## 3. 要約候補

### 要約候補: docs/01_overview-arch-01-process.md / L70-84 サービス一覧表
- 現在の問題: モデル名・ポート番号は`config/agent.toml`が最終権威であり陳腐化しやすい上、表の件数と本文L47「11サーバ」の記述が食い違っている。
- 要約方針: 表は「アーキテクチャ上の位置づけの説明」に限定し、「代表値であり実際の接続先は`agent.toml`を正本とする」という注記を冒頭に強調する。件数の断定は避ける。
- 要約後のサンプル: 「以下は代表的な構成例であり、正確なポート・モデル対応は`config/agent.toml`を正本とする。」

### 要約候補: docs/01_overview-arch-02-pipelines.md / L45-50 クエリパイプライン実装補足
- 現在の問題: ツールループガードの異常種別4つを列挙するなど詳細度が高く、本文の主題(パイプライン全体像)から逸脱している。
- 要約方針: 各項目を1行に圧縮し、詳細仕様は`agent/tool_loop_guard.py`または`05_agent_*`系詳細文書への参照リンクに委ねる。
- 要約後のサンプル: 「ツールループガードは異常な繰り返し呼び出しパターンを検出し強制終了させる(詳細は`agent/tool_loop_guard.py`参照)。」

### 要約候補: docs/01_overview-arch-03-features.md / L28-42 実装済み機能サマリ表
- 現在の問題: `files-03-scripts`系のファイル一覧表と内容が重複しており、ファイル名変更のたびに二重に追従が必要。
- 要約方針: Canonical Source Ruleに従い、ファイル対応の正本は`files-03-scripts`側とし、本ファイルは機能名とディレクトリ名(ファイル名までは書かない)の対応のみに絞る。
- 要約後のサンプル: 「メモリ機能 → `agent/memory/`(詳細ファイル対応はdocs/01_overview-files-03-scripts-part1.md参照)」

### 要約候補: docs/01_overview-files-02-rag.md / L27-34 ディレクトリ構成
- 現在の問題: 命名規則自体は状態遷移を示す価値ある情報だが、`registered/`配下の保持方針が書かれていない。
- 要約方針: 命名規則は残しつつ、保持方針が未確認である旨をNeeds confirmationとして明記する一文を追加。
- 要約後のサンプル: 「`registered/`配下のファイル保持期間・クリーンアップ方針は本ドキュメント範囲では未確認(要確認)。」

### 要約候補: docs/01_overview-files-06-misc.md / L27-45 eventbusファイル名列挙
- 現在の問題: `broker.py`/`offsets.py`/`dlq.py`/`replay_route.py`等の一言コメント列挙にとどまり、失敗時・復旧時のフローが読み取れない。
- 要約方針: ファイル名列挙を削り、配信失敗→DLQ退避→リプレイという復旧フローの説明に置き換える。
- 要約後のサンプル: 「配信に失敗したメッセージはDLQ(`dlq.py`)に退避され、`replay_route.py`のエンドポイント経由で再送できる。」

### 要約候補: docs/01_overview-files-04-shared-part2.md / ツールキャッシュ・ヘルスゲート関連記述
- 現在の問題: `tool_cache.py`(LRU+TTL)、`mcp_health.py`、`tool_transport_invoker.py`のファイル名羅列にとどまり採用理由が書かれていない。
- 要約方針: 「サーバーのヘルス状態によってツール呼び出しをゲートする」「重複呼び出し削減とステールデータ回避のトレードオフでTTLキャッシュを採用」という設計方針を1〜2文で要約。
- 要約後のサンプル: 「MCPサーバーのヘルス状態に応じてツール呼び出しをゲートする仕組みがあり(`mcp_health.py`)、頻繁な再呼び出しはTTL付きLRUキャッシュ(`tool_cache.py`)で緩和している。」

---

## 4. 残す・強化する記述

### 強化候補: docs/01_overview-arch-02-pipelines.md / L64-70「ワークフローは常時必須」
- 残す理由: フォールバック経路が存在しないという不変条件であり、設計判断として最重要。
- 強化すべき観点: 根拠として挙げている`_FORBIDDEN_KEYS`(`build_agent_config()`)は**確認済みの誤り**(リポジトリ全体をgrepしても存在しない)。断定的な実装詳細への言及を避け、コードで裏付けが取れる`deploy.sh`/`setup_services.sh`の`[FATAL]`チェックと`RuntimeError`起動中断を根拠として書き直す。
- 追記例: 「ワークフロー定義はデプロイ時(`deploy/deploy.sh`)・起動時(`setup_services.sh`のテーブル存在確認)の両方でfail-fastチェックされ、欠落時は`[FATAL]`でexit 1する。」

### 強化候補: docs/01_overview-arch-03-features.md / L62-70「セッション終了時の診断保存」
- 残す理由: 復旧時・障害時の考え方(WALチェックポイント)に関わる重要情報。
- 強化すべき観点: WAL TRUNCATEチェックポイントの失敗時にどうなるか(次回起動時の挙動、データ損失リスク)が書かれていない。
- 追記例: 「WAL TRUNCATEに失敗した場合でもプロセスは終了するが、次回起動時にWALファイルが肥大化した状態から再開する(データ損失は想定されないが要監視)。」(※実装確認の上で記述、未確認ならNeeds confirmationとする)

### 強化候補: docs/01_overview-files-04-shared-part1.md / L29-31「rag.sqlite/session.sqlite/workflow.sqlite」
- 残す理由: 状態の正本の所在を示す最重要情報。
- 強化すべき観点: 単一DBでなく3分割にした理由(ロック競合回避/バックアップ単位分離/スキーマ独立性)が本文にない。
- 追記例: 「3DBに分割しているのは、書き込み頻度の異なるデータ(セッション状態・ワークフロー状態・RAGインデックス)間でのロック競合を避けるため(要設計者確認)。」

### 強化候補: docs/01_overview-files-04-shared-part2.md / `events.py`「(配送機構なし)」
- 残す理由: 誤解しやすい重要な制約(型定義のみで配送責務を持たない)。
- 強化すべき観点: 実際の配送責務を担うコンポーネント(eventbus?)が明記されていない。
- 追記例: 「`events.py`はイベント型定義のみを提供し、実際の配送は`scripts/eventbus/broker.py`が担う。」

### 強化候補: docs/01_overview-files-05-config.md / `agent.toml`・`file_read_mcp_server.toml`・`shell_mcp_server.toml`
- 残す理由: 設定振り分け基準・セキュリティ制約の正本所在という重要情報。
- 強化すべき観点: (1)agent.tomlと個別MCPサーバーtoml間の設定振り分け基準、(2)許可リスト変更時の承認フロー・運用ルールが書かれていない。
- 追記例: 「許可ディレクトリ/許可コマンドの変更は原則コードレビューを経て`conf.d/`側の設定と合わせて更新すること(誤って緩めると意図せぬファイル/コマンド実行を許可するリスクがある)。」

### 強化候補: docs/01_overview-files-06-misc.md / `conf.d/`の説明
- 残す理由: 実際の`conf.d/`(`cicd-mcp`, `git-mcp`, `web-search-mcp`, `github-mcp`の4ファイル)のうち、`git-mcp`には「`allowed_repo_paths`が空のとき全リポジトリアクセス拒否(fail-closed)」「`read_only=true`がデフォルト」という**重要なセキュリティデフォルト**が実装されている(実読で確認済み)。これは実装者が誤解すると意図せぬ書き込み許可等の重大な障害につながる。
- 強化すべき観点: 現状`github-mcp`のみ記載で他3ファイルが欠落しているため、4ファイル全てとそのセキュリティデフォルト値を本文に反映する。
- 追記例: 「`conf.d/`には`github-mcp`・`cicd-mcp`・`git-mcp`・`web-search-mcp`の4設定が存在する。特に`git-mcp`は`allowed_repo_paths`未設定時に全リポジトリアクセスを拒否するfail-closed設計であり、`read_only=true`がデフォルトである。」

### 強化候補: docs/01_overview-files-03-scripts-part1.md / L67-71「変更時の注意点」
- 残す理由: 実装者が見落としがちな連動変更ポイントを示す、設計書として最も価値の高い部類の記述。
- 強化すべき観点: 同様の記述を他ファイル(services/, workflow/等)にも拡充する方向が望ましい。
- 追記例: 「`idempotency_ops.py`は同一イベントの二重処理防止、`attempt_ops.py`はステージ実行リトライ回数管理を担う(責務混同に注意)。」

---

## 5. Before / After 書き換え例

### 例1: MCPサーバー台数の記述
- Before(docs/01_overview-arch-01-process.md L47): 「11 サーバ (:8004〜:8014)」
- After: 「MCPサーバー群(:8004〜:8014、ただし:8011は未使用)。正確な台数・ポート対応はdocs/01_overview-files-05-config.mdを正本とする。」
- 書き換え理由: `config/agent.toml`の`[mcp_servers.*]`は実際には10個であり(8011欠番)、「11」という件数は**確認済みの誤り**。数値の正本を1箇所に集約し、他箇所は参照のみにすることで今後の乖離を防ぐ。

### 例2: ツールルーティングの優先順位
- Before(docs/01_overview-arch-03-features.md L54-56): 「ルーティング優先順位は (1) 起動時の`/v1/tools` live discovery マップ、(2) `shared/tool_registry.py`の静的レジストリ、の二段階フォールバック」
- After: 「`RuntimeToolRegistry`(`shared/route_resolver.py`)が唯一のルーティング権威である。起動時の`/v1/tools` discoveryマップはvalidation専用でルーティングには使われず、静的レジストリ(`tool_registry.py`)は現状参照されない(config `tool_names`はドリフト検証専用)。」
- 書き換え理由: `shared/route_resolver.py`のdocstringに「the sole routing authority」「discovery_map is validation-only, never used by resolve()」「ToolRegistry is no longer consulted here」と明記されており、現行の二段階フォールバック説明は**推測ではなく確認済みの事実誤り**。実装者が誤ったフォールバック挙動を前提に障害対応すると誤診断につながるため最優先で修正すべき。

### 例3: commandsディレクトリのファイル一覧
- Before(docs/01_overview-files-03-scripts-part2.md L30, L47, L50, L55-58): 「registry.py … (15 mixins)」「cmd_tooling.py # /tool, /plan コマンド」「cmd_rag_export.py # /rag, /export, /compact コマンド」「db_help_display.py」「db_stats_display.py」「db_rag_ops.py」
- After: 「commands/配下は`/help`・`/config`・`/stats`等の主要スラッシュコマンドを責務別mixin(現在12種類)に分割して実装している。完全なファイル一覧・対応コマンドは実装ツリー(`scripts/agent/commands/`)を参照する。」
- 書き換え理由: mixin数(15→実際12)、`/tool`・`/rag`・`/export`コマンドの実体不在、`db_help_display.py`等3ファイルの非実在は全て**確認済みの誤り**(該当ファイルは`__pycache__`の`.pyc`のみ残存、削除コミット`846dc93b`済み)。逐語列挙をやめ実装ツリー参照に委ねることで再陳腐化を防ぐ。

### 例4: MCPサーバーファイル名(web_search/github)
- Before(docs/01_overview-files-03-scripts-part4.md L36-42): 「server.py / tools.py / models.py / search_provider.py / formatters.py」
- After: 「web_search/配下は共通基盤(models.py, dispatch.py, tool_validators.py)の上に各サービス実装(`web_search_server.py`等、サービス名接頭辞付き)を積む構成。完全なファイル一覧は実装ツリーを参照する。」
- 書き換え理由: 文書記載のファイル名は現行コードに存在せず(実際は`web_search_server.py`/`web_search_tools.py`/`web_search_models.py`/`web_search_service.py`)、かつ`health.py`・`metrics.py`が未掲載という**確認済みの誤り**。githubディレクトリでも同様の接頭辞リネームの反映漏れがある。

### 例5: conf.d/の記述
- Before(docs/01_overview-files-06-misc.md 該当箇所): 「conf.d/(github-mcp用の systemd 環境変数設定)」
- After: 「conf.d/にはgithub-mcp・cicd-mcp・git-mcp・web-search-mcpの4設定が存在する。特にgit-mcpは`allowed_repo_paths`未設定時に全リポジトリアクセスを拒否するfail-closed設計であり、`read_only=true`がデフォルトである(セキュリティ上重要)。」
- 書き換え理由: 実際の`conf.d/`には4ファイルが存在するが本文は1件のみ記載しており記載漏れ(確認済み)。特にgit-mcpのセキュリティデフォルトは運用上の注意として省略できない重要情報であり、単なる記載漏れの修正にとどまらず強化が必要。

---

## 6. Needs confirmation 一覧

### A. 確認済みの事実誤り(推測ではなく実コード突合により確定、優先度高)

#### Needs confirmation: docs/01_overview-arch-03-features.md L54-56「ツールルーティング優先順位」
- 確認したいこと: 「(1)live discovery→(2)静的レジストリ」という二段階フォールバック説明を、実装(`RuntimeToolRegistry`単独権威)に合わせて全面的に修正してよいか。
- 現在の根拠: `scripts/shared/route_resolver.py`のdocstring・実装。
- 不確実な理由: これは記述側の誤りであることが実装確認で確定しているため「不確実」ではなく「誤り確定」。書き換えの承認のみ必要。
- 誤っていた場合の影響: 実装者が誤ったフォールバック挙動を前提に障害調査・改修を行い、誤診断・誤修正につながる。
- 推奨対応: 「例2」の書き換え案で即修正。

#### Needs confirmation: docs/01_overview-arch-01-process.md L47「11サーバ」
- 確認したいこと: 実装(10サーバ、8011欠番)に合わせて件数表記を訂正してよいか。
- 現在の根拠: `config/agent.toml`の`[mcp_servers.*]`、サービス一覧表(10行)。
- 不確実な理由: 件数の食い違いは確認済みだが、8011が「将来使用予定の欠番」なのか「廃止済み」なのかは文書からは判断できない。
- 誤っていた場合の影響: 運用者がポート8011に何かが動いていると誤認し、障害調査で無駄な確認工数が発生する。
- 推奨対応: 8011の扱いを設計者に確認の上、「例1」の書き換え案を適用。

#### Needs confirmation: docs/01_overview-arch-02-pipelines.md L66「`workflow_mode`は`_FORBIDDEN_KEYS`に含まれ`ConfigLoadError`で起動不可」
- 確認したいこと: `_FORBIDDEN_KEYS`という機構は現存するか、実装変更で削除されたか、そもそも記述が最初から誤りだったか。
- 現在の根拠: リポジトリ全体をgrepしても`_FORBIDDEN_KEYS`という識別子は存在しない。
- 不確実な理由: 「ワークフロー常時必須」という結論自体は`deploy.sh`/`setup_services.sh`の`[FATAL]`チェックで別途裏付けられるが、根拠として挙げているこの実装詳細は確認できない。
- 誤っていた場合の影響: 実装者が存在しないコードパスを前提にトラブルシュートし、時間を浪費する。
- 推奨対応: 「4章 強化候補arch-02」の書き換え案(deploy.sh/setup_services.shベースの根拠に差し替え)を適用。

#### Needs confirmation: docs/01_overview-files-03-scripts-part2.md 全体
- 確認したいこと: `/rag`・`/export`・`/tool`コマンド、`db_help_display.py`/`db_stats_display.py`/`db_rag_ops.py`は意図的な機能廃止か、別ファイルへの再配置か。
- 現在の根拠: git logでコミット`846dc93b`(「remove dead RAG pipeline settings ... and unused /db rag /rag commands」)を確認。`__pycache__`に`.pyc`のみ残存。
- 不確実な理由: 廃止自体は確認できたが、後継機能の有無(`/db`関連が別ファイルに統合されたか完全廃止か)は本レビュー範囲では判断できない。
- 誤っていた場合の影響: 廃止された機能の説明を読んだ利用者が存在しないコマンドを使おうとする。
- 推奨対応: 文書更新担当者に実装状況の再確認を依頼し、「例3」の書き換え案を適用。

#### Needs confirmation: docs/01_overview-files-03-scripts-part4.md(web_search/github)、docs/01_overview-files-03-scripts-part5.md(shell/rag_pipeline/cicd/mdq/git)
- 確認したいこと: ファイル名の`_prefix`付けリネームがドキュメント更新なしに行われた経緯、および他のmcp_servers配下(file/等)に同様の見落としがないかの横断確認。
- 現在の根拠: 実コード(`scripts/mcp_servers/{web_search,github,shell,rag_pipeline,cicd,mdq,git}/`)との突合で、複数ファイルの命名不一致・記載漏れを確認済み(誤り自体は確定)。
- 不確実な理由: リネームの経緯・意図(API互換性への影響有無)は本レビュー範囲外で未確認。
- 誤っていた場合の影響: 実装者が文書のファイル名で検索・grepして見つからず混乱する。
- 推奨対応: 「例4」の書き換え案を適用しつつ、file/等未確認ディレクトリの横断チェックを実施する。

#### Needs confirmation: docs/01_overview-files-03-scripts-part5.md「db_fts.py」
- 確認したいこと: `db_fts.py`の機能が`db_grep.py`か`db_schema.py`のどちらに統合されたか、あるいは完全に廃止されたか。
- 現在の根拠: `scripts/mcp_servers/mdq/__pycache__/db_fts.cpython-313.pyc`が残存(過去に実在した証拠)。
- 不確実な理由: 統合先・削除経緯が本レビュー範囲では特定できない。
- 誤っていた場合の影響: FTS機能の所在を誤解し、機能追加時に誤った箇所を修正する。
- 推奨対応: 実装担当者に統合先を確認の上、記述を修正。

#### Needs confirmation: docs/01_overview-files-04-shared-part2.md「config_utils.py, runtime_tool.py, runtime_tool_registry.py」欠落
- 確認したいこと: この3ファイルが意図的に文書範囲から除外されているのか、単なる更新漏れか。
- 現在の根拠: `scripts/shared/`に実在するが本文に記載なし。
- 不確実な理由: 除外基準(公開APIでないため等)が文書からは読み取れない。
- 誤っていた場合の影響: これらのファイルの責務(特に`runtime_tool_registry.py`はルーティング関連の可能性があり、arch-03の誤りとも関連しうる)が文書に反映されず、設計理解に欠落が生じる。
- 推奨対応: 3ファイルの責務を確認し、要約候補として本文に追加するか除外理由を明記する。

#### Needs confirmation: docs/01_overview-files-06-misc.md「conf.d/記載漏れ」
- 確認したいこと: `cicd-mcp`・`git-mcp`・`web-search-mcp`の3ファイルが意図的に本文から省かれたのか単なる更新漏れか。
- 現在の根拠: 実際の`conf.d/`には4ファイル存在するが本文は`github-mcp`のみ記載(実読で確認済み、誤り自体は確定)。
- 不確実な理由: 除外意図は不明だが、内容自体(fail-closed, read_only=trueデフォルト)は確認済みであり事実誤りというより記載漏れに分類される。
- 誤っていた場合の影響: git-mcpのセキュリティデフォルトが実装者に伝わらず、`allowed_repo_paths`設定を誤解して意図しないアクセス制御になるリスク。
- 推奨対応: 「例5」の書き換え案を適用し、4ファイル全てを本文に反映する。

#### Needs confirmation: docs/01_overview-files-03-scripts-part1.md「repository_gateway.pyの分類漏れ」
- 確認したいこと: `repository_gateway.py`が責務別ファイル一覧表のどのカテゴリにも記載されていない点は意図的省略か更新漏れか。
- 現在の根拠: 実コードに存在し、かつ「変更時の注意点」(L70)には言及があるが、表本体には無い。
- 不確実な理由: 存在は把握されているのに表に無い理由が読み取れない。
- 誤っていた場合の影響: ファイル一覧表の網羅性への信頼が損なわれる程度で影響は小さいが、更新時に反映漏れが継続するリスク。
- 推奨対応: 表への追加を推奨。

---

### B. 執筆者の意図確認が必要な項目(設計判断の背景が未記載、事実誤りではない)

#### Needs confirmation: docs/01_overview-files-02-rag.md「registered/配下の保持方針」
- 確認したいこと: `registered/`配下ファイルの保持期間・削除方針。
- 現在の根拠: 本ファイル単体には運用ポリシーの記載がなく、他文書(`03_rag_*`系)にあるか未確認。
- 不確実な理由: 本レビュー範囲外の文書を確認していないため。
- 誤っていた場合の影響: ディスク容量の運用判断を誤る可能性。
- 推奨対応: `03_rag_*`系文書の確認、なければ運用者への聞き取り。

#### Needs confirmation: docs/01_overview-files-04-shared-part1.md「rag.sqlite/session.sqlite/workflow.sqliteの3DB分離理由」
- 確認したいこと: 3DB分離がロック競合回避目的か関心分離目的か。
- 現在の根拠: 文書に理由の記載なし。
- 不確実な理由: 設計者の意図が文書化されていない。
- 誤っていた場合の影響: 将来DB構成を変更する際に本来の分離意図を損なう設計変更をしてしまう可能性。
- 推奨対応: 設計者への確認、確認後に4章の追記例を反映。

#### Needs confirmation: docs/01_overview-files-04-shared-part2.md「ドリフト検証失敗時の挙動」
- 確認したいこと: `tool_registry.py`/`tool_routing_validation.py`のドリフト検知後、起動をブロックするのか警告ログのみか。
- 現在の根拠: コード概観だけでは断定できず。
- 不確実な理由: 実装の詳細動作を追い切れていない。
- 誤っていた場合の影響: 障害対応時にドリフト検知が致命的エラーか単なる警告かの判断を誤る。
- 推奨対応: 実装確認の上で本文に明記。

#### Needs confirmation: docs/01_overview-files-05-config.md「agent.tomlと個別MCPサーバーtomlの設定振り分け基準」
- 確認したいこと: 何を共通設定(agent.toml)にし何を個別設定にするかの判断基準。
- 現在の根拠: 文書に明記なし。
- 不確実な理由: 設計者の意図が言語化されていない。
- 誤っていた場合の影響: 将来の設定追加時に一貫性のない配置がなされる。
- 推奨対応: 設計者への確認。

#### Needs confirmation: 3DB分離理由・ツールキャッシュ/ヘルス管理の設計判断とアーキテクチャ文書側の重複有無
- 確認したいこと: `files-04-shared-part1/2`の設計判断が`arch-01`等アーキテクチャ文書側で既に説明されているか。
- 現在の根拠: 今回のレビュー対象(arch-01〜03)を通読した範囲では該当する説明は見当たらなかったが、悉皆確認はしていない。
- 不確実な理由: レビュー範囲・時間の制約。
- 誤っていた場合の影響: 重複記述が生じ、修正漏れのリスクが増す。
- 推奨対応: 次回レビュー時にarch系文書との重複有無を確認する。
