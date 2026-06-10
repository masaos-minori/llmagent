# Agent Runtime 改修計画書

## 全体方針

- 本改修では -後方互換性を維持しない-。旧挙動の温存、曖昧な入力受け入れ、暗黙補正、warning のみで継続する救済分岐は削除する。
- すべてのレイヤで -fail-fast- を徹底する。設定不備、接続失敗、永続化失敗、起動失敗、ツール実行失敗、履歴圧縮失敗、ライフサイクル不整合は即座に検知し、呼び出し元へ明示的に返す。
- 変換・型付けは厳密に行う。`Any`、曖昧な `dict`、`list[str] / str | None / tuple[...]` などの loosely typed 契約は削減し、境界ごとに専用モデルまたは Protocol を導入する。
- `except Exception` は原則使用しない。想定される失敗型を個別に捕捉し、それ以外はそのまま送出する。
- REPL / Context / Factory / Lifecycle / Repositories / Orchestrator / TurnRunner / View の責務を再分離し、各モジュールが単一責務になるよう再設計する。
- command 層・REPL 層・永続化層・オーケストレーション層・ライフサイクル層の境界を明確にし、相互参照と状態の暗黙共有を減らす。

## 実装ルール

- 失敗を `None`、空配列、`False`、`"?"` などへ変換して継続しない。正常系と異常系は型と例外で区別する。
- すべての I/O（設定ロード、SQLite、プロセス起動、ネットワーク、stdio、HTTP、履歴保存）は明示的な失敗契約を持つ。
- `SQLiteHelper(...)` の直接生成を各所に散らさず、Repository / Factory / Provider 経由に統一する。
- dataclass / config model / context model / lifecycle model は mutable と immutable を意図的に分ける。
- `print()` を業務ロジックに混ぜない。CLI 表示は view 層へ集約し、ドメイン処理やライフサイクル制御から分離する。
- `Logger` / warning ベースのエラー吸収を廃止し、ログは補助情報とする。制御フローは例外または結果型で表現する。
- 設定構築は「ロード → 正規化 → field validation → cross-field validation」を一方向で実施し、途中で fail-soft にしない。
- 非同期処理では cancellation / timeout / restart / shutdown の責務を明示し、再起動回数や idle timeout も構造化した state で管理する。

## ファイルごとの修正内容

### 1. `repl.py`

#### High
- `AgentREPL` が担っている責務（初期化、health check、startup banner、MCP 起動、REPL ループ、session 初期化、resource close）を分解し、thin coordinator 化する。
- `_get_chunk_count()` の `except Exception` による `"?"` 返却を廃止し、DB 接続失敗を明示的に扱う。
- `_start_mcp_servers()` / `_start_subprocess_servers()` の broad exception を廃止し、HTTP/stdio 起動失敗を structured error として扱う。
- `print()` による startup warning を view 経由へ統一する。

#### Medium
- `SLASH_COMMANDS` の静的定義を registry 主導へ寄せる。
- `AgentContext` の初期化・依存差し込み・Orchestrator/CommandRegistry 構築を factory へさらに寄せる。
- `run()` の startup / shutdown シーケンスを phase ごとの手続きに分解する。

#### Low
- startup banner 表示ロジックを view helper に移す。

---

### 2. `repl_health.py`

#### High
- `probe_mcp_health()`、`check_service_health()`、`_fetch_stdio_tools()`、`_collect_server_tool_names()`、watchdog 系にある `except Exception` を除去し、HTTP error / RPC error / parse error / lifecycle error を個別に扱う。
- health check failure を単なる warning 文字列リストではなく、構造化された診断結果モデルへ変更する。
- restart 判定と restart 実行を分離し、watchdog が直接ライフサイクルを触りすぎる構造を整理する。

#### Medium
- HTTP/stdio の健康診断処理を strategy 化する。
- tool definition runtime check を「期待集合」と「実際集合」の比較サービスへ切り出す。
- restart count / cool-down / 永続障害の取扱いを state 化する。

#### Low
- logger の文言と warning 生成規約を統一する。

---

### 3. `session.py`

