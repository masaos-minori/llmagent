# マルチエージェント・オーケストレーション 実装計画書

作成日: 2026-05-28

## 0. 前提・設計方針

- 現行システムは **Agent 本体 + 複数 MCP サーバ** という構成であり、MCP サーバは `GET /health`、`GET /v1/tools`、`POST /v1/call_tool` を持つ **HTTP MCP** として運用されている。
  Agent 側は起動時に `/v1/tools` 差分検査を行い、必要に応じて watchdog で OpenRC サービス再起動も実行する。
- 現行 REPL は `AgentREPL._handle_user_message()` で **RAG → 履歴追記 → compress → LLM → tool loop** を 1 ターン処理として実装しており、`ToolExecutor` が tool 名から MCP サーバへルーティングする。
- 現行 Agent は `AgentContext` に `LLMClient`、`ToolExecutor`、`HistoryManager`、`RagPipeline`、`CommandRegistry`、`AgentSession` を注入する責務分離設計であり、複数 Runtime へ役割分化させる土台になる。
- 初期実装では、**独自 TCP やファイル監視ベースではなく、既存運用資産と整合する HTTP MCP ベース**を正式方式として採用する。ファイル監視型や独自 TCP は将来の補助オプションとして位置付ける。
- 本計画では、**Orchestrator を中核とし、Planner / PatchWorker / Validator / Integrator / Publisher を Phase 1 の最小役割構成**として採用する。Reviewer / Researcher / Memory Manager は Phase 2 以降で追加する。これは現行の `plan_mode`、RAG、tool loop、session 永続化を段階的に multi-agent へ拡張しやすいためである。
- 作業分離は **Git worktree** を第一候補とし、成果物は Git に集約する。現行 system には file / github MCP が存在し、ローカルファイル操作と GitHub 操作の責務が整理されているため、worktree 分離と統合制御の基盤として活用可能である。

---

## 1. 目的

単一の万能エージェントに巨大タスクを一括処理させるのではなく、**役割別エージェント群を並列稼働させ、タスク分解・実装・検証・統合を分担する階層型オーケストレーション基盤**を実現する。ユーザーが求める Planner / PatchWorker / Validator / Integrator / Publisher を Phase 1 の基本役割として実装し、将来的に Researcher / Reviewer / Memory Manager を追加する。

### 期待する効果

- 並列実行による高速化。複数 Worker が独立 worktree で並行に実装・検証を進められるため、単一 Agent の直列処理よりスループットを上げやすい。
- 専門特化による品質向上。
- 大規模 multi-file change への対応。現行 Agent は context budget / compress / tool loop の制約を持つため、context 分割型 multi-agent は大規模変更の安定性を上げやすい。
- 実装 → テスト失敗 → 修正 → 再検証の自動反復。現行 Agent は `/tool show`、`/undo`、`/session load`、tool result 保持を持つため、これを run / phase 単位へ昇格することで自動サイクル化が可能になる。

---

## 2. To-Be アーキテクチャ

### 2.1 推奨アーキテクチャ

```text
User
  ↓
orchestrator-mcp
  ├─ planner-agent
  ├─ patchworker-agent[*]
  ├─ validator-agent
  ├─ integrator-agent
  ├ publisher-agent
  ├─ reviewer-agent         (Phase 2)
  ├─ researcher-agent       (Phase 2)
  └─ memory-manager-agent   (Phase 2)
```

- **`orchestrator-mcp`** を新規 MCP サーバとして実装し、タスク分解、フェーズ管理、担当割当、barrier 管理、再試行判定、最終統合を担う。現行 AgentREPL の「薄いコーディネータ」思想を、単一ターンではなく複数 Worker 制御へ昇格させるイメージである。
- 各 Worker は専用の role prompt・allowed-tools・作業ディレクトリを持ち、**同一コードベースの WorkerRuntime** を role 別設定で起動する。現行 `AgentContext` / `AgentConfig` / `ToolExecutor` の責務分離構造は、複数 Runtime を並列起動する設計へ展開しやすい。
- PatchWorker は並列数可変とし、**`patchworker-agent[0..N-1]`** を worktree 単位で増やせるようにする。現行 file-mcp と github-mcp は多ファイル編集・GitHub 更新系の責務をすでに持つため、Worker ごとの成果物隔離と統合作業に転用可能である。

### 2.2 既存システムとの対応

