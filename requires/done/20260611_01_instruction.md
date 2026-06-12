# Python プログラム改修計画書 High / Medium 対象版

## 全体方針

### 事実
- 対象は `tool_policy.py`、`tool_result_formatter.py`、`tool_runner.py`、`tool_scheduler.py`、`stdio_lifecycle.py`、`tool_approval.py`、`tool_audit.py`、`tool_loop_guard.py` の 8 ファイルである
- 業務ロジック上の fail-fast を阻害する実装が存在する
  - `tool_runner.py:46` の `assert`
  - `tool_runner.py:50-54` の不正 JSON を `{}` にフォールバックする処理
  - `tool_runner.py:108-120` の `except Exception`
  - `tool_approval.py:60-67` の `except Exception: pass`
  - `tool_approval.py:137-140` の不正 JSON を `{}` にフォールバックする処理
  - `tool_loop_guard.py:122-125` の不正 JSON を `{}` にフォールバックする処理
  - `stdio_lifecycle.py:97-111` と `stdio_lifecycle.py:115-124` の `except Exception`
- `dict` と `Any` を境界以外でも多用している
  - `tool_runner.py`
  - `tool_approval.py`
  - `tool_policy.py`
  - `tool_scheduler.py`
  - `tool_result_formatter.py`
  - `tool_audit.py`
- `str(args.get(...))` による無条件文字列化が存在する
  - `tool_policy.py:66,85,106,144,166,167`
  - `tool_result_formatter.py:49-72`
- `print` による直接出力が存在する
  - `tool_runner.py:99,104,106`
  - `tool_approval.py:96,103,113,114,120,143,144,149`
- 監査ログ、承認判定、実行結果の内部表現が `dict` と生文字列中心である

### 推測
- 現状は後方互換的な吸収処理と暗黙補正が残っており、入力異常時に処理継続する設計になっている可能性が高い
- strict typing と schema validation を先に導入しないと、ファイル単位修正の影響範囲が読みにくい可能性が高い

### 改修方針
- 後方互換性は維持しない。旧入力の吸収、暗黙補正、デフォルト補完、継続前提のフォールバックを削除する
- High と Medium のみを対象とする。Low は今回の計画対象外とする
- すべての境界で厳密な変換・型付けを行う
- 例外は fail-fast 前提で上位へ伝播する
- `assert`、`except Exception`、`dict[str, Any]`、`str(args.get(...))`、直接 `print` を段階的に除去する
- 監査ログ、承認判定、実行結果は専用 DTO を定義して扱う
- LLM 由来 JSON は decode 後に schema 検証し、不一致は即時失敗とする
- 不明な tool 名、不明な tier、不明な metadata は fail-open ではなく fail-fast とする

## 実装ルール

### 必須ルール
- `assert` を業務ロジックで使用しない。前提条件違反は明示例外を送出する
- `except Exception` を使用しない。捕捉対象を具体例外に限定する
- `dict[str, Any]` を外部境界以外で使用しない。境界通過直後に型変換する
- `str(args.get(...))` のような無条件文字列化を禁止する。入力型を検証し、期待型以外は例外とする
- 変換・型付けは厳密に行う
- `None` と空文字と未設定を同一視しない
- 監査ログ、承認判定、実行結果はそれぞれ専用 DTO を定義する
- LLM 由来 JSON は decode 後に schema 検証する。schema 不一致は即時失敗とする
- 出力は直接 `print` せず、UI/CLI 出力用インターフェースへ集約する
- 不明な tool 名、不明な tier、不明な metadata は fail-open ではなく fail-fast とする