#### High
- `AgentSession` が note/document/message/session 管理をまとめて持っているため、責務を分割する。message / note / document / session title / undo を別 service/repository に切り出す。
- `except Exception` により `None` / `[]` / `False` へ変換しているメソッドを fail-fast に変更する。
- `SQLiteHelper` の直接利用を repository 層へ押し下げ、session façade はユースケース呼び出しだけにする。

#### Medium
- `start()` / `undo_last_turn()` / `delete_last_turn()` のトランザクション境界を明示する。
- `list_sessions()` や `set_title()` などを session repository と service に分ける。
- session 状態と current session id の同期を context 側と明示的に整合させる。

#### Low
- ログメッセージと戻り値規約を統一する。

---

### 4. `session_message_repo.py`

#### High
- `save()` / `save_many()` / `fetch_messages()` の broad exception を廃止する。
- 永続化失敗時に warning だけで継続しない。session 層へ例外または明示的失敗結果を返す。
- `SQLiteHelper` 依存を注入可能にし、接続生成を repository 内に固定しない。

#### Medium
- 単件保存と複数保存の重複ロジックを整理する。
- message model を typed object 化し、dict ベース入出力を減らす。

#### Low
- logger 出力の粒度を統一する。

---

### 5. `stdio_lifecycle.py`

#### High
- `TransportState` / `TransportHandle` / `StdioServerLifecycleManager` の状態遷移を厳密化し、idle shutdown・restart・ensure_ready の分岐を fail-fast にする。
- `_start()` / `_stop_stdio()` の broad exception を廃止し、起動失敗・停止失敗・状態不整合を個別に扱う。
- stdio transport state を dict 的に持つのではなく、遷移可能な状態機械として明示する。

#### Medium
- idle timeout 判定と shutdown 実行を分離する。
- on-demand 起動と常駐起動の責務を分離する。
- stdio lifecycle を protocol ベースで HTTP lifecycle と共通抽象に寄せる。

#### Low
- dataclass の責務を簡潔化する。

---

### 6. `cli_view.py`

#### High
- `print()` による直接出力を抽象化し、Writer/Reader/CLIView の責務を明確にする。
- 進捗表示、トークン表示、履歴保存、警告表示を view contract に乗せ、REPL や Orchestrator が直接文言を持たないようにする。
- 非同期入力と readline セットアップの境界を明確化し、端末依存失敗を吸収しない。

#### Medium
- `Writer` / `Reader` / `CLIView` を Protocol 主導にし、テスト用実装を差し替えやすくする。
- view 層での文字列整形をヘルパに分離する。

#### Low
- 表示文言の統一と docstring の整理。

---

### 7. `config.py`

#### High
- `load_config()` の broad exception ラップを見直し、設定ロード失敗原因（ファイル不存在・型不正・値不正）を分類する。
- `Any` を使った builder (`load_config`, `_build_*`, `build_agent_config`) を厳密型へ変更する。
- `AgentConfig.__post_init__` と `_validate_cross_field()` による cross-field validation を整理し、field validation と cross-field validation を一方向パイプラインへ統一する。
- mutable runtime config と immutable startup config を分ける。

#### Medium
- `LLMConfig`, `RAGConfig`, `ToolConfig`, `MemoryConfig`, `ApprovalConfig`, `ObservabilityConfig` の依存関係を明示する。
- builder 群の重複（`cfg.get(..., default)`）を共通変換ヘルパ化する。
- URL / timeout / token limit / retry count などの primitive 群を強い型に近づける。

#### Low
- docstring と設定キー説明の同期。

---

### 8. `context.py`

#### High
- `AgentContext` に集約されている mutable state を再整理し、永続状態・会話状態・turn 状態・サービス参照を分離する。
- `ConversationState`, `TurnState`, `RuntimeStats`, `AppServices` の mutable 性を見直し、不変にできる部分は不変化する。

#### Medium
- context を単なる shared bag にせず、更新単位ごとに責務を分ける。
- `AppServices` の具象依存を interface に寄せる。

#### Low
- dataclass defaults の見直しと docstring の整理。

---

### 9. `document_repo.py`