- 現行 `AgentREPL` は単一ユーザー対話用フロントエンドとして残し、重作業は `orchestrator-mcp` へ委譲する。
- 既存 MCP サーバ群（web / file / github / 将来の rag-pipeline-mcp / mdq-mcp 等）は Worker 群も共通利用し、role ごとに `allowed_tools` 制御をかける。
- 現行 `AgentSession` / `notes` / audit 系情報は、将来的に **run 単位の保存**へ拡張する。すでに session 永続化・notes・tool result 保持の土台がある。

---

## 3. 役割設計

### 3.1 Phase 1 で採用する役割

#### Planner
- 役割: ユーザー要求を phase / task へ分解する。
- 使用ツール: 調査系中心。`search_docs`、RAG、`read_text_file`（限定）、`github_search_*`（必要時）。
- 禁止例: 直接 patch 作成、merge。

#### PatchWorker
- 役割: 局所変更の実装。
- 使用ツール: file-mcp の編集系、必要なら branch / patch 作成系。現行 file-mcp は `write_file` / `edit_file` / `move_file` / `grep_files` を持つ。
- 実行単位: worktree 単位で隔離。

#### Validator
- 役割: テスト実行、lint / typecheck / runtime 検証、失敗要因抽出。
- 使用ツール: 将来的な local execution MCP、file 系 read、テスト結果参照。
- 出力: `pass/fail`, error summary, retry hint。

#### Integrator
- 役割: 複数 PatchWorker 成果の統合、conflict 解消、最終組み立て。
- 使用ツール: git / file / review 結果参照。
- 最終責務: merge-ready な成果物を作る。

### 3.2 Phase 2 以降で追加する役割

#### Reviewer
- 役割: patch diff のレビュー、設計逸脱検出、ガイドライン適合確認。
- 使用ツール: read / grep / outline / diff 参照。原則書き込み禁止。

#### Retriever / Researcher
- 役割: 実装前調査、仕様探索、差分影響調査。
- 使用ツール: web-search-mcp、mdq-mcp、file-mcp の read / grep 系。
- 出力: 調査メモ、参照箇所一覧、影響ファイル一覧。

#### Memory Manager
- 役割: 長期知識・ルール・失敗知見の整理。
- 使用ツール: notes、将来的な mdq-mcp / memory MCP。
- 出力: 再利用可能な guideline / lesson learned。

---

## 4. オーケストレーター責務

### 4.1 中核責務

Orchestrator は以下を担う。これはユーザー提示要件と一致する。
- タスク分解
- Worker 割当
- phase 管理
- barrier 管理
- merge / test / retry 判定

現行 Agent は単一ターンの tool loop を管理するが、multi-agent ではこれを**phase loop**へ格上げする必要がある。

### 4.2 推奨 phase

1. `plan`
2. `implement`
3. `validate`
4. `integrate`
5. `finalize`

Phase 2 以降では以下を追加する。
- `research`
- `review`
- `memory_update`

### 4.3 Barrier / phase 同期

- `plan` 完了まで `patchworker` 配布を待たせる barrier。
- 全 PatchWorker 完了まで `integrator` を待たせる barrier。
- `Validator fail` 時は `PatchWorker` または `Integrator` へ retry routing。

これはユーザー要件の「phase 同期」「バリア同期」「議論ループ」の最小実装であり、現行の `serial_tool_calls` による順序保証や `/plan` による段階制御の発展形として位置付けられる。

---

## 5. 通信方式・制御方式

### 5.1 採用方式

**初期実装は HTTP MCP を正式採用**する。

理由は以下。
- 現行基盤がすでに HTTP MCP / `/v1/call_tool` / `/v1/tools` / OpenRC / watchdog で統一されている。
- 既存 `ToolExecutor` が HTTP ルーティング・TTL キャッシュ・エラーハンドリングを持つ。
- 新 transport を増やすより、まず既存運用と整合する方が安全である。

### 5.2 実装上の通信モデル

```text
AgentREPL or client
  -> orchestrator-mcp
     -> worker runtimes
     -> file-mcp / github-mcp / web-search-mcp / rag-pipeline-mcp / mdq-mcp
```

初期実装では、**worker-control-mcp を別に設けず `orchestrator-mcp` 自身が worker 管理を行う**。これは構成を単純化し、既存 MCP 運用へ最短で乗せるためである。

---

