## 1. Goal

### 1.1 現行設計の確認

現行は `agent.py` を起点とする CLI REPL 構成である。
中央制御の多くが `AgentREPL` に集中している。
このため、現行は単一 REPL coordinator 構成であり、役割ごとに分離したマルチエージェント構成ではない。

現在 `AgentREPL` に集中している主な責務は以下である。

- ユーザー入力受付
- slash command 実行
- RAG 実行
- LLM 呼び出し
- tool loop 実行
- MCP 呼び出し
- 会話履歴更新
- セッション保存
- 実行中状態の一部管理

### 1.2 改修目標

中央 `Orchestrator` を中核とする構成へ移行する。
後方互換性は考慮しない。

改修目標は以下である。

- `agent.py` に集中した責務を `Orchestrator` に分離する
- `agent.py` は CLI REPL として維持する
- REPL は UI と command のみに限定する
- `AgentContext` は conversation state のみに限定する
- `workflow/task/artifact/retry/approval` の正本を `state_manager.py` に一本化する
- `Planner / Retriever / PatchWorker / Integrator / Validator / Publisher` を独立プロセスの MCP Server とする
- 各 MCP Server は単一責務に限定する
- RAG 実行は `Retriever MCP Server` に分離する
- `Orchestrator` に workflow 制御、状態管理、承認、ポリシー、repository 操作管理を集約する
- 1 session : N workflows を許可する
- workflow は `workflow_id` で独立管理する
- session は UI 表示と起点履歴のみに使う
- 依存関係がない task は並列実行を許可する
- approval 対象は GitHub 書き込みから Draft PR 作成までとする

### 1.3 目標フロー

目標フローは以下とする。

1. `Planner` が変更要求を `change_set` に分解する
2. `Orchestrator` が `change_set` を複数の `file task` に展開する
3. `Retriever` が evidence と context を収集する
4. `PatchWorker` が各 file の変更案と diff を生成する
5. `Integrator` が file 群を `patch_set` に統合する
6. `Validator` が `patch_set` 全体を検証する
7. `Orchestrator` が policy と approval を判定する
8. `Publisher` が branch 作成、commit、push、Draft PR 作成、final summary を行う

補足は以下である。

- `Integrator` は統合専用とする
- `Publisher` は公開専用とする
- `Integrator` と `Publisher` は責務が異なるため分離する

### 1.4 採用方針

採用方針は以下とする。

- MCP 通信方式は HTTP / stdio を主方式とする
- `GET /health`、`GET /v1/tools`、`POST /v1/call_tool` を標準インタフェースとする
- 既存 watchdog、`/mcp` 表示、MCP health 運用と整合させる
- 初期構成は `Planner / Retriever / PatchWorker / Integrator / Validator / Publisher` の 6 role とする
- `Reviewer / Researcher / Memory Manager` は Phase 2 以降の拡張候補とする
- 作業分離は Git worktree を第一候補とする
- 成果物は Git と `workflow.sqlite` に集約する

## 2. Scope

### 2.1 対象ファイル

既存ファイルは以下とする。

- `agent.py`
- `agent_repl.py`
- `agent_context.py`
- `agent_commands.py`
- `agent_rag.py`
- `config/agent.json`
- `config/common.json`

新規ファイルは以下とする。

- `orchestrator.py`
- `workflow_engine.py`
- `task_scheduler.py`
- `retry_controller.py`
- `state_manager.py`
- `orchestrator_models.py`
- `approval_gate.py`
- `policy_engine.py`
- `repository_gateway.py`
- `mcp_registry.py`
- `planner_mcp_server.py`
- `retriever_mcp_server.py`
- `patch_worker_mcp_server.py`
- `integrator_mcp_server.py`
- `validator_mcp_server.py`
- `publisher_mcp_server.py`
- `audit_logger.py`
- `worker_runtime.py`
- `worker_launcher.py`
- `worktree_manager.py`
- `orchestrator_scheduler.py`
- `orchestrator_barrier.py`
- `scripts/orchestrator_mcp_server.py`
- `scripts/orchestrator_state.py`
- `config/orchestrator_mcp_server.json`
- `init.d/orchestrator-mcp`

### 2.2 永続化

永続化対象は以下とする。

- workflow 管理 DB は `workflow.sqlite`
- event 監査ログは JSONL 併用を許可する
- worker 個別ログをファイル出力する