#### High
- `list_documents()` / `delete_document()` の broad exception を廃止し、DB 失敗を `[]` / `False` へ変換しない。
- document repository で session DB に直接依存している構造を明示的 provider 経由へ変更する。
- list / delete の結果を typed model へ寄せる。

#### Medium
- query と command を分割する。
- フィルタ引数や戻り型を厳密化する。

#### Low
- ログ文言統一。

---

### 10. `error_injection_service.py`

#### High
- エラー注入ルールを明示的な policy として定義し、テスト専用の責務に限定する。
- 本番コードと混在しないよう、注入条件と適用対象を厳密に制御する。

#### Medium
- 注入シナリオを enum / rule object 化する。
- lifecycle / orchestrator との接点を限定する。

#### Low
- テストユーティリティとしての docstring 整理。

---

### 11. `factory.py`

#### High
- `build_agent_context()` が多くの具象依存を wiring しているため、生成責務を分解する。
- `_build_llm_client()` / `_build_tool_executor()` / `_build_history_manager()` / `_build_memory_services()` の builder を fail-fast にし、部分構築成功のまま継続しない。
- `_ServerLifecycleRouter` を protocol/adapter ベースに置き換え、HTTP/stdio lifecycle の差異を吸収する。
- plugin registry 初期化や tracer 初期化も副作用を明示し、失敗時は起動停止する。

#### Medium
- factory 内部での config → service 変換を部品化する。
- provider/container と actual construction を分け、テスト用差し替えを容易にする。

#### Low
- helper 関数名の整理。

---

### 12. `history.py`

#### High
- `HistoryManager` の圧縮失敗を `None` と warning で吸収しない。
- 履歴圧縮、保護ターン、文字数計測、圧縮対象選定を分離する。
- LLM 圧縮失敗時の fallback を除去し、失敗を明示的に REPL/Orchestrator へ返す。

#### Medium
- `CompressResult` をより厳密な結果型にする。
- tokenizer / char-based budget を policy 化する。
- 圧縮対象選定を `history_selection_policy.py` とより明確に分離する。

#### Low
- logger 文言と helper 命名の整理。

---

### 13. `history_selection_policy.py`

#### High
- 選定ポリシーを純粋関数/純粋オブジェクトに保ち、副作用を持たせない。
- policy と compression 実行を分離し、選定結果を typed model で返す。

#### Medium
- protect turns, system prompt 保護, pinned history などの規則を設定可能にする。
- policy のテストしやすさを高める。

#### Low
- 規則の docstring を補強する。

---

### 14. `http_lifecycle.py`

#### High
- `HttpServerLifecycleManager` の起動・停止・restart・health poll を fail-fast 化し、broad exception を廃止する。
- subprocess 起動失敗・health-check timeout・停止失敗・pid/state 不整合を明示的な失敗型で管理する。
- `StartupFailure` / `HttpStartupError` の責務を整理し、例外体系を一本化する。

#### Medium
- health-check polling と起動シーケンスを分離する。
- lifecycle state を別 state model に切り出す。
- HTTP lifecycle を stdio lifecycle と共通 protocol に合わせる。

#### Low
- logger メッセージの統一。

---

### 15. `lifecycle.py`

#### High
- `LifecycleState` を実際の lifecycle manager 実装と同期し、到達可能状態・遷移規則を明文化する。

#### Medium
- state enum だけでなく event / transition を導入する。

#### Low
- enum 命名と文書化の整理。

---

### 16. `lifecycle_protocol.py`

#### High
- protocol を実装実態に合わせて見直し、 restart / ensure_ready / shutdown / state access の契約を厳密化する。
- HTTP/stdio の違いを吸収できる最小 interface にする。

#### Medium
- sync/async の混在を避け、 protocol の戻り型を統一する。

#### Low
- docstring 更新。

---

### 17. `llm_turn_runner.py`

#### High
- turn 実行の責務（LLM 呼び出し、tool call handling、streaming、retry、error mapping）を明確化し、Orchestrator との重複を排除する。
- error mapping を fail-fast にし、空文字や簡易 result に丸めない。
- request/response の typed model を導入する。