## 6. 状態同期・共有コンテキスト設計

### 6.1 共有状態の分離

状態同期は最難所であり、以下の 3 層に分けるべきである。

1. **Run-level state**
   - `run_id`
   - `phase`
   - `task graph`
   - `worker assignments`
   - `barrier state`

2. **Artifact-level state**
   - `worktree path / branch`
   - `changed files`
   - `patch status`
   - `validation status`

3. **Knowledge-level state**
   - `research notes`
   - `review comments`
   - `retry reasons`
   - `accepted decisions`

現行 system には `sessions/messages/notes/tool_result_store` があるが、multi-agent ではこれを **run-oriented state** へ昇格させる必要がある。

### 6.2 推奨保存方式

初期実装は以下を推奨する。
- **JSONL 物理ログ**
- **SQLite メタDB**
- **Git / worktree に成果物集約**

これは既存の SQLite 利用、audit / observability、ファイルベースデプロイ運用と親和性が高い。SQLite はすでに sessions/messages/documents/chunks 管理で使われているため、新規に `orchestrator.sqlite` を追加しても自然である。

### 6.3 共有コンテキスト方針

- Planner と Researcher は **要約メモ**を共有。
- PatchWorker は **必要な差分仕様だけ**を受け取る。
- Validator / Integrator は **成果物と task-specific context** を受け取る。
- 全員が全履歴を共有しない。

これはユーザー要件の「コンテキスト分割による品質安定」「コンテキスト肥大化抑制」に合致し、現行 system の context budget / compression / notes の考え方とも整合する。

---

## 7. Worker 実装方針

### 7.1 共通 Worker Runtime

各 Worker を完全別実装にせず、**role-specific prompt と allowed-tools を差し替えた共通 Runtime**にする。現行 Agent はすでに以下の構造を持つため、これを WorkerRuntime へ再利用する。

- `AgentContext`
- `LLMClient`
- `ToolExecutor`
- `HistoryManager`
- `CommandRegistry`
- `AgentConfig`

つまり、`AgentREPL` の単一ユーザー対話部分を薄くし、**WorkerRuntime** として切り出す発想である。

### 7.2 role-specific prompt / allowed-tools

各 Worker には以下を持たせる。
- `role_prompt`
- `persona`
- `allowed_tools`
- `disallowed_tools`
- `input_budget`
- `output_contract`

例:
- Planner → senior architect / research-heavy / no write
- PatchWorker → senior engineer / file write / no merge
- Validator → tester / execution tools only
- Integrator → integrator / merge authority

現行 `system_prompts`、`/system` 切替、`plan_mode`、`require_approval_tools` などの仕組みは、この role 制御へ拡張しやすい。

---

## 8. 作業分離方式

### 8.1 推奨: Git worktree

**Git worktree** を第一候補とする。
理由は以下。
- 同一リポジトリの複数作業を並列化しやすい。
- PatchWorker ごとに独立ファイル空間を持てる。
- Integrator が最終的に統合しやすい。

現行には `file-mcp` と `github-mcp` があり、ローカルファイル変更と GitHub 反映の両方を責務分離しているため、worktree 分離との親和性が高い。

### 8.2 成果物管理

各 Worker 成果物は以下で管理する。
- `runs/<run_id>/workers/<worker_id>/` メタ情報
- `worktrees/<run_id>/<worker_id>/` 作業領域
- `artifacts/<run_id>/` 収集物（diff, logs, summaries）
- Git commit / patch file / validation report

---

## 9. 実装コンポーネント

### 9.1 新規追加コンポーネント
- `scripts/orchestrator_mcp_server.py`
- `scripts/orchestrator_models.py`
- `scripts/orchestrator_state.py`
- `scripts/worker_runtime.py`
- `scripts/worker_launcher.py`
- `scripts/worktree_manager.py`
- `scripts/orchestrator_scheduler.py`
- `scripts/orchestrator_barrier.py`
- `config/orchestrator_mcp_server.json`
- `init.d/orchestrator-mcp`

### 9.2 SQLite / JSONL
- `db/orchestrator.sqlite`
- `logs/orchestrator_events.jsonl`
- `logs/worker_<id>.log`

### 9.3 既存改修対象
- `tool_executor.py`
  - `orchestrator_*` ツールの新規ルーティング追加。
- `agent_repl.py`
  - 単一 Agent 実行ではなく Orchestrator 呼び出しモードの追加。
