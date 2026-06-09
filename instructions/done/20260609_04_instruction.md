# 改修計画書

文書名: サービス層分離・設定反映標準化・互換機能削除に関する改修計画書
対象ファイル: `config_reload.py` / `mcp_install.py` / `mcp_status.py` / `ingest_workflow.py`

## 1. 目的

本改修の目的は、対象 4 ファイルに分散して残存する表示責務、CLI 入出力責務、移行期の互換機能、文字列ベースの状態表現、設定辞書への直接反映処理を整理し、サービス層の責務を明確化したうえで、保守性・テスト容易性・設計整合性を向上させることである。`mcp_install.py` には CLI 入力抽象と手順表示が共存し、`mcp_status.py` には probe と table formatting が同居し、`config_reload.py` には legacy 直呼び前提の service sync と多数の cfg 直接更新処理が存在し、`ingest_workflow.py` には lazy import・段階別例外握り込み・可変 result 更新が残っている。

## 2. 改修の基本方針

### 2.1 全体方針

1. サービス層から表示・対話・環境依存の責務を除去し、構造化データの生成と業務ロジックの実行に役割を限定する。`McpInstallService` は現在 `ScaffoldResult` の返却に加えて `print_next_steps()` を持ち、`McpStatusService` は status probe に加えて固定幅 table の整形を行っているため、これらは分離対象とする。
2. 設定再読込は `dict[str, Any]` をサービスが直接解釈する方式を縮退させ、差分適用・型変換・反映結果記録を分離した構成へ移行する。`ConfigReloadService.apply_config_dict()` は複数の helper を経由して `ctx.cfg` を直接更新し、さらに `sync_services()` を呼んでいる。
3. 後方互換性のために残されている入口、旧構成前提、legacy 呼出し前提は削除する。特に `sync_services()` はコメント上で legacy code から直接呼ばれることが前提化されており、今回の改修で排除対象とする。
4. 例外処理は「例外文字列を result に格納するのみ」の形から見直し、段階、原因、通知、ログ出力を明確化する。`IngestWorkflowService` は `crawl` / `split` / `ingest` の各段で `Exception` を包括捕捉し、`result.error = str(e)` としている。

### 2.2 適用原則

1. UI 文言、CLI 入力、テーブル整形、運用手順出力は Presentation / Adapter 層に移動する。`CliInstallQA` および `print_next_steps()`、`format_table()` は整理対象とする。
2. 文字列の暗黙変換や既定値強制上書きを避け、型付き DTO または検証層を介した反映へ統一する。`config_reload.py` の `int()`, `float()`, `bool()` 反映は代表的対象である。
3. 旧互換のためだけに存在する分岐、入口、キー受理、運用メッセージは削除する。

## 3. 現状整理

### 3.1 `config_reload.py` の現状

`ConfigReloadService` は `apply_config_dict()` を入口として、`_apply_rag_tool_params()`、`_reload_approval_settings()`、`_apply_mcp_url_reload()`、`_apply_llm_prompt_params()`、`_apply_sse_reload_params()` を順次実行し、最後に `sync_services()` で live service に対して適用している。`sync_services()` はコメント上で `apply_config_dict and directly by legacy code` と位置付けられている。さらに、LLM、履歴管理、tools、conversation prompt まで 1 クラスで横断的に更新している。

### 3.2 `mcp_install.py` の現状

`McpInstallService.run()` は `InstallQA` を通じて `port`、`role`、`with_confd` の入力を受け、`install_mcp_server()` などを呼び出して `ScaffoldResult` を生成する。一方で同クラスは `print_next_steps()` を持ち、`scripts/mcp/...`、`deploy/deploy.sh`、`deploy/setup_services.sh`、`/etc/init.d/...`、`rc-update`、`rc-service` を前提とする手順を直接出力している。`CliInstallQA` は interactive な `input()` と事前指定値の両方を同一クラスで扱っている。

### 3.3 `mcp_status.py` の現状

`McpStatusService.probe_all()` は configured MCP servers を走査し、HTTP transport の場合は `GET {url}/health` で状態確認し、stdio transport の場合は `ctx.services.stdio_procs` から生存状態を判定する。その後、`health_registry` から health state を取得して `status = f"{status}/{health_label}"` と連結し、`McpServerStatus` を生成している。さらに `format_table()` により固定幅文字列テーブルを組み立てている。`_tier_label_for_server()` は tool safety tiers から最高リスク tier を算出して表示ラベルへ変換している。

