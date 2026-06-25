# 中央オーケストレーター型協調基盤 統合仕様書

## 1. 目的

### 1.1 目的

本仕様の目的は、LLM を利用した複数エージェントによる協調開発基盤を構築し、そのための中央オーケストレーター型アーキテクチャを定義することである。
対象基盤は、中央オーケストレーター方式、MCP(Model Context Protocol) ベース、複数ホスト分散、Event Bus による非同期連携、Git による成果物共有、CPU 環境前提の軽量設計を特徴とする。

本仕様では、Orchestrator による全体制御の確立、Worker Agent の責務単純化、Event Bus による永続通知と監査ログの実現、Git による成果物共有の一貫性確保を目的とする。

## 2. 適用範囲

本仕様の適用範囲は以下の通り。

- Orchestrator 本体
- Orchestrator の外部インタフェースである Orchestrator MCP
- Worker Agent 群
- Event Bus
- Metadata DB
- Shared Git Repo と Git LFS
- MCP による Agent 呼び出し
- Shell MCP / Git MCP / File MCP / EventBus MCP を含む補助 MCP 群

## 3. 前提条件

本仕様の前提条件は以下の通り。

- OS は Linux。
- 実装言語は Python 前提。
- 通信は HTTP 前提。
- 配布構成は複数ホスト分散構成。
- イベント永続化が必須、再送と Replay が必須。
- Event Bus は自作実装前提。
- 成果物共有は Git とする。
- Worker Agent は MCP Server として実装。
- shell 実行を許可する前提。
- 遅延対策およびスループット最適化は要件外。

## 4. 全体アーキテクチャ

### 4.1 構成概要

本基盤は中央集権制御を採用し、Orchestrator がワークフロー全体の意思決定と実行制御を担当。

Orchestrator は外部インタフェースとして Orchestrator MCP を持ち、その内部に Goal Manager、Workflow Manager または Workflow Engine、Scheduler または Task Scheduler、Retry Controller、State Manager、Agent Registry、Event Manager、GitOps を持つ。

Worker は役割別に分離し、Planner、Retriever、Patch Worker、Validator、Integrator を主要 Worker とする。

Event Bus は軽量通知専用であり、永続化、再送、Replay、監査ログ、および UI 更新のためのイベント配信を提供する。エージェント間の直接通信は排除し、Event Bus を中心に疎結合・非同期連携を実現する。これにより、リトライ容易性、ログ永続化、障害局所化、非同期化を実現する。

成果物共有は Shared Git Repo を正とし、Event Bus には実体を流さず参照情報のみを流す。Metadata DB はタスク状態と冪等性管理の正であり、Orchestrator 再起動時の復元根拠となる。

### 4.2 論理構成

論理構成は以下の通り。

- Shared Git Repo
  - ソース
  - パッチ
  - レポート
  - LFS ポインタ
- Orchestrator 本体
  - Workflow Engine
  - Task Scheduler
  - Agent Registry
  - Event Manager
  - Retry Controller
  - State Manager
  - GitOps
- Orchestrator MCP
  - Goal 管理 API
  - Workflow 開始 API
  - Task 作成 API
- Event Bus
  - publish API
  - consume API
  - subscribe API
  - replication API
  - append-only log(JSONL / NDJSON)
  - SQLite index
  - Subscription Manager
  - Ack Manager
- Metadata DB
  - task 状態
  - attempt
  - processed event_id
  - 成果物参照
- Worker Agent 群
  - Planner MCP
  - Retriever MCP
  - Patch Worker MCP
  - Validator MCP
  - Integrator MCP
- 補助 MCP 群
  - Shell MCP
  - Git MCP
  - File MCP
  - EventBus MCP

リポジトリ構成の代表例は以下の通り。

```text
multi-agent-system/
├── orchestrator/
├── event-bus/
├── planner-mcp/
├── retriever-mcp/
├── patch-worker/
├── validator/
├── integrator/
├── shared/
│   ├── schemas/
│   ├── utils/
│   └── protocols/
├── scripts/
├── logs/
└── repositories/
```