- `agent_commands.py`
  - `/mcp` 表示へ orchestrator-mcp を追加。
  - 将来的に `/orchestrate` コマンドを追加。
- `deploy/deploy.sh` / `deploy/setup_services.sh`
  - 新規サービスと設定配置追記。

---

## 10. `orchestrator-mcp` の `/v1/tools` 定義（JSON相当）

現行 MCP 共通仕様では `/v1/tools` はツール名・説明一覧を返す最小形式であるが、Orchestrator では `input_schema` / `output_schema` を含む拡張形式が望ましい。これは run 制御・status 管理・retry 制御に構造化 I/O が必要なためである。現行 MCP は `{"result": str, "is_error": bool}` を中心とするが、orchestrator では `result_data` を使う前提で設計する。

### 10.1 推奨拡張形式

```json
{
  "server_name": "orchestrator-mcp",
  "server_version": "1.0.0",
  "tools": [
    {
      "name": "orchestrate_task",
      "description": "Create and execute a multi-agent run from a user task.",
      "input_schema": {
        "type": "object",
        "properties": {
          "task": { "type": "string", "description": "User task to execute." },
          "repo_path": { "type": "string", "description": "Repository root path." },
          "mode": { "type": "string", "description": "Execution mode, e.g. standard or deep." },
          "max_patchworkers": { "type": "integer", "minimum": 1 },
          "constraints": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Execution constraints or guardrails."
          }
        },
        "required": ["task", "repo_path"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "phase": { "type": "string" },
          "plan": { "type": "array", "items": { "type": "object" } },
          "workers": { "type": "array", "items": { "type": "object" } }
        },
        "required": ["run_id", "phase"]
      }
    },
    {
      "name": "get_run_status",
      "description": "Get current status of an orchestrated run.",
      "input_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" }
        },
        "required": ["run_id"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "phase": { "type": "string" },
          "barrier_state": { "type": "object" },
          "workers": { "type": "array", "items": { "type": "object" } },
          "progress": { "type": "object" }
        },
        "required": ["run_id", "phase"]
      }
    },
    {
      "name": "get_run_artifacts",
      "description": "Get artifacts produced by a run, such as patches, validation results and summaries.",
      "input_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" }
        },
        "required": ["run_id"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "artifacts": { "type": "array", "items": { "type": "object" } },
          "integrated_diff": { "type": "string" },
          "validation_summary": { "type": "object" }
        },
        "required": ["run_id", "artifacts"]
      }
    },
    {
      "name": "retry_phase",
      "description": "Retry a failed or blocked phase in an orchestrated run.",
      "input_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "phase": { "type": "string" },
          "reason": { "type": "string" }
        },
        "required": ["run_id", "phase"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "phase": { "type": "string" },
          "retry_count": { "type": "integer" },
          "workers": { "type": "array", "items": { "type": "object" } }
        },
        "required": ["run_id", "phase"]
      }
    },
    {
      "name": "abort_run",
      "description": "Abort a running orchestration and perform cleanup.",
      "input_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "cleanup": { "type": "boolean" }
        },
        "required": ["run_id"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "aborted": { "type": "boolean" },
          "cleanup_summary": { "type": "object" }
        },
        "required": ["run_id", "aborted"]
      }
    },
    {
      "name": "list_workers",
      "description": "List active worker runtimes and their health states.",
      "input_schema": {
        "type": "object",
        "properties": {}
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "workers": { "type": "array", "items": { "type": "object" } }
        },
        "required": ["workers"]
      }
    }
  ]
}
```

### 10.2 最小互換形式

既存 `/v1/tools` の最小互換形式を維持する場合は、まずは以下のような `name` / `description` のみでもよい。現行 MCP ではこれが最も互換性が高い。

```json
{
  "tools": [
    { "name": "orchestrate_task", "description": "Create and execute a multi-agent run from a user task." },
    { "name": "get_run_status", "description": "Get current status of an orchestrated run." },
    { "name": "get_run_artifacts", "description": "Get artifacts produced by a run." },
    { "name": "retry_phase", "description": "Retry a failed or blocked phase in an orchestrated run." },
    { "name": "abort_run", "description": "Abort a running orchestration and perform cleanup." },
    { "name": "list_workers", "description": "List active worker runtimes and their health states." }
  ]
}
```

---

