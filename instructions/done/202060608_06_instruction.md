# 1. 改修計画書

## 1.1 目的

本計画の目的は、後方互換性のために残されている façade / re-export / call-site 維持層を削除し、分割済みコンポーネントへ直接依存する構成へ移行することである。
特に、`config.py` の backward compatibility 用 re-export、`lifecycle.py` の互換 façade、`llm_turn_runner.py` の call-site 無変更前提の適応層、`session.py` の façade / re-export は優先的な見直し対象である。

## 1.2 全体方針

- 後方互換性のために残されている機能は削除する。明示的には、`config.py` 末尾の `DbConfig` / `build_db_config` の re-export は「Re-exported here for backward compatibility.」と記載されており、削除対象である。
- `lifecycle.py` は「Provides the same ServerLifecycleManager public API so all callers ... are unaffected.」と明記された façade であるため、HTTP / stdio lifecycle manager への直接依存へ移行し、この互換層は削除対象とする。
- `llm_turn_runner.py` は「same ctx/callbacks ... without changing the call-site interface」とされており、`orchestrator.py` からの移行を容易にするための適応層である。移行完了後は専用 interface に寄せ、互換前提の wiring は削減する。
- `session.py` は repository 群への façade であり、`DocumentRepository` / `NoteRepository` / `SessionMessageRepository` を re-export しているため、必要な repository を直接参照する構成に寄せる。

---

# 2. 対象ファイルと改修内容

## 2.1 `agent/config.py`

### 現状
`config.py` の末尾では、`DbConfig` と `build_db_config` を `db.config` から import し、「Re-exported here for backward compatibility.」として再公開している。

### 問題点
設定構築の本来の責務は `AgentConfig` / `build_agent_config()` にある一方で、DB 設定だけが別モジュールから互換 re-export されており、依存入口が二重化している。後方互換維持のためだけに残る API である。

### 改修方針
- `DbConfig` / `build_db_config` の re-export を削除する。
- 利用側は `db.config` を直接 import する構成へ移行する。

### 変更例
- 削除対象:
  - `from db.config import DbConfig, build_db_config` の module end re-export。

### 影響範囲
- `agent.config` から `DbConfig` / `build_db_config` を参照している caller に影響する。`build_agent_config()` 自体の利用には影響しない。

---

## 2.2 `agent/lifecycle.py`

### 現状
`lifecycle.py` は「MCP server lifecycle facade.」であり、`HttpServerLifecycleManager` と `StdioServerLifecycleManager` に委譲しつつ、「Provides the same ServerLifecycleManager public API so all callers (factory.py, repl.py, watchdog) are unaffected.」と明記している。

### 問題点
責務分割後も、旧 caller を無変更で残すための互換 façade が 1 層残っている。HTTP / stdio の本体ロジックはすでに `http_lifecycle.py` / `stdio_lifecycle.py` に抽出済みであり、`lifecycle.py` は適応層としての価値が中心になっている。

### 改修方針
- `ServerLifecycleManager` façade を削除対象とし、caller を `HttpServerLifecycleManager` / `StdioServerLifecycleManager` へ直接依存させる。
- 共通 state 管理や restart policy が必要なら、互換 API 維持ではなく、用途別 service bundling として再構成する。

### 変更例
- 削除対象:
  - `ServerLifecycleManager` façade。
- 移行先:
  - HTTP subprocess 起動 / restart / shutdown は `HttpServerLifecycleManager`。
  - stdio ondemand / idle shutdown / restart は `StdioServerLifecycleManager`。

### 影響範囲
- `factory.py` の `_build_tool_executor()` で生成している lifecycle。
- `repl.py` からの startup / shutdown / watchdog 呼び出し。
- `repl_health.py` の watchdog restart 経路。

---

## 2.3 `agent/llm_turn_runner.py`

### 現状
`llm_turn_runner.py` は「Extracted from orchestrator.py. LLMTurnRunner.run() replaces _run_turn().」と説明され、さらに「Accepts the same ctx/callbacks used by Orchestrator so it can be wired in without changing the call-site interface.」と記載されている。