### 実装上の統一事項
- `agent/tool_models.py` を新設し、少なくとも `ToolCallRequest`、`ToolCallFunction`、`ToolExecutionResult`、`ToolMeta`、`ApprovalOutcome`、`AuditEvent` を定義する
- `agent/tool_enums.py` を新設し、少なくとも `RiskLevel`、`OperationType`、`ApprovalDecisionType`、`GuardDecisionType` を定義する
- `agent/tool_exceptions.py` を新設し、少なくとも `ToolArgumentsDecodeError`、`ToolExecutorUnavailableError`、`PolicyViolationError`、`ApprovalPreviewError`、`AuditUnavailableError`、`LifecycleConfigurationError` を定義する
- `agent/tool_output.py` を新設し、CLI/UI 出力を集約する
- 内部戻り値は `bool` や `str | None` ではなく、型付き DTO または具体例外を使う

## ファイルごとの修正内容

### `tool_runner.py`

#### 事実
- `execute_one_tool_call()` で `assert ctx.services.tools is not None` を使用している (`tool_runner.py:46`)
- tool arguments の JSON decode 失敗時に `{}` を採用して継続している (`tool_runner.py:50-54`)
- `_collect_tool_result_msgs()` で `ToolResultStore.store()` の失敗を `except Exception` で握りつぶしている (`tool_runner.py:108-120`)
- `print` による直接出力がある (`tool_runner.py:99,104,106`)
- 戻り値・中間値に `dict` と `list[Any]` を使用している (`tool_runner.py:37-41`, `tool_runner.py:141`, `tool_runner.py:173`)

#### 修正内容
- High
  - `assert` を削除し、`ctx.services.tools is None` は `ToolExecutorUnavailableError` を送出する
  - tool call JSON decode 後に `ToolCallRequest` へ strict 変換する。decode 失敗・schema 不一致は即時失敗とする
  - `_collect_tool_result_msgs()` の `except Exception` を削除し、永続化失敗は具体例外で停止する
  - `execute_one_tool_call()` と実行経路の戻り値を `ToolExecutionResult` DTO に統一する
- Medium
  - `print` を廃止し、`agent/tool_output.py` へ委譲する
  - denied 結果を文字列直書きではなく型付き出力モデルに統一する

### `tool_approval.py`

#### 事実
- `ApprovalDecision` は `TypedDict(total=False)` で必須項目保証がない (`tool_approval.py:38-45`)
- dry-run 失敗を `except Exception: pass` で握りつぶしている (`tool_approval.py:60-67`)
- arguments decode 失敗時に `{}` を採用して継続している (`tool_approval.py:137-140`)
- `print` による直接出力がある (`tool_approval.py:96,103,113,114,120,143,144,149`)
- plan mode block は audit に統一されていない (`tool_approval.py:142-147`)

#### 修正内容
- High
  - `ApprovalDecision` を `dataclass(frozen=True)` または同等 DTO に置換する
  - `risk_level` と `decision` を `Enum` 化する
  - dry-run 実行失敗を黙殺せず `ApprovalPreviewError` として即時失敗させる
  - JSON decode fallback を削除し、`ToolCallRequest` 変換失敗で停止する
  - `check_approval()` の `bool` 戻り値を廃止し、`ApprovalOutcome` DTO を返す
- Medium
  - 直接 `print` と `input()` を使わず承認 UI インターフェースへ分離する
  - plan mode block も監査イベントとして統一記録する

### `tool_policy.py`

#### 事実
- `classify_operation_type()` と `classify_risk()` は生文字列を返している (`tool_policy.py:43-53`, `tool_policy.py:113-130`)
- `_TIER_TO_RISK` は `dict[str, str]` で、未知 tier の扱いが明示されていない (`tool_policy.py:35-40`, `tool_policy.py:120-121`)
- `check_allowed_root()` と `check_allowed_repo()` は `bool` 返却で、理由は別関数へ分散している (`tool_policy.py:133-168`, `tool_policy.py:171-195`)
- `str(args.get(...))` による型曖昧化が複数箇所にある (`tool_policy.py:66,85,106,144,166,167`)