## 11. `config/agent.json` の `mcp_servers` 追記例

現行 Agent は MCP サーバ群を `HTTP` で呼び出し、起動時に `/v1/tools` 差分検査や watchdog によるヘルスチェックを実施する。新規 `orchestrator-mcp` を既存 MCP 群と同列に扱うには、`mcp_servers` セクションへ接続情報と OpenRC サービス名を追記する必要がある。

以下は追記例である。ポート番号は例として `8009` を採用する。既存 MCP の `8004/8005/8006`、想定される追加 MCP 群（`rag-pipeline-mcp` など）の後段として扱いやすい。

```json
{
  "mcp_servers": {
    "web_search": {
      "transport": "http",
      "url": "http://127.0.0.1:8004",
      "cmd": [],
      "openrc_service": "web-search-mcp"
    },
    "file": {
      "transport": "http",
      "url": "http://127.0.0.1:8005",
      "cmd": [],
      "openrc_service": "file-mcp"
    },
    "github": {
      "transport": "http",
      "url": "http://127.0.0.1:8006",
      "cmd": [],
      "openrc_service": "github-mcp"
    },
    "orchestrator": {
      "transport": "http",
      "url": "http://127.0.0.1:8009",
      "cmd": [],
      "openrc_service": "orchestrator-mcp"
    }
  }
}
```

### 11.1 追記方針

- キー名は `orchestrator` を推奨する。`ToolExecutor` 側で専用ルーティングを追加しやすく、他の `web_search` / `file` / `github` と命名粒度が揃うため。
- `transport` は現行 MCP と同じく `http` を前提とする。現行 Agent は HTTP MCP を標準運用としている。
- `openrc_service` は watchdog が `rc-service restart` に使用するため、OpenRC スクリプト名と一致させる必要がある。現行仕様でも watchdog は `mcp_servers` の `openrc_service` を参照する。

---

## 12. `config/agent.json` の `tool_definitions` 追記例

現行 Agent は `config/agent.json` の `tool_definitions` を LLM に与え、LLM が tool calling により MCP ツールを選択する。`orchestrator-mcp` を統合制御サーバとして組み込むには、`tool_definitions` にも orchestrator 用ツール群を追加する必要がある。

以下は OpenAI 互換 function calling 形式での追記例である。現行 Agent も `tool_definitions` をこの形式で扱う前提である。

```json
{
  "tool_definitions": [
    {
      "type": "function",
      "function": {
        "name": "orchestrate_task",
        "description": "Create and execute a multi-agent run from a user task.",
        "parameters": {
          "type": "object",
          "properties": {
            "task": { "type": "string", "description": "User task to execute." },
            "repo_path": { "type": "string", "description": "Repository root path." },
            "mode": { "type": "string", "description": "Execution mode." },
            "max_patchworkers": { "type": "integer", "minimum": 1 },
            "constraints": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["task", "repo_path"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_run_status",
        "description": "Get current status of an orchestrated run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_run_artifacts",
        "description": "Get artifacts produced by a run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "retry_phase",
        "description": "Retry a failed or blocked phase in an orchestrated run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "phase": { "type": "string" },
            "reason": { "type": "string" }
          },
          "required": ["run_id", "phase"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "abort_run",
        "description": "Abort a running orchestration and perform cleanup.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "cleanup": { "type": "boolean" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "list_workers",
        "description": "List active worker runtimes and their health states.",
        "parameters": {
          "type": "object",
          "properties": {}
        }
      }
    }
  ]
}
```

### 12.1 追記方針

- `orchestrate_task` は通常経路で使用し、multi-agent 実行の標準入口とする。単一 Agent の `AgentREPL._handle_user_message()` より上位の run 管理入口に相当する。
- `get_run_status` / `get_run_artifacts` は `/runs` 的な観測機能の基礎になる。現行 Agent の `/mcp` / `/stats` / `/context` の延長線上に位置付けられる。
- `retry_phase` / `abort_run` は、phase loop と stuck recovery を機械化するために必要である。ユーザー要件の retry / barrier / lifecycle 管理に対応する。
- `list_workers` は worker health と割当確認に使う。watchdog / observability とも整合する。

---

## 13. `agent.json` への統合追記例（抜粋）

以下は、`mcp_servers` と `tool_definitions` をまとめて追記したときのイメージである。既存定義がある前提のため、抜粋として示す。