### 3.4 `ingest_workflow.py` の現状

`IngestWorkflowService.run()` は crawl、split、ingest の 3 段階を順番に実行し、結果を `IngestResult` に集約して返却する。`_crawl()` では URL とローカルファイルを判定し、`WebCrawler` を lazy import して処理する。`_split_and_ingest()` では `ChunkSplitter`、必要時には `ConfigLoader`、さらに `RagIngester` を lazy import し、`run_in_executor()` を用いて処理している。各段階の失敗時には `stage` と `error` を更新するが、ログ出力や原因分類は限定的である。`logger` は定義されているが、実際の出力利用は見えない。

## 4. 課題

### 4.1 アーキテクチャ上の課題

1. サービス層に UI・CLI・表示整形が混在しており、責務分離が不十分である。`print_next_steps()` と `format_table()` はその典型である。
2. 設定反映処理が 1 クラスに集中し、複数ドメインを横断して状態更新している。`config_reload.py` は LLM、RAG、MCP、Approval、Tool、Memory、Conversation をまとめて更新している。
3. ワークフロー依存クラスが関数内部 import されており、依存の明示性とテスト差し替え性が低い。`WebCrawler`、`ChunkSplitter`、`RagIngester`、`ConfigLoader` が該当する。

### 4.2 実装上の課題

1. `config_reload.py` では `bool(new_cfg.get(...))` のような単純変換が多数あり、文字列入力時に意図しない真偽判定が起こり得る。
2. `config_reload.py` では未指定項目に対して既定値を適用する実装が多く、部分 reload 時でも現行値保持ではなく既定値へ上書きされる可能性がある。
3. `mcp_status.py` では `status` が availability と health の連結文字列で表現されており、機械判定や UI 再利用に不向きである。
4. `ingest_workflow.py` では各段階で `Exception` を包括捕捉し、`str(e)` のみを格納しているため、障害解析に必要な文脈が不足する。
5. `mcp_install.py` では OpenRC 前提の手順や配備パスが固定化されており、環境依存が強い。

### 4.3 後方互換性に起因する課題

1. `config_reload.py` の `sync_services()` は legacy code からの直接呼出し前提が残っている。
2. `mcp_install.py` には旧運用手順を内包した出力が残っており、サービス層に環境依存の互換責務を残している。
3. `mcp_status.py` では固定幅テーブルと連結 status が旧表示互換を引きずっている。
4. `ingest_workflow.py` では UI 文言をそのまま `messages` に積む形式が、旧利用側との互換を優先した構造に見える。

## 5. 改修対象および改修内容

## 5.1 `config_reload.py` 改修内容

### 5.1.1 High

1. `apply_config_dict()` を唯一の公開入口とし、`sync_services()` の legacy 直呼び前提を削除する。必要に応じて private helper 化する。
2. 設定反映をドメイン別に分割する。少なくとも LLM、MCP、Approval、Tool/RAG、Conversation Prompt を個別の reload handler とし、`ConfigReloadService` は orchestration のみ担う構成へ変更する。
3. `bool()`、`int()`、`float()` による ad-hoc 変換を改め、検証付き変換処理を共通化する。特に真偽値変換は明示的 parser を導入する。
4. 未指定項目は既定値で強制上書きせず、「変更要求がある項目のみ反映する」差分適用へ変更する。
5. 旧互換キーや内部名との二重管理を解消し、構成キーの受理体系を一本化する。`github_server_url` と `ctx.cfg.mcp.github_url` のような対応関係は整理対象とする。

### 5.1.2 Medium

1. `ConfigReloadResult` を before/after を持つ差分レポートへ拡張する。現状の `applied` / `needs_restart` / `skipped` のみでは監査と運用説明が不足する。
2. MCP server の hot reload 可否を URL 変更、transport 変更、新規追加などのルールとして定義し、判定ロジックを明文化する。
3. `ctx.cfg.tool.system_prompt_tool` と `ctx.conv.system_prompt_content` の更新責務を一元化し、prompt 同期の整合性を保証する。