## 5. 役割と責務

### 5.1 MCPサーバ一覧

本仕様で採用する MCP サーバ一覧は以下の 10 種とする。

1. **Orchestrator MCP**
   - ゴール管理
   - ワークフロー管理
   - タスク投入
   - エージェント割当
   - リトライ
   - 状態管理
   - 最終承認
   - API
     - `POST /workflow/start`
     - `POST /task/create`

2. **Planner MCP**
   - タスク分解
   - 依存関係生成
   - 作業単位定義
   - 完了条件定義

3. **Retriever MCP**
   - RAG 検索
   - 関連コード抽出
   - 関連履歴検索
   - 根拠収集
   - 使用技術
     - 全文検索: ripgrep
     - ベクトル検索: sqlite-vss
     - キャッシュ: sqlite

4. **Patch Worker MCP**
   - FIM(Fill In the Middle) 編集
   - 差分生成
   - 局所変更
   - 特徴
     - 1ファイル限定
     - 小規模編集
     - token 削減

5. **Validator MCP**
   - lint
   - 型チェック
   - test
   - 実行確認

6. **Integrator MCP**
   - patch 統合
   - conflict 解決
   - 最終成果物生成
   - レポート作成

7. **Shell MCP**
   - shell 実行

8. **Git MCP**
   - Git 操作

9. **File MCP**
   - ファイル操作

10. **EventBus MCP**
    - Event Bus API

### 5.2 Event Bus

Event Bus は Orchestrator と Worker 間の通知経路を提供し、永続化、再送、Replay、監査ログ、UI 更新のためのイベント配信を担う。初期実装では Pull 型 polling により Agent が consume し、将来拡張として SSE による subscribe を提供する。

### 5.3 Git と Git LFS

Git と Git LFS は成果物共有の正である。Event Bus には実体を流さず、commit sha、branch、path、PR URL、LFS 対象パスなどの参照情報のみを流す。Patch Worker は Git commit を作成し、Validator はその commit を checkout して検証し、Integrator が統合を行う。Patch Worker 側では branch 分離と force push 禁止を行う。危険操作である `git push`、`git merge`、main ブランチ直接更新、保護ブランチ例外操作は Orchestrator が統制する。

### 5.4 Metadata DB

Metadata DB はタスク状態、attempt、processed event_id、成果物参照、冪等性情報を保持する状態管理 DB である。状態の正および冪等性の正として機能し、Orchestrator 再起動時の復元根拠となる。Task 状態は `PENDING`、`RUNNING`、`FAILED`、`COMPLETED` を持つ。task ごとに `timeout_sec` を設定し、timeout 到達時は `FAILED` 扱いとして retry ポリシーへ遷移する。`max_attempts` 超過時は `FAILED` 確定とし、恒久障害は即時 `FAILED` として DLQ 登録する。

### 5.5 シーケンス図

#### 5.5.1 基本フロー

基本フローは以下の通り。

```text
User
  │
  ▼
Orchestrator
  │  workflow.started
  ▼
Event Bus
  │
  ▼
Planner
  │  task.created
  ▼
Event Bus
  │
  ▼
Patch Worker
  │  patch.completed / patch.generated
  ▼
Event Bus
  │
  ▼
Validator
  │  validation.success / validation.completed
  ▼
Event Bus
  │
  ▼
Integrator
  │  integration.completed
  ▼
Orchestrator
```

## 6. ワークフロー仕様

### 6.1 標準フロー

開発系の標準フローは `Retriever → PatchWorker → Validator → Integrator` とする。Planner はゴールからタスク群と依存関係を生成し、Orchestrator がその依存関係を解決して各 Worker に割り当てる。Orchestrator は Workflow 制御、依存関係解決、実行順序決定、完了判定、Task Scheduling、同時実行数制御、Retry 制御、Timeout 管理、ハング検出、中断と再実行、状態管理、成果物参照の確定、危険操作ガード、監査イベント出力を担当する。