### 問題点
`LLMTurnRunner` は分割された本体ロジックである一方、`Orchestrator` 側との互換 wiring を維持するために「same ctx/callbacks」を受ける設計になっている。これは移行途中の適応層であり、専用 interface に寄せきれていない。

### 改修方針
- `LLMTurnRunner` を `Orchestrator` 互換 adapter ではなく、turn-level LLM loop 専用 service として扱う。
- `ctx/callbacks` の互換的受け渡しを整理し、必要な依存だけを constructor 引数に持つ形へ改める。

### 変更例
- 削減対象:
  - `same ctx/callbacks ... without changing the call-site interface` を前提とした依存の受け方。
- 連動修正:
  - `orchestrator.py` 側で `LLMTurnRunner` 呼び出しを専用 interface に合わせる。

### 影響範囲
- `orchestrator.py` の `_handle_llm_turn()` / `_process_turn()`。
- `ErrorInjectionService` への mid-turn error 注入経路。

---

## 2.4 `agent/orchestrator.py`

### 現状
`orchestrator.py` は「Turn-level orchestration facade.」であり、`LLMTurnRunner` と `ToolLoopGuard` へ委譲する構造を取る。

### 問題点
`LLMTurnRunner` へ streaming + tool-call loop を渡しつつ、`Orchestrator` 側にも `_handle_llm_turn()`、`_process_turn()`、LLM transport error 処理、history append / rollback 相当の制御が残っているため、turn-level 制御と error handling の責務境界がまだ重なっている。

### 改修方針
- `Orchestrator` の責務を「turn lifecycle 管理」と「周辺 service 呼び出しの順序制御」に限定する。
- `LLMTurnRunner` 側へ寄せられるエラー処理・LLM loop 責務は移譲し、重複した例外ハンドリングを削減する。

### 変更例
- 見直し対象:
  - `_handle_llm_turn()` 内の `LLMTransportError` / `Exception` 捕捉と `TurnResult` 組み立て。
  - `_process_turn()` での再度の `LLMTransportError` 捕捉。

### 影響範囲
- `repl.py` の `AgentREPL._init_orchestrator()` と `run()` 経路。
- `LLMTurnRunner` の interface。

---

## 2.5 `agent/session.py`

### 現状
`session.py` は「AgentSession facade — delegates to domain-specific repository modules.」であり、`DocumentRepository`、`NoteRepository`、`SessionMessageRepository` を re-export しつつ、各 repository への単純委譲を多く持つ。

### 問題点
session lifecycle と repository delegation が 1 クラスにまとめられており、さらに repository の import を façade 経由にしているため、永続化責務の境界が不明瞭である。re-export により依存先も隠蔽されている。

### 改修方針
- `AgentSession` は session lifecycle 管理に責務を絞る。
- note/document/message repository は caller が直接依存できるようにし、`session.py` 側の re-export と単純委譲を削減する。

### 変更例
- 削除候補:
  - `DocumentRepository` / `NoteRepository` / `SessionMessageRepository` の re-export import。
  - note/document/message に関する単純 delegation method 群。

### 影響範囲
- `AgentREPL` や command layer が `AgentSession` にまとめて依存している箇所。
- `SessionMessageRepository` の session_id 更新ロジック。

---

## 2.6 `agent/factory.py`

### 現状
`factory.py` は `AgentContext assembly factory.` として service injection を担い、`ToolExecutor`、`HistoryManager`、memory layer、plugin registry、tracer、lifecycle を組み立てて `ctx.services` に注入している。

### 問題点
factory 自体は妥当な責務だが、`_build_tool_executor()` では `ServerLifecycleManager` を組み立て、互換 façade を前提とした wiring になっている。さらに memory layer など optional feature も façade ベースで束ねる構造であり、primitive service への直接 wiring に寄り切っていない。