```json
{
  "mcp_servers": {
    "web_search": {
      "transport": "http",
      "url": "http://127.0.0.1:8004",
      "cmd": [],
      "openrc_service": "web-search-mcp"
    },
    "file": {
      "transport": "http",
      "url": "http://127.0.0.1:8005",
      "cmd": [],
      "openrc_service": "file-mcp"
    },
    "github": {
      "transport": "http",
      "url": "http://127.0.0.1:8006",
      "cmd": [],
      "openrc_service": "github-mcp"
    },
    "orchestrator": {
      "transport": "http",
      "url": "http://127.0.0.1:8009",
      "cmd": [],
      "openrc_service": "orchestrator-mcp"
    }
  },
  "tool_definitions": [
    {
      "type": "function",
      "function": {
        "name": "orchestrate_task",
        "description": "Create and execute a multi-agent run from a user task.",
        "parameters": {
          "type": "object",
          "properties": {
            "task": { "type": "string" },
            "repo_path": { "type": "string" },
            "mode": { "type": "string" },
            "max_patchworkers": { "type": "integer" },
            "constraints": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["task", "repo_path"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_run_status",
        "description": "Get current status of an orchestrated run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_run_artifacts",
        "description": "Get artifacts produced by a run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "retry_phase",
        "description": "Retry a failed or blocked phase in an orchestrated run.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "phase": { "type": "string" },
            "reason": { "type": "string" }
          },
          "required": ["run_id", "phase"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "abort_run",
        "description": "Abort a running orchestration and perform cleanup.",
        "parameters": {
          "type": "object",
          "properties": {
            "run_id": { "type": "string" },
            "cleanup": { "type": "boolean" }
          },
          "required": ["run_id"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "list_workers",
        "description": "List active worker runtimes and their health states.",
        "parameters": {
          "type": "object",
          "properties": {}
        }
      }
    }
  ]
}
```

---

## 14. MCP レスポンス形式（推奨）

現行 MCP 共通仕様は `{"result": str, "is_error": bool}` を中心とするが、Orchestrator では run / phase / worker / artifacts などの構造化返却が必要になる。そのため、後方互換を保ちながら以下の拡張形式を推奨する。

```json
{
  "result": "orchestrate_task started. run_id=run-20260528-001",
  "result_text": "orchestrate_task started. run_id=run-20260528-001",
  "result_data": {
    "run_id": "run-20260528-001",
    "phase": "implement",
    "workers": [
      {"worker_id": "planner-0", "role": "planner", "status": "completed"},
      {"worker_id": "patchworker-0", "role": "patchworker", "status": "running"}
    ],
    "plan": [
      {"task_id": "t1", "summary": "Refactor config loader", "assigned_to": "patchworker-0"}
    ]
  },
  "is_error": false,
  "error_code": null,
  "truncated": false,
  "meta": {
    "phase": "implement",
    "elapsed_ms": 184.2
  }
}
```

方針は以下。
- `result_text`: 人間向け要約。
- `result_data`: 実データ。
- `meta`: phase / elapsed / retry count / barrier info 等。
- `truncated=true` の場合、artifact 一覧や diff が制限されたことを示す。

---

## 15. Phase 1 実装順序

### Step 1: `orchestrator-mcp` 最小起動
- `GET /health`
- `GET /v1/tools`
- `POST /v1/call_tool`
- `orchestrate_task`
- `get_run_status`

### Step 2: WorkerRuntime 共通化
- Planner / PatchWorker / Validator / Integrator の role preset
- role-specific prompt / allowed-tools
- `chat_url` / `code_url` の role 切替利用

### Step 3: worktree manager
- run_id / worker_id 単位の worktree 作成
- cleanup
- artifact 収集

### Step 4: validation fail -> retry
- Validator report の取得
- retry_phase
- abort / stuck handling

### Step 5: `/mcp` / watchdog / OpenRC 統合
- `mcp_servers` 追記
- OpenRC スクリプト追加
- `/mcp` 表示反映


## 16. 結論

1. `orchestrator-mcp` の追加。
2. Planner / PatchWorker / Validator / Integrator の 4 役から開始。
3. HTTP MCP + worktree + SQLite/JSONL による中央集権型同期。
4. role-specific prompt / allowed-tools 制御の導入。
5. validation fail -> retry の自動ループまでを Phase 1 完了条件とする。