推奨ログ・DB 配置例は以下とする。

- `db/workflow.sqlite`
- `db/rag.sqlite`
- `logs/orchestrator_events.jsonl`
- `logs/worker_<id>.log`

### 2.3 対象 role

`Planner` の責務は以下とする。

- task graph 設計
- dependency 定義
- acceptance criteria 定義

`Retriever` の責務は以下とする。

- evidence 収集
- context 提供
- RAG 実行

`PatchWorker` の責務は以下とする。

- file 単位 patch 生成
- local / GitHub 対象編集案作成
- diff 作成

`Integrator` の責務は以下とする。

- `patch_set` 統合
- file patch 群の整合確認
- validator 入力 artifact 生成
- integration summary 生成

`Validator` の責務は以下とする。

- syntax check
- lint
- unit test

`Publisher` の責務は以下とする。

- branch 作成
- commit
- push
- Draft PR 作成
- final summary

## 3. Design

### 3.1 全体構成

```text
agent.py
  -> agent_repl.py
    -> orchestrator.py
      -> workflow_engine.py
      -> task_scheduler.py
      -> retry_controller.py
      -> state_manager.py
      -> approval_gate.py
      -> policy_engine.py
      -> repository_gateway.py
      -> mcp_registry.py
      -> planner_mcp_server.py
      -> retriever_mcp_server.py
      -> patch_worker_mcp_server.py
      -> integrator_mcp_server.py
      -> validator_mcp_server.py
      -> publisher_mcp_server.py
```

### 3.2 REPL 層

`agent.py` の責務は以下とする。

- CLI entrypoint
- REPL 起動

`agent_repl.py` の責務は以下とする。

- ユーザー入力受付
- progress 表示
- slash command 受付
- workflow 結果表示

`agent_context.py` の責務は以下とする。

- conversation state のみ保持する
- workflow/task/artifact/retry/approval は保持しない

設計原則は以下とする。

- REPL は UI と command のみに限定する
- workflow 実行責務は `orchestrator.py` に集中する
- `AgentContext` は会話履歴と表示状態のみを持つ

### 3.3 Orchestrator

#### 3.3.1 `orchestrator.py`

`orchestrator.py` の責務は以下とする。

- workflow 起動
- `change_set` の `file task` 展開
- role MCP Server 呼び出し
- dependency 実行制御
- state 更新
- retry 制御
- approval / policy 制御
- barrier 制御
- final result 返却

主要 API は以下を基本とする。

- `start_workflow(session_id, request_text, mode)`
- `resume_workflow(workflow_id)`
- `cancel_workflow(workflow_id)`
- `get_workflow_status(workflow_id)`
- `get_workflow_artifacts(workflow_id)`
- `retry_phase(workflow_id, phase, reason)`

#### 3.3.2 `workflow_engine.py`

責務は以下とする。

- workflow state machine
- task state transition
- approval 待ち遷移
- terminal state 判定
- phase 進行管理

状態例は以下とする。

- workflow: `pending`, `running`, `waiting_approval`, `completed`, `failed`, `cancelled`
- task: `queued`, `ready`, `running`, `succeeded`, `failed`, `blocked`, `skipped`

推奨 phase は以下とする。

- `plan`
- `retrieve`
- `implement`
- `integrate`
- `validate`
- `publish`
- `finalize`

#### 3.3.3 `task_scheduler.py`

責務は以下とする。

- runnable task 抽出
- dependency 解決
- 並列 dispatch
- role 別 concurrency 制御
- barrier 連携

設計方針は以下とする。

- DAG 前提
- dependency がない `file task` は並列実行する
- 同一 file は直列化する
- GitHub 書き込み相当 task は排他制御する

#### 3.3.4 `retry_controller.py`

責務は以下とする。

- failure classification
- retry 可否判定
- backoff 算出
- role 別 retry 上限管理

設計方針は以下とする。

- 一時的通信失敗は retry する
- syntax/lint/unit test failure は原則 deterministic failure として扱う
- retry は role / error class ごとに制御する

#### 3.3.5 `state_manager.py`

責務は以下とする。

- workflow/task/artifact/retry/approval の正本管理
- `workflow.sqlite` 永続化
- resume / replay 用復元
- event 記録

管理対象の論理テーブルは最低限以下とする。