### 5.1.3 Low

1. `ConfigReloadResult` 内部は重複排除可能な構造へ変更する。
2. helper 名を役割に合わせて再命名する。`_apply_rag_tool_params()` は実際には LLM retry や watchdog 等も含んでいるため、命名が広すぎる。

### 5.1.4 削除対象

1. `sync_services()` の legacy direct-call 前提。
2. 旧互換キー受理。
3. `_ConfigMixin` からの移行途中で残った暫定的責務分散の前提。

## 5.2 `mcp_install.py` 改修内容

### 5.2.1 High

1. `print_next_steps()` を `McpInstallService` から削除し、CLI Presenter へ移管する。サービスは `ScaffoldResult` の返却に専念する。
2. OpenRC 固定の手順文言、固定パス、固定スクリプト前提をサービス外へ追い出し、環境依存機能をテンプレートまたは deployment adapter に分離する。
3. `server_name`、`role`、`port`、既存ファイル衝突、予約名等の事前検証を追加し、error handling を installer 任せから service 主体へ見直す。

### 5.2.2 Medium

1. `role` を文字列ではなく Enum として定義する。現在の `generic | sqlite | shell | git | ci` は typo 耐性が低い。
2. `CliInstallQA` を interactive 専用とし、事前値注入用の non-interactive 実装を別クラスへ分離する。
3. `tool_snippet` と `agent_toml_snippet` は単純な文字列断片ではなく、構造化 patch 情報またはテンプレートパラメータとして返す方式へ変更する。

### 5.2.3 Low

1. ポート入力エラーは範囲外、非数値、利用不可などに分けて返す。現状は `"Invalid port number."` に集約されている。
2. `asyncio.to_thread(input, ...)` を CLI adapter に閉じ込め、サービスモジュールから対話実装を切り離す。

### 5.2.4 削除対象

1. `print_next_steps()` のような手順文言出力機能。
2. OpenRC 固定を前提とする運用メッセージ。
3. Interactive と flags 指定を同一実装で兼ねる移行的構成。

## 5.3 `mcp_status.py` 改修内容

### 5.3.1 High

1. `probe_all()` と `format_table()` を分離し、probe service と formatter を別クラス化する。
2. `status` の連結文字列表現を廃止し、availability / health / transport-specific detail を個別フィールド化する。現状は `status = f"{status}/{health_label}"` であ
   り、利用側拡張性が低い。
3. HTTP health check は固定の `GET {url}/health` 前提を見直し、server type または設定に応じた probe strategy を導入する。

### 5.3.2 Medium

1. MCP servers の probe は逐次 await から、同時実行数制御付き並列 probe へ変更する。
2. `httpx.AsyncClient(timeout=5.0)` の timeout を設定化する。
3. `_tier_label_for_server()` において未知の tier を黙って `READ_ONLY` 扱いせず、validation error ないし warning とする。

### 5.3.3 Low

1. 固定幅列フォーマットは formatter 側設定に移し、長い endpoint/cmd の短縮・折返しに対応できるようにする。
2. stdio ライフサイクル状態の文字列は Enum 化する。`STOPPED`、`NOT_STARTED`、`RUNNING`、`DEAD` が対象である。

### 5.3.4 削除対象

1. 連結済み status 文字列を利用側に渡す旧互換。
2. REPL 互換の固定幅テーブル生成を service 内に残す実装。

## 5.4 `ingest_workflow.py` 改修内容

### 5.4.1 High

1. `crawl` / `split` / `ingest` の各段階で包括的に `Exception` を捕捉して `str(e)` のみを返す実装を見直し、原因分類済み例外とログ出力へ変更する。
2. `WebCrawler`、`ChunkSplitter`、`RagIngester`、`ConfigLoader` の lazy import を縮退させ、DI または factory 注入へ変更する。
3. ワークフロー段階ごとの入出力と staging 副作用を明示し、失敗時の cleanup 方針を整理する。現状は段階進行が暗黙の状態依存である。

### 5.4.2 Medium