#### 修正内容
- High
  - `RiskLevel` と `OperationType` を `Enum` 化する
  - 事前チェック API を `bool` 返却ではなく、成功か例外送出のどちらかに統一する
  - `preflight_deny_reason()` を廃止し、呼び出し側は具体例外で分岐する
  - 未知 tier は `UnknownToolSafetyTierError` などの明示例外で停止する
  - `ToolCallRequest` から型付き accessor を通して path/repo/branch を取得する
- Medium
  - `tool_name` 未使用引数を削除し、署名を整理する
  - path/branch 取り出しと設定参照を validator として共通化する

### `tool_scheduler.py`

#### 事実
- `build_execution_groups()` の入力が `list[dict]` と `dict[str, dict]` である (`tool_scheduler.py:14-18`)
- `tool_meta.get(name, {})` により未登録 metadata を空 dict で継続している (`tool_scheduler.py:34`)
- `resource_scope`、`requires_serial`、`is_write` を非検証で読んでいる (`tool_scheduler.py:35-41`)

#### 修正内容
- High
  - `build_execution_groups()` のシグネチャを `list[ToolCallRequest]` と `dict[str, ToolMeta]` に変更する
  - 未登録 tool metadata は即時失敗とする
  - 空の tool 名や不正 metadata を入力境界で reject する
- Medium
  - resource group の順序規則を明文化し、入力順保持または明示ソートのどちらかに固定する

### `stdio_lifecycle.py`

#### 事実
- `ensure_ready()` は不適合条件を no-op で返す (`stdio_lifecycle.py:61-64`)
- `_start()` は `cfg.cmd` 未設定でも warning と状態更新のみで継続する (`stdio_lifecycle.py:80-90`)
- `_start()` と `_stop_stdio()` で `except Exception` を使用している (`stdio_lifecycle.py:97-111`, `stdio_lifecycle.py:115-124`)
- transport state は `TransportHandle` と複数 dict に分散している (`stdio_lifecycle.py:24-57`)

#### 修正内容
- High
  - `ensure_ready()` の no-op を廃止し、設定不整合は `LifecycleConfigurationError` を送出する
  - `cfg.cmd` 未設定は例外送出とし、黙って FAILED 状態にしない
  - `except Exception` を廃止し、transport 固有例外や `OSError` 等へ分解する
  - start/stop/restart の失敗契機を DTO または具体例外へ統一する
- Medium
  - state 管理を 1 つの集約オブジェクトへ整理する
  - `set_transport_state()` の未存在 key 暗黙作成を廃止する

### `tool_result_formatter.py`

#### 事実
- `mask_args()` は top-level key のみをマスクする (`tool_result_formatter.py:24-29`)
- `build_github_preview()` と `build_preview()` で `str(args.get(...))` を使用している (`tool_result_formatter.py:49-72`)
- preview 生成は tool 名ごとの if 分岐と生 dict 前提である (`tool_result_formatter.py:59-72`)

#### 修正内容
- High
  - preview 生成の入力を `ToolCallRequest` に統一し、型未確定の `dict` を直接受けない
  - `str(args.get(...))` を廃止し、期待型不一致は例外とする
- Medium
  - 再帰マスキングを導入し、入れ子の秘匿値も遮断する
  - tool ごとの preview 生成を dispatcher 化し、分岐責務を整理する

### `tool_audit.py`

#### 事実
- `ctx.services.audit_logger is None` の場合は黙って return する (`tool_audit.py:35-40`, `tool_audit.py:60-61`, `tool_audit.py:85-86`)
- `log_approval_decision()` は `ApprovalDecision` を `dict.get()` ベースで参照している (`tool_audit.py:67-70`)
- audit payload をその場で dict 構築している (`tool_audit.py:41-55`, `tool_audit.py:62-74`, `tool_audit.py:89-103`)

#### 修正内容
- High
  - audit 必須前提とする場合、logger 未設定を `AuditUnavailableError` として停止する
  - `ApprovalOutcome`、`ToolExecutionResult`、監査イベント DTO を分離して定義する
  - `dict.get()` ベース参照を廃止し、型付き DTO から監査データを組み立てる