- `workflows`
- `workflow_tasks`
- `workflow_dependencies`
- `workflow_artifacts`
- `workflow_retries`
- `workflow_approvals`
- `workflow_events`
- `mcp_endpoints`
- `mcp_health_status`

#### 3.3.6 `approval_gate.py`

責務は以下とする。

- GitHub write 系操作の承認制御
- approval request 作成
- approval record 保存
- `waiting_approval` 遷移制御

approval 対象は以下とする。

- file create / update / delete
- push
- Draft PR 作成

#### 3.3.7 `policy_engine.py`

責務は以下とする。

- repository 制約判定
- branch 制約判定
- path 制約判定
- action allow / deny 判定

設計方針は以下とする。

- deny by default
- policy 通過後のみ approval に進める

#### 3.3.8 `repository_gateway.py`

責務は以下とする。

- local / GitHub repository I/O 抽象化
- `file-mcp` / `github-mcp` 利用の共通化
- diff / branch / push / PR 操作の窓口統一

設計方針は以下とする。

- `PatchWorker` と `Publisher` から直接 `github-mcp` を乱用させない
- repository 操作を 1 箇所に集中する

#### 3.3.9 `mcp_registry.py`

責務は以下とする。

- MCP endpoint 登録
- health check
- capability 取得
- `/mcp` 表示用情報提供

#### 3.3.10 `audit_logger.py`

責務は以下とする。

- approval / retry / failure / GitHub write の監査ログ記録
- `workflow_id` / `task_id` / `patch_set` 単位の追跡性担保

### 3.4 role MCP Server

#### 3.4.1 `Planner` (`planner_mcp_server.py`)

役割は以下とする。

- task graph 設計
- dependency 定義
- acceptance criteria 定義

入力は以下とする。

- user request
- session context
- repository context

出力は以下とする。

- `goal`
- `change_sets`
- `tasks`
- `dependencies`
- `acceptance_criteria`

#### 3.4.2 `Retriever` (`retriever_mcp_server.py`)

役割は以下とする。

- evidence 収集
- context 提供
- RAG 実行

入力は以下とする。

- request
- change_set
- repository / doc context

出力は以下とする。

- evidence list
- context package
- source metadata

設計方針は以下とする。

- `agent_rag.py` の core を service 化して再利用する
- RAG 実行を REPL から切り離す

#### 3.4.3 `PatchWorker` (`patch_worker_mcp_server.py`)

役割は以下とする。

- file 単位 patch 生成
- local / GitHub 対象編集案作成
- diff 作成

入力は以下とする。

- file task
- evidence / context
- repository target
- constraints

出力は以下とする。

- file patch
- diff
- rationale
- changed file summary

設計方針は以下とする。

- 基本単位は `file` とする
- write 実行は持たせない
- worktree 単位隔離を前提とする

#### 3.4.4 `Integrator` (`integrator_mcp_server.py`)

役割は以下とする。

- `patch_set` 統合
- file patch 群の整合確認
- validator 入力 artifact 生成
- integration summary 生成

入力は以下とする。

- file patch 群
- repository context
- validation 前提情報

出力は以下とする。

- `patch_set`
- integrated diff
- validation 用 artifact
- integration summary

設計方針は以下とする。

- `patch_set` 統合に限定する
- Git 操作は持たない

#### 3.4.5 `Validator` (`validator_mcp_server.py`)

役割は以下とする。

- syntax check
- lint
- unit test

入力は以下とする。

- `patch_set`
- repository state
- scope

出力は以下とする。

- syntax result
- lint result
- unit test result
- failed case list
- logs
- summary

設計方針は以下とする。

- 検証単位は `patch_set` 全体とする
- file 単位でなく論理変更単位で整合性確認する

#### 3.4.6 `Publisher` (`publisher_mcp_server.py`)

役割は以下とする。

- branch 作成
- commit
- push
- Draft PR 作成
- final summary

入力は以下とする。

- validation 済み `patch_set`
- repository context
- approval / policy 状態

出力は以下とする。

- branch 名
- commit plan
- push result
- Draft PR payload
- final summary

設計方針は以下とする。

- 公開責務に限定する
- approval 済み成果物のみを扱う
- merge は持たない

### 3.5 共有状態と成果物管理

session と workflow の関係は以下とする。