### 6.2 Workflow 定義形式

Workflow 定義は YAML ベースとする。例として `workflows/default.yaml` は以下の通り。

```yaml
workflow:
  - id: retrieve
    agent: retriever
    timeout_sec: 300
    retry:
      max_attempts: 2

  - id: patch
    agent: patch-worker
    depends_on: [retrieve]
    timeout_sec: 900
    retry:
      max_attempts: 2

  - id: validate
    agent: validator
    depends_on: [patch]
    timeout_sec: 900
    retry:
      max_attempts: 1

  - id: integrate
    agent: integrator
    depends_on: [validate]
    timeout_sec: 600
    retry:
      max_attempts: 1
```

## 7. Event Bus 仕様

### 7.1 位置付け

Event Bus は軽量通知専用とし、ルーティングや依存解決は Orchestrator が担当する。永続ログを正として Replay を提供する。設計方針は高性能よりも単純性、可読性、障害解析容易性を優先する。

### 7.2 ノード構成

各ホストに `eventbus-node` を配置する。publish と consume/subscribe はローカル node を優先し、replication は node 間で実施する。例として Host A に orchestrator + eventbus-node、Host B に patch-worker + eventbus-node を配置する。物理構成例として `event-bus/app.py`、`storage/events.jsonl`、`storage/offsets/`、`storage/deadletter/` を持つ。

### 7.3 通信方式

初期実装では Pull 型を採用し、Agent は polling によりイベントを取得する。理由は実装容易、OpenRC 環境適合、WebSocket 不要、メモリ削減である。
API は `POST /publish`、`GET /consume?consumer=...&topic=...`、`POST /ack` を持つ。
将来拡張では `publish: HTTP POST`、`subscribe: SSE`、`replication: HTTP` を採用する。
`GET /subscribe?topic=...&since_seq=...` により Replay 起点を指定し、replication は `GET /replicate?since_seq=...` または `POST /replicate/push` を用いる。

#### 7.3.1 図式化: Pull 初期実装 / SSE 将来拡張

```text
[初期実装: Pull / Polling]

Worker Agent
   │
   │ GET /consume?consumer=<id>&topic=<pattern>
   ▼
Event Bus Node
   │
   │ read from JSONL + SQLite index
   ▼
Event Store
   │
   │ POST /ack
   ▼
Ack Manager / Offset Store
```

```text
[将来拡張: SSE]

Worker Agent
   │
   │ GET /subscribe?topic=<pattern>&since_seq=<n>
   ▼
Event Bus Node
   │
   │ stream events via SSE
   ▼
Worker Agent

Replication:
Event Bus Node A  <--HTTP pull/push-->  Event Bus Node B
```

### 7.4 Topic 設計

初期設計の Topic 一覧は以下の通り。

- `workflow.started`
- `task.created`
- `task.assigned`
- `patch.completed`
- `validation.failed`
- `validation.success`
- `integration.completed`

協調基盤仕様の Topic 設計は以下の通り。

- `orch.command`
- `orch.status`
- `artifact.notice`
- `audit.log`
- `dlq.any`

`orch.command` は Orchestrator から Worker、`orch.status` は Worker から Orchestrator、`artifact.notice` は Worker から Orchestrator および UI、`audit.log` は監査ログ、`dlq.any` は処理不能隔離を表す。

### 7.5 event_type 設計

event_type は以下を定義する。

- `task.dispatch`
- `task.started`
- `task.progress`
- `task.completed`
- `task.failed`
- `patch.generated`
- `validation.completed`
- `integration.completed`
- `artifact.updated`
- `audit.guard.executed`

初期設計の `patch.completed`、`validation.success` / `validation.failed`、`integration.completed` は上記 event_type に対応づける。

### 7.6 event envelope