### 改修方針
- `lifecycle.py` の façade 削除に合わせて、factory は `HttpServerLifecycleManager` / `StdioServerLifecycleManager` などの具体 service を直接配線する構成へ改める。
- 互換層前提の build helper を削減し、`ctx.services` へ入る service の単位を現在の責務分割に合わせる。

### 変更例
- 見直し対象:
  - `_build_tool_executor()` における `ServerLifecycleManager` 生成。
  - `build_agent_context()` の lifecycle / optional service 注入順。

### 影響範囲
- `repl.py` の `_init_components()`。
- `AgentContext.services` の構成。

---

## 2.7 `agent/repl.py`

### 現状
`repl.py` は entry point として `AgentContext`、`CLIView`、`CommandRegistry`、`Orchestrator`、health functions を束ねる。`AgentREPL responsibilities` として `_repl_loop`、`_init_components`、`run` が示されている。

### 問題点
entry point であること自体は妥当だが、startup sequence、health check wrapper、MCP server 起動、session 初期化、REPL loop が 1 クラスに集中している。分割は進んでいるが、依然として coordinator の責務が広い。

### 改修方針
- `AgentREPL` は entry point coordinator に留め、startup preparation と runtime loop を別コンポーネントへ切り分ける。
- [repl_health.py] に既に切り出した health/watchdog 処理への wrapper は縮小し、直接依存へ寄せる。

### 変更例
- 見直し対象:
  - `_check_service_health()` / `_check_tool_definitions()` / `_watchdog_loop()` の wrapper。
  - `_start_mcp_servers()` / `_check_services()` / `_setup_initial_prompt()` の startup sequence の分離。

### 影響範囲
- `run()` の起動順序全体。
- `factory.py`、`orchestrator.py`、`repl_health.py` との依存関係。

---

## 2.8 `agent/history.py` / `agent/history_selection_policy.py`

### 現状
`history.py` は `HistoryManager` として conversation compression を担い、`history_selection_policy.py` は「selection logic can be tested and configured independently」として抽出されている。

### 問題点
選別ロジックは外出しされているが、`HistoryManager` 側にも `_select_turns_to_compress()`、`_build_history_text()`、`_build_summary_msg()` など複数の補助責務が残っている。policy の独立化意図は良いが、圧縮候補選別と summary prompt 組み立てがまだ manager 側に残り、責務境界が完全には整理されていない。

### 改修方針
- `HistorySelectionPolicy` を選別責務の唯一の入口に寄せる。
- `HistoryManager` は token/char 監視と LLM compression 呼び出しに責務を絞る。

### 変更例
- 見直し対象:
  - `HistoryManager._select_turns_to_compress()`。
  - `HistorySelectionPolicy` へ移譲可能な importance / partition / selection ロジック。

### 影響範囲
- `factory.py` の `_build_history_manager()`。
- `orchestrator.py` の history compression 呼び出し。

---

# 3. 後方互換性のために残されている機能の削除対象

1. `agent/config.py` の `DbConfig` / `build_db_config` re-export。明示的に backward compatibility 用と記載されている。
2. `agent/lifecycle.py` の `ServerLifecycleManager` façade。same public API を維持し caller を unaffected にするための層である。
3. `agent/llm_turn_runner.py` の「same ctx/callbacks ... without changing the call-site interface」という適応レイヤー的設計。移行完了後は専用 interface に寄せて縮小対象とする。
4. `agent/session.py` の repository re-export と単純 delegation のうち、互換目的のみで保持されている部分。

---

# 4. 実施順序

## 4.1 Phase 1
- `config.py` の backward compatibility re-export 削除。
- `lifecycle.py` façade の廃止方針確定と caller の直接依存化。
- `session.py` façade / re-export の縮小。

## 4.2 Phase 2
- `llm_turn_runner.py` と `orchestrator.py` の interface / error handling 境界整理。
- `factory.py` の service wiring を互換層非依存に変更。

## 4.3 Phase 3
- `repl.py` の coordinator 責務縮小。
- `history.py` / `history_selection_policy.py` の責務境界明確化。