- 1 session : N workflows
- workflow は `workflow_id` で独立管理する
- session は UI 表示と起点履歴に限定する

共有状態は以下 3 層に分ける。

- run-level state
- artifact-level state
- knowledge-level state

成果物管理は以下を基本とする。

- `runs/<workflow_id>/workers/<worker_id>/` に worker メタ情報
- `worktrees/<workflow_id>/<worker_id>/` に作業領域
- `artifacts/<workflow_id>/` に diff、logs、summaries を保存
- Git commit、patch file、validation report を成果物として扱う

artifact 保存方式は当面 DB inline を採用する。対象例は以下とする。

- diff
- `patch_set`
- validator logs
- evidence bundle
- Draft PR payload

### 3.6 Orchestrator MCP 公開面

`orchestrator-mcp` は少なくとも以下の MCP tool を提供する。

- `orchestrate_task`
- `get_run_status`
- `get_run_artifacts`
- `retry_phase`
- `abort_run`
- `list_workers`

`config/agent.json` には `mcp_servers.orchestrator` を追加する。

- key: `orchestrator`
- transport: `http`
- url: `http://127.0.0.1:8009`
- openrc_service: `orchestrator-mcp`

tool 定義には orchestrator 用 function calling 定義を追加する。

- `orchestrate_task`
- `get_run_status`
- `get_run_artifacts`
- `retry_phase`
- `abort_run`
- `list_workers`

### 3.7 不足する役割

必須の追加 external role は `Publisher` とする。
理由は以下とする。

- `Integrator` の統合責務と GitHub 公開責務は異なる
- approval 境界を `Publisher` の前に置ける
- retry policy を統合失敗と公開失敗で分離できる

Phase 2 以降の拡張候補は以下とする。

- `Reviewer`
- `Researcher`
- `Memory Manager`

内部補助コンポーネントとして `audit_logger.py` を追加推奨とする。

## 4. Implementation steps

各段階は単独でレビュー可能な単位で分割する。
各 Phase は完了条件を持つ。

### 4.1 Phase 0. 責務境界の固定

対象は以下とする。

- `agent.py`
- `agent_repl.py`
- `agent_context.py`
- `agent_commands.py`
- `agent_rag.py`

実施内容は以下とする。

- REPL 固有責務と orchestration 責務の切分け
- `AgentContext` から除去する state の確定
- 旧 direct tool loop / direct RAG path の削除対象確定
- file 単位 task と `patch_set` 単位 artifact の境界明文化
- `Integrator` と `Publisher` の責務境界明文化

完了条件は以下とする。

- responsibility map 完成
- remove / move 対象一覧完成
- role と内部コンポーネントの責務が文書で固定される

### 4.2 Phase 1. Orchestrator 骨格と `workflow.sqlite` 導入

対象は以下とする。

- `orchestrator.py`
- `workflow_engine.py`
- `task_scheduler.py`
- `retry_controller.py`
- `state_manager.py`
- `orchestrator_models.py`

実施内容は以下とする。

- workflow/task/artifact DTO 定義
- state machine 実装
- scheduler 骨格実装
- retry policy 骨格実装
- `workflow.sqlite` スキーマ作成
- `state_manager.py` 永続化 API 実装

完了条件は以下とする。

- workflow 作成、状態更新、task 登録、event 記録が単体動作する
- `workflow_id` で独立管理できる

### 4.3 Phase 2. REPL 層の縮退

対象は以下とする。

- `agent.py`
- `agent_repl.py`
- `agent_context.py`

実施内容は以下とする。

- `agent.py` を薄い entrypoint に変更
- `agent_repl.py` を UI adapter に変更
- `AgentContext` を conversation state のみに縮退
- REPL から direct workflow 実行ロジックを除去
- `Orchestrator` 呼出しに差替え

完了条件は以下とする。

- REPL が `Orchestrator` を呼んで workflow を起動できる
- `AgentContext` に workflow 状態が残らない

### 4.4 Phase 3. Retriever への RAG 分離

対象は以下とする。

- `agent_rag.py`
- `retriever_mcp_server.py`

実施内容は以下とする。

- RAG core service の抽出
- UI callback 依存除去
- MCP request/response 定義
- REPL 直結 RAG path の削除
- `Retriever` から evidence/context を返す経路追加

完了条件は以下とする。