1. `IngestResult.stage` は Enum または `Literal` へ変更し、コメント依存の文字列運用をやめる。現状は `"ok" | "crawl" | "split" | "ingest"` がコメントでのみ定義されている。
2. `messages` は UI 向け文字列配列ではなく、イベント名・レベル・メタデータを持つ構造へ変更する。
3. `snippets_only` のための `rag_pipeline.toml` 読込後上書き処理は専用設定オブジェクトへ移動する。現状は `md_index_enable = True` を直接差し込んでいる。

### 5.4.3 Low

1. 未使用の `logger` は削除または本来のログ出力へ利用する。
2. `run_in_executor(None, ...)` の executor 方針を明確化し、CPU/I/O 特性に応じて制御する。

### 5.4.4 削除対象

1. 旧利用側との互換のために残っている UI 文言中心の `messages` 形式。
2. 起動軽量化や移行都合のために残っている lazy import 前提が不要であれば削除する。

## 6. 実施優先順位

### 6.1 Phase 1: 最優先

1. `config_reload.py` の単一公開入口化、legacy 呼出し前提削除、型変換見直し、差分適用化。
2. `mcp_install.py` の表示責務分離、OpenRC 固定前提削除。
3. `mcp_status.py` の probe / formatter 分離と status 構造化。
4. `ingest_workflow.py` の例外設計見直しと依存性注入化。

### 6.2 Phase 2: 中優先

1. `config_reload.py` のドメイン別 reload handler 化と差分レポート強化。
2. `mcp_status.py` の並列 probe 化、timeout 設定化、tier validation 強化。
3. `ingest_workflow.py` のイベント構造化、stage Enum 化、staging 管理整理。
4. `mcp_install.py` の role Enum 化、QA 実装分離、結果構造化。

### 6.3 Phase 3: 低優先

1. 命名見直し、重複排除、formatter 改善、ログ整備。
2. 小規模 cleanup と利用側移行完了確認。

## 7. 期待効果

1. サービス層の責務が整理され、テストコードの単純化とモック差し替え容易性が向上する。これは `mcp_install.py`、`mcp_status.py`、`ingest_workflow.py` に顕著である。
2. `config_reload.py` の設定反映が明示的・検証可能となり、reload 時の不具合混入が減る。
3. 状態表現が構造化され、CLI、REPL、Web UI、API 応答で再利用しやすくなる。`mcp_status.py` と `ingest_workflow.py` において特に有効である。
4. 後方互換維持のためだけに残っていた複雑さを削除でき、将来改修時の判断コストが下がる。

## 8. リスクおよび留意事項

1. 後方互換機能削除に伴い、既存呼出し元、既存設定ファイル、旧表示処理を同時に改修する必要がある。特に `sync_services()` 直接利用箇所や旧 config key 利用箇所の洗い出しが前提となる。
2. `mcp_install.py` の OpenRC 前提除去に伴い、現行の運用手順文書または deploy スクリプト側に代替表現を整備する必要がある。
3. `ingest_workflow.py` の依存性注入化は、既存初期化コードに変更を要求するため、組立て箇所の整合確認が必要である。
4. `mcp_status.py` の status 構造化は、現行文字列を前提とした表示側やテストに影響する。

## 9. 実施条件

1. 対象 4 ファイルの呼出し元を横断確認し、legacy 依存箇所を先行棚卸しすること。特に `config_reload.py` は単独改修ではなく周辺反映が必要である。
2. Presentation 層、CLI Adapter、Formatter、Reload Handler などの新責務配置先を事前に決めること。`mcp_install.py` と `mcp_status.py` では配置先設計が重要である。
3. ingest pipeline では副作用を持つ staging 領域管理が絡むため、ワークフロー境界と失敗時挙動を事前定義すること。

## 10. 結論

対象 4 ファイルは、Mixin からの切り出しにより一定の分離は進んでいる一方で、表示責務、互換機能、辞書直反映、文字列ベース状態表現、依存関係の暗黙化が残存している。今回の改修では、これらを段階的に整理するのではなく、後方互換維持のために残されている機能は削除する という前提で、入口・役割・状態表現・設定反映方式を再定義することが望ましい。最優先は `config_reload.py` の単一入口化と差分適用化であり、次点として `mcp_install.py` と `mcp_status.py` の表示責務分離、`ingest_workflow.py` の例外設計と依存性注入化を進める。