#### Medium
- streaming 処理と complete response 処理を分離する。
- retry ルールを config/policy 化する。

#### Low
- ログとメソッド名の整理。

---

### 18. `note_repo.py`

#### High
- `add_note()` / `list_notes()` / `delete_note()` / `get_all_note_contents()` の broad exception を廃止し、`None` / `[]` / `False` fallback を削除する。
- note repository の戻り値を typed model に変更する。
- DB provider 注入方式へ変更する。

#### Medium
- query と command を分割する。
- 共通 SQL 実行ヘルパに依存しすぎない責務分離を行う。

#### Low
- ログ文言整理。

---

### 19. `orchestrator.py`

#### High
- `Orchestrator` の責務を再整理し、turn 制御・error mapping・view interaction・service coordination を分離する。
- `except Exception` により `TurnResult(success=False, ...)` へ丸める挙動を見直し、未知例外を安易に domain result へ変換しない。
- `TurnResult` を厳密な結果型にし、`answer` / `error_kind` / `success` の loosely coupled な構造を改善する。
- turn lifecycle（開始、LLM 実行、tool 実行、後処理、失敗処理）を phase ごとに明示化する。

#### Medium
- Orchestrator と `LLMTurnRunner` の境界を整理する。
- cancellation / timeout / interrupt / undo 対応を結果型に反映する。
- CLI 表示や warning 作成を view へ寄せる。

#### Low
- docstring と命名の更新。

## 作業ステップ

1. -型と失敗契約の固定-
   - `config.py`, `context.py`, `lifecycle.py`, `lifecycle_protocol.py`, `orchestrator.py` の境界型・状態型・結果型を定義し直す。
   - `None` / `False` / 空配列 / `"?"` によるエラー吸収箇所を洗い出し、明示的失敗型へ置換する。

2. -Repository 層の fail-fast 化-
   - `session_message_repo.py`, `document_repo.py`, `note_repo.py` を改修し、broad exception と fallback 戻り値を除去する。
   - `session.py` は façade 化し、repository 呼び出しだけに寄せる。

3. -Lifecycle 層の再設計-
   - `http_lifecycle.py`, `stdio_lifecycle.py`, `lifecycle.py`, `lifecycle_protocol.py` の state/transition を整理する。
   - restart / stop / ensure_ready / health poll の順序と失敗契約を統一する。

4. -History / Turn 実行の整理-
   - `history.py`, `history_selection_policy.py`, `llm_turn_runner.py`, `orchestrator.py` を再分割し、圧縮・選定・turn 実行・error mapping を分離する。

5. -Factory / REPL の thin coordinator 化-
   - `factory.py` の wiring を分割し、`repl.py` から初期化詳細を排除する。
   - `repl_health.py` を health service 化し、REPL は結果表示のみ行う。

6. -View と Context の整理-
   - `cli_view.py` を表示専用にし、`context.py` を shared mutable bag から責務別 state container に再構成する。

7. -異常系テスト追加-
   - Config load error
   - SQLite failure
   - HTTP subprocess start failure
   - stdio transport restart failure
   - health-check timeout
   - history compression failure
   - turn runner failure
   - note/document/session repository failure

## 完了条件

- `except Exception` が原則として除去され、例外は分類済みになっている。
- REPL / Factory / Lifecycle / Repository / TurnRunner / Orchestrator / View の責務境界が明確になっている。
- すべての I/O 失敗が `None` / `[]` / `False` / `"?"` に丸められず、明示的失敗として扱われている。
- `AgentContext` の状態構造が整理され、shared mutable state の範囲が縮小している。
- `config.py` の field validation と cross-field validation が一方向パイプラインとして整理されている。
- lifecycle state と protocol が HTTP/stdio 実装の実態に一致している。
- repository 層が fail-fast 化され、永続化失敗を warning のみで継続しない。
- history 圧縮と turn 実行の責務が分離され、Orchestrator が thin coordinator に近づいている。
- REPL は startup/shutdown/input loop の最小責務だけを持ち、詳細処理は service/factory/lifecycle へ移譲されている。