- RAG 実行が `Retriever MCP Server` 経由で動作する
- `agent_repl.py` が RAG 実行を直接持たない

### 4.5 Phase 4. Planner 導入と workflow 展開

対象は以下とする。

- `planner_mcp_server.py`
- `orchestrator.py`
- `task_scheduler.py`

実施内容は以下とする。

- request から `change_set` への変換
- task graph 生成
- dependency 生成
- acceptance criteria 生成
- `change_set` から `file task` 展開ロジック実装

完了条件は以下とする。

- 1 request から `workflow_id` 配下に `file task` 群が作成される
- dependency を用いた ready / blocked 制御が動作する

### 4.6 Phase 5. PatchWorker 導入

対象は以下とする。

- `patch_worker_mcp_server.py`
- `orchestrator.py`
- `worker_runtime.py`
- `worker_launcher.py`
- `worktree_manager.py`

実施内容は以下とする。

- file 単位 patch 生成 API 実装
- diff 生成
- local / GitHub 対象編集案作成
- `file task` 入出力 schema 固定
- 複数 file task の並列実行経路実装
- worktree 作成、cleanup、artifact 収集実装

完了条件は以下とする。

- 1 file task ごとに patch/diff が生成される
- 複数 file task を並列実行できる
- worker ごとに worktree が分離される

### 4.7 Phase 6. Integrator 導入

対象は以下とする。

- `integrator_mcp_server.py`

実施内容は以下とする。

- file patch 群から `patch_set` へ統合
- 同一 workflow の file 変更を論理変更単位へ集約
- validation 用 artifact 生成
- integration summary 生成

完了条件は以下とする。

- `patch_set` が生成される
- validator 入力として一貫した artifact ができる
- `Integrator` が Git 操作を持たないことが保証される

### 4.8 Phase 7. Validator 導入

対象は以下とする。

- `validator_mcp_server.py`
- `retry_controller.py`

実施内容は以下とする。

- `patch_set` 全体に対する syntax/lint/unit test 実行
- result schema 固定
- deterministic failure と transient failure の分類
- retry policy との接続

完了条件は以下とする。

- validator 結果が workflow 状態へ反映される
- retry 対象と非対象が分離される

### 4.9 Phase 8. Repository / Policy / Approval / Audit 導入

対象は以下とする。

- `repository_gateway.py`
- `policy_engine.py`
- `approval_gate.py`
- `mcp_registry.py`
- `audit_logger.py`
- `orchestrator_barrier.py`

実施内容は以下とする。

- local / GitHub repository I/O 窓口統一
- branch/path/action 制約実装
- approval request / approval record 実装
- GitHub write から Draft PR 作成までを gate 対象化
- role MCP health / capability 監視追加
- approval / retry / write action の監査ログ記録追加
- barrier 制御実装

完了条件は以下とする。

- GitHub write 系操作が policy + approval を経由しないと進まない
- `/mcp` で role MCP 状態が確認できる
- 監査ログで publish 系操作を追跡できる

### 4.10 Phase 9. Publisher 導入

対象は以下とする。

- `publisher_mcp_server.py`
- `repository_gateway.py`

実施内容は以下とする。

- branch 作成
- commit 生成
- push
- Draft PR 作成
- final summary 生成
- approval 済み `patch_set` のみを publish 対象に制限

完了条件は以下とする。

- validation 済み `patch_set` について GitHub 公開経路が動作する
- approval 後のみ push / Draft PR が実行される
- `Publisher` が統合責務を持たないことが保証される

### 4.11 Phase 10. agent / MCP 統合

対象は以下とする。

- `config/agent.json`
- `tool_definitions`
- `scripts/orchestrator_mcp_server.py`
- `config/orchestrator_mcp_server.json`
- `init.d/orchestrator-mcp`
- `deploy/deploy.sh`
- `deploy/setup_services.sh`

実施内容は以下とする。

- `mcp_servers.orchestrator` を追加
- orchestrator 用 `tool_definitions` を追加
- `GET /health`、`GET /v1/tools`、`POST /v1/call_tool` を実装
- OpenRC サービス追加
- watchdog 連携
- deploy スクリプト更新

完了条件は以下とする。

- `orchestrator-mcp` が既存 MCP 群と同じ運用で起動・監視される
- `/mcp` に `orchestrator-mcp` が表示される
- `tool_definitions` と `/v1/tools` 整合が取れる

