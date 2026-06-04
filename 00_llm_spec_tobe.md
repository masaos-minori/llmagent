# Refactoring Instructions for Claude Code

## Overall Policy

* Remove all remaining legacy features, classes, and settings that are kept only for backward compatibility.
* Do not preserve backward-compatibility leftovers unless there is a clear, explicit requirement to keep them.
* Simplify the codebase by eliminating transitional compatibility layers.

以下の修正を実施

# `session.py`

## 改善点

* `save_many()` は 1 トランザクションでまとめている点は良いが、各行ごとに `db.execute()` を繰り返しており、**大量保存時の効率が限定的**である。
* セッション・文書・ノート・削除処理まで 1 クラスに集約されており、**Repository の責務境界が広い**。会話履歴、RAG 文書、ノートは論理的に分離可能である。
* `fetch_messages()` は JSON 破損時に warning を出して処理継続するが、**データ不整合の検知と復旧方針**は明確でない。

## 修正方針

* `save_many()` を `executemany()` 相当へ寄せる。
* `SessionMessageRepository` / `DocumentRepository` / `NoteRepository` へ分割する。
* 破損レコード検知時の監査イベント化を追加する。


# `http_lifecycle.py`

## 改善点

* 起動失敗時は `StartupFailure` を作成しているが、**timeout パスでは stderr の回収を行わずに `proc.terminate()` だけで終了**しており、原因調査情報が欠落する。
* timeout 後に `terminate()` はするが、**wait / kill の後始末が不足**している。ゾンビ化または停止遅延に対する耐性が弱い。
* `verify_running()` は warning のみで回復しないため、**起動モード subprocess の自己修復挙動が限定的**である。

## 修正方針

* timeout 時も stderr を回収し、`StartupFailure` 相当の情報を例外へ含める。
* `terminate -> wait(timeout) -> kill` の標準手順へ統一する。
* `verify_running()` を「warning のみ」ではなく、必要なら restart へ接続できる設計へ寄せる。

# `stdio_lifecycle.py`

## 改善点

* `_ensure_ondemand()` は double-checked locking を実装しており良いが、**watchdog 側にも restart ロジックが存在する**ため、起動・再起動責務が一本化されていない。
* `shutdown_idle()` 後の transport マップ更新方針が見えにくく、**停止済み transport の再利用ポリシー**を明文化した方がよい。

## 修正方針

* stdio 再起動を必ず lifecycle manager 経由に統一し、watchdog は lifecycle の public API のみ呼ぶ。
* transport state を `running / stopped / failed` などの明示状態へ寄せる。

# `lifecycle.py`

## 改善点

* facade としては機能しているが、`_http_procs` / `_start_locks` を **private property の後方互換**として露出しており、内部構造の隠蔽が崩れている。
* facade であるにもかかわらず、`last_called` などの state を持ち、実装詳細との結合が残る。**完全な薄い facade になっていない**。

## 修正方針

* backward-compat property の利用箇所を先に除去し、その後 API から削除する。
* facade は public API のみ維持し、観測系が必要なら専用 status API を足す。

# `repl_health.py`

**重要度: High**

## 改善点

* `watchdog_loop()` が HTTP と stdio の probe / restart / idle shutdown を持っており、**health check と lifecycle 制御が混在**している。
* `_watchdog_check_stdio()` は `transport.start()` を直接呼ぶため、**stdio 再起動が lifecycle manager を経由しない**。`ToolExecutor` との関係や再接続手順の一貫性を崩しやすい。
* `check_tool_definitions()` は useful だが、tool definition mismatch の扱いが startup 時 validation と runtime drift 検知で未分離である。

## 修正方針

* watchdog は health 判定のみ、再起動は lifecycle service へ委譲する。
* startup validation と runtime revalidation を別関数に分離する。

# `factory.py`

**重要度: Medium**

## 改善点

* 依存注入の中心として整理されているが、**plugin 初期化、audit logger、LLM client、tool executor、history manager、memory layer 構築が 1 モジュールに集中**している。
* `_build_memory_layer()` に deferred import を使って起動コスト削減している一方、**起動時 feature assembly の見通しがやや分散**する。

## 修正方針

* `build_agent_context()` を bootstrap 専用 orchestrator に寄せ、factory 自体は pure builder 群へ整理する。
* `observability`, `memory`, `tools`, `llm` の builder をサブモジュール分割する。

# `context.py`

## 改善点

* `AgentContext` は `ConversationState` / `TurnState` / `RuntimeStats` / `AppServices` を束ねる設計だが、**flat access の後方互換を維持**しているため、利用側からは state の境界が見えにくい。
* `ServiceContainer` deprecated も残っており、**移行完了前の構造物が長く残るリスク**がある。

## 修正方針

* 新規コードでの flat access 禁止を lint / review ルール化する。
* `ctx.history` など旧 API 参照箇所を段階的に `ctx.conversation.history` 等へ移す。

# `config.py`

## 改善点

* `AgentConfig` は 7 つの sub-config を compose しているが、**flat field access の後方互換が残っている**ため、設定の所属ドメインが曖昧になる。
* `load_config()` は例外時に warning を出して空 dict を返すため、**設定欠落が静かに既定値へフォールバックしやすい**。運用事故の検知が遅れる可能性がある。

## 修正方針

* 必須設定と任意設定を分離し、必須欠落時は fail-fast を採る。
* flat access を非推奨から削除フェーズへ進める。

# `cli_view.py`

## 改善点

* `Writer` / `Reader` Protocol は導入されているが、実装本体は `print`, `input`, `readline` 直結であり、**非対話環境・テスト環境への置換性はまだ限定的**である。
* `write_progress()` / `clear_progress()` は固定幅前提の簡易実装であり、**UI 表示とロジックの厳密分離までは未達**である。

## 修正方針

* stdout / stderr / input source を injectable にし、CLI 実装を terminal adapter へ寄せる。
* progress 表示は renderer 抽象化を導入する。

# `repl.py`

## 改善点

* 現状は Coordinator として薄く整理されているが、`SQLiteHelper`, `Logger`, health check, watchdog 起動まで抱えるため、**bootstrap 層として他の起動責務をさらに分離可能**である。

## 修正方針

* `AgentBootstrap` のような起動専用層を設け、REPL 本体は入出力ループのみに寄せる。

# `repl_debug.py`

## 改善点

* pure helper 化されており方向性はよいが、RAG debug builder と two-stage context detection が同居しており、**用途別モジュール分離の余地**がある。

## 修正方針

* `rag_debug.py` と `context_detection.py` へ分割する。

# `repl_tool_exec.py`

**重要度: High**

## 改善点

* 実体を `tool_approval.py`, `tool_audit.py`, `tool_policy.py`, `tool_result_formatter.py`, `tool_runner.py` へ分離した点はよいが、**re-export による後方互換層がそのまま public API を支配**している。
* テスト互換のため private alias を多数 export しており、**内部 API と外部 API の境界が曖昧**である。

## 修正方針

* テスト側 import を新モジュール構成へ更新し、alias export を段階的に削除する。
* public API を `tool_runner` 系の明示 export のみに縮小する。