event envelope は `schemas/event_envelope.json` に定義する。フィールドは以下の通り。

```json
{
  "event_id": "ulid-or-uuid",
  "event_type": "namespace.action",
  "event_version": 1,
  "occurred_at": "rfc3339",
  "producer": "orchestrator-or-worker-id",
  "correlation_id": "workflow-id",
  "causation_id": "previous-event-id",
  "key": "ordering-key",
  "payload": {}
}
```

各フィールドの意味は以下の通り。

- `event_id`: 冪等性キー
- `correlation_id`: ワークフロー単位追跡
- `causation_id`: 因果関係復元
- `key`: 最小順序制御。task 単位推奨

初期設計のイベント形式は `event_id`、`topic`、`source`、`timestamp`、`payload` を持つ。統合後は event envelope の簡易表現として包含する。

永続化は JSONL を物理ログとして 1 イベント 1 行で保存し、例として `events/2026-05-21.log` のような NDJSON ローテーションを行う。
SQLite は参照・Replay 用インデックスとして `events` テーブルを持ち、`seq INTEGER PRIMARY KEY AUTOINCREMENT`、`event_id TEXT UNIQUE`、`topic TEXT NOT NULL`、`event_type TEXT NOT NULL`、`key TEXT`、`payload_json TEXT NOT NULL`、`created_at TEXT NOT NULL` を保持し、`topic/seq`、`event_type/seq`、`key/seq` の index を持つ。

Replay は subscriber が `since_seq` を保持し、再接続時に `since_seq + 1` から再開する。
Orchestrator は Metadata DB と突合して未処理補完を行う。
再送と冪等性は at least once 配信を前提とし、消費側で `event_id` による重複排除を行う。
command は `task_id` と `attempt` を持つ方針とする。
DLQ は `dlq.any` を用い、リトライ上限超過や恒久障害を隔離する。
記録項目は元イベント、例外情報、retry 回数、隔離理由とする。
Retry は指数バックオフを採用し、例として 1s、2s、4s、8s を用いる。
Worker 障害時は timeout 検知、task 再投入、stale task cleanup を行う。

## 8. MCP 連携仕様

### 8.1 呼び出しモデル

呼び出しモデルは `Orchestrator → MCP → Worker` とする。
Worker Agent は MCP Server として実装され、Orchestrator は Orchestrator MCP を外部インタフェースとして持つ。
エージェント間プロトコルは HTTP + JSON を採用する。

### 8.2 MCP payload 方針

command イベントの `payload` に MCP JSON を内包する。MCP JSON は `method` と `params` を持つ。代表例は以下の通り。

```json
{
  "mcp": {
    "method": "task.request",
    "params": {
      "task_id": "123",
      "role": "patch-worker",
      "repo": "org/project",
      "branch": "work/task-123",
      "targets": ["src/app.py", "tests/test_app.py"],
      "constraints": {
        "dangerous_git_ops": "guarded",
        "binary_assets": "git_lfs"
      }
    }
  }
}
```

Orchestrator MCP の API は以下の通り。

- `POST /workflow/start`
  - request

```json
{
  "goal": "README を改善",
  "repository": "/repo/project"
}
```

- `POST /task/create`
  - request

```json
{
  "type": "patch",
  "target": "src/app.py"
}
```

Planner MCP の入出力例は以下の通り。

```json
{
  "goal": "認証機能追加"
}
```

```json
{
  "tasks": [
    {
      "id": "task-1",
      "type": "patch",
      "target": "auth.py"
    }
  ]
}
```

Patch Worker MCP の入出力例は以下の通り。

```json
{
  "file": "src/app.py",
  "instruction": "logger追加"
}
```

```diff
+ import logging
```

## 9. 成果物共有と Artifact Flow

### 9.1 原則