### 4.12 Phase 11. command 再設計と旧経路削除

対象は以下とする。

- `agent_commands.py`
- `agent_repl.py`
- 不要化した旧 logic

実施内容は以下とする。

- `/plan` を workflow 起動入口に変更
- `/mcp` を role MCP 可視化に変更
- `/stats` を workflow/task/retry/approval 表示に変更
- `/context` を conversation + workflow 表示に変更
- `/rag` を `Retriever` ドライラン呼出しに変更
- 旧 direct tool loop / direct RAG path / 旧 coordinator logic 削除

完了条件は以下とする。

- REPL が新構成前提で一貫動作する
- 旧内部 orchestration ロジックが削除される

## 5. Risks

### 5.1 REPL と Orchestrator の責務重複

リスクは以下である。

- `agent_repl.py` に orchestration が残る

対策は以下とする。

- REPL は UI と command のみに限定する
- workflow 実行責務は `orchestrator.py` に強制集約する

### 5.2 state の二重管理

リスクは以下である。

- `AgentContext` と `state_manager.py` の両方に workflow 状態が残る

対策は以下とする。

- `AgentContext` は conversation state のみとする
- workflow/task/artifact/retry/approval は `state_manager.py` のみで管理する

### 5.3 role MCP 分散によるレイテンシ上昇

リスクは以下である。

- MCP hop 増加で全体遅延が増える

対策は以下とする。

- dependency がない `file task` を並列化する
- retrieval 結果を再利用する
- validator 実行範囲を最適化する
- role 別 timeout を設計する

### 5.4 file 単位分割による一貫性崩れ

リスクは以下である。

- 複数 file をまたぐ変更で部分整合が崩れる

対策は以下とする。

- `Integrator` が `patch_set` 単位で統合する
- `Validator` は `patch_set` 全体を検証する
- approval も `patch_set` 単位に紐付ける

### 5.5 approval 前後で artifact が差し替わるリスク

リスクは以下である。

- 承認した内容と実際に push された内容が異なる

対策は以下とする。

- `patch_set hash` を approval record に保存する
- GitHub write は承認済み hash のみ実行許可する

### 5.6 repository 操作責務の拡散

リスクは以下である。

- `PatchWorker` と `Publisher` がそれぞれ独自に `github-mcp` / `file-mcp` を呼ぶ

対策は以下とする。

- `repository_gateway.py` 経由に統一する
- repository 操作ポリシーを `policy_engine.py` で中央判定する

### 5.7 retry 暴走

リスクは以下である。

- syntax/lint/unit test failure を不適切に再試行する

対策は以下とする。

- deterministic failure は retry を抑制する
- transient error のみ retry する
- role / error 種別ごとに `max_attempts` を設定する

### 5.8 `workflow.sqlite` の肥大化

リスクは以下である。

- diff / logs / evidence を DB inline 保存することで DB サイズが増大する

対策は以下とする。

- artifact のサイズ上限を設ける
- 列単位の圧縮や truncation 方針を定める
- 将来の外部 artifact store 分離余地を残す

### 5.9 `Integrator` と `Publisher` の境界混濁

リスクは以下である。

- `Integrator` に Git 操作が再流入する
- `Publisher` が patch 統合まで持ち始める

対策は以下とする。

- `Integrator` は `patch_set` 生成までに限定する
- `Publisher` は approval 後の公開に限定する
- `repository_gateway.py` の write API は `Publisher` からのみ使用可とする

### 5.10 approval 対象の逸脱

リスクは以下である。

- push や Draft PR 作成が approval を経ずに実行される

対策は以下とする。

- approval 対象を GitHub 書き込みから Draft PR 作成までに固定する
- `approval_gate.py` で対象 action を enum 化する
- `audit_logger.py` で必ず記録する

### 5.11 HTTP MCP 統合不整合

リスクは以下である。

- `tool_definitions` と `/v1/tools` の差分で起動時整合が崩れる
- watchdog / OpenRC 名不一致で障害時復旧に失敗する

対策は以下とする。

- `orchestrator-mcp` の `/v1/tools` と `config/agent.json` 定義を同時更新する
- `openrc_service` 名と init.d 名を厳密に一致させる
- Phase 10 で deploy と agent 設定を同時反映する