- Medium
  - event schema を固定し、event 名と field 名を定数化する
  - `resource_scope` 抽出を共通 accessor へ寄せる

### `tool_loop_guard.py`

#### 事実
- cycle/dedup 判定は raw `message["tool_calls"]` と raw arguments 文字列を直接 fingerprint 化している (`tool_loop_guard.py:70-79`, `tool_loop_guard.py:97-104`)
- retry 判定で invalid JSON を `{}` にフォールバックしている (`tool_loop_guard.py:122-125`)
- 戻り値が `str | None` であり、判定結果が構造化されていない (`tool_loop_guard.py:61-65`, `tool_loop_guard.py:94-95`, `tool_loop_guard.py:115-116`, `tool_loop_guard.py:139-145`, `tool_loop_guard.py:158-170`)
- retry block 時に dedup 用 hint を再利用している (`tool_loop_guard.py:127-130`)

#### 修正内容
- High
  - raw dict ではなく `ToolCallRequest` に正規化した後に fingerprint を生成する
  - invalid JSON fallback を削除し、decode 失敗は即時失敗とする
  - guard 判定結果を `GuardDecision` DTO に変更する
- Medium
  - retry 用 hint を dedup 用と分離する
  - fingerprint 戦略をユーティリティ化し、guard 本体から分離する

## 作業ステップ

1. 型と例外の土台を新設する
   - `agent/tool_models.py`
   - `agent/tool_enums.py`
   - `agent/tool_exceptions.py`
   - `agent/tool_output.py`
2. LLM 由来 tool call の入力境界を strict 化する
   - `tool_runner.py`
   - `tool_approval.py`
   - `tool_loop_guard.py`
3. policy 層を fail-fast に変更する
   - `tool_policy.py` の `bool` / `str | None` ベース判定を廃止する
   - 未知 tier、未知 tool、未知 metadata の即時失敗を追加する
4. approval と runner を DTO ベースへ変更する
   - `ApprovalOutcome`
   - `ToolExecutionResult`
   - 直接 `print` の除去
5. scheduler を型付き metadata 前提へ変更する
   - `tool_scheduler.py`
   - metadata 欠落時失敗の実装
6. lifecycle を no-op 禁止で再設計する
   - `stdio_lifecycle.py`
   - 具体例外への分解
7. formatter と audit を型付き DTO 前提へ変更する
   - `tool_result_formatter.py`
   - `tool_audit.py`
8. loop guard を構造化する
   - `GuardDecision` 導入
   - retry hint 分離
9. テスト更新
   - 不正 JSON
   - 未知 tool
   - 未知 tier
   - audit logger 未設定
   - lifecycle 設定不備
   - dry-run 失敗
10. 静的検査
   - `mypy --strict`
   - `ruff check`
   - `pytest`

## 完了条件

### 必須
- 対象 8 ファイルから `except Exception` が除去されている
- 業務ロジック上の `assert` が除去されている
- 外部境界以外から `dict[str, Any]` が除去されている
- `str(args.get(...))` のような無条件文字列化が除去されている
- LLM 由来 JSON が decode 後に schema 検証され、異常時に即時失敗する
- 不明な tool 名、不明な tier、不明な metadata が即時失敗する
- 監査ログ、承認判定、実行結果が DTO で表現される
- 直接 `print` による出力が対象ファイルから除去されている
- High / Medium 対象項目の修正が完了している

### 検証
- `mypy --strict` が通過している
- `ruff check` が通過している
- `pytest` が通過している
- 不正 JSON や設定不整合の異常系テストが追加されている

### 不明
- `ctx.services.tools.execute()` が送出する具体例外型は不明
- `ctx.tool_result_store.store()` の具体例外型は不明
- `StdioTransport.start()` / `stop()` の具体例外型は不明
- audit 未設定時を致命扱いにする運用要件は不明