成果物の実体は Git と Git LFS に置く。
Event Bus は参照情報のみを流す。
Event Bus には commit sha、branch、path、PR URL、LFS 対象パスなどの参照情報を流す。
Patch Worker 側では branch 分離と force push 禁止前提。
危険操作である `git push`、`git merge`、main ブランチ直接更新、保護ブランチ例外操作は Orchestrator が統制し、実行結果は `audit.guard.executed` として監査イベントに残す。

### 9.2 標準フロー

成果物共有と Artifact Flow の標準フローは以下の通り。

1. PatchWorker は作業ブランチ上で patch を生成し、Git commit を作成する。Git LFS 対象があれば追加または更新する。
2. Worker は `artifact.updated` または `artifact.notice` 相当イベントで成果物参照を通知する。通知内容は `repo`、`branch`、`commit`、`paths`、`lfs.enabled`、`lfs.paths`、`pr.url` を含む。
3. Validator は対象 commit を checkout し、lint、型チェック、test、実行確認を行う。実行例として `ruff check .`、`mypy .`、`pytest` を用いる。
4. Integrator は検証済み成果物を統合し、必要に応じて conflict 解決、最終成果物生成、レポート作成を行う。
5. push、PR 作成、merge は Worker ではなく Orchestrator が実行する。実行時は対象 repo、branch、commit、実行者、実行時刻を監査イベントへ保存する。
6. Host 障害時は Git と Git LFS を正として復旧し、Event Log の replication、Metadata DB の未完了タスク復元、Event Replay により未処理補完を行う。

artifact.updated の例は以下の通り。

```json
{
  "repo": "org/project",
  "branch": "work/task-123",
  "commit": "abc1234",
  "paths": ["docs/design.md", "assets/diagram.png"],
  "lfs": {
    "enabled": true,
    "paths": ["assets/diagram.png"]
  },
  "pr": {
    "url": "https://github.com/org/project/pull/456"
  }
}
```

## 10. 運用・障害回復・実装方針

### 10.1 障害回復

Agent 障害時は Orchestrator により retry を実施し、attempt を記録する。
ブランチ命名規約により二重実行の衝突を低減する。
Event Bus 障害時は append-only log と SQLite index から Replay を行い、replication によって欠損を補完する。
subscriber は `since_seq` により再開する。
Host 障害時は Git と Git LFS を正として復旧し、Orchestrator 再起動時には Metadata DB から未完了タスクを復元し、Event Replay で未処理補完を行い、Git 参照と整合させる。

### 10.2 SPOF 対策

Orchestrator のアクティブスタンバイを想定する。
自動選出は要件外とし、手動切替でも成立すること前提。
必須運用として Metadata DB バックアップおよび Orchestrator 起動時リカバリ手順を整備する。

### 10.3 OpenRC サービス設計

OpenRC サービス例は以下の通り。起動順は `event-bus → orchestrator → agents` とする。

```text
/etc/init.d/
├── orchestrator
├── event-bus
├── planner
├── retriever
├── validator
```

### 10.4 推奨ライブラリ

推奨ライブラリは以下の通り。

- HTTP: FastAPI
- 非同期: asyncio
- DB: sqlite3
- JSON: orjson
- shell: subprocess
- Git: GitPython

### 10.5 性能方針

CPU 節約方針は、polling 間隔長め、並列数制限、小さい context、patch 単位分割とする。
メモリ節約方針は、model 共有、process 数最小化、sqlite 利用、queue 非メモリ化とする。
重視項目は単純性、障害解析容易性、CPU 省電力、永続化、ローカル完結、OpenRC 適合とする。

### 10.6 推奨実装順

推奨実装順は以下の通り。

1. Event Bus
2. Orchestrator
3. Planner
4. Patch Worker
5. Validator
6. Integrator
7. 分散化

### 10.7 未確定事項

未確定事項は以下の通り。

- Orchestrator 冗長化方式。手動切替か自動切替か
- Event Bus replication トポロジ。全結合、スター、リングなど
- Metadata DB 配置。Orchestrator ローカル SQLite か共有 DB か
- GitHub token の保管と権限設計
