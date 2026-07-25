## 中央オーケストレーター型協調基盤 統合仕様書

### 1. 目的

#### 1.1 目的

本仕様の目的は、LLM を利用した複数エージェントによる協調開発基盤を構築し、そのための中央オーケストレーター型アーキテクチャを定義することである。
対象基盤は、中央オーケストレーター方式、複数ホスト分散、Event Bus による非同期連携、Git による成果物共有、CPU 環境前提の軽量設計を特徴とする。
本仕様では、Orchestrator による全体制御の確立、Worker Agent の責務単純化、Event Bus による永続通知と監査ログの実現、Git による成果物共有の一貫性確保を目的とする。

### 2. 適用範囲

本仕様の適用範囲は以下の通り。
- Agent にビルトインされた Orchestrator 本体
- Worker Agent 群
- Agent にビルトインされた Event Bus
- Metadata DB
- Shared Git Repo と Git LFS
- Agent 内部の HTTP / JSON ベース呼び出し

### 3. 前提条件

本仕様の前提条件は以下の通り。
- OS は Linux。
- 実装言語は Python 前提。
- 通信は HTTP 前提。
- 配布構成は複数ホスト分散構成。
- イベント永続化が必須、再送と Replay が必須。
- Event Bus は Agent 機能としてすでに存在している前提とする。
- 成果物共有は Git とする。
- Worker Agent は独立した Agent Runtime または内部実行単位として実装。
- shell 実行を許可する前提。
- 遅延対策およびスループット最適化は要件外。

### 4. 全体アーキテクチャ

#### 4.1 構成概要

本基盤は中央集権制御を採用し、Orchestrator がワークフロー全体の意思決定と実行制御を担当する。
Orchestrator は Agent のビルトイン機能として実装し、その内部に Goal Manager、Workflow Manager または Workflow Engine、Scheduler または Task Scheduler、Retry Controller、State Manager、Agent Registry、Event Manager、GitOps を持つ。
Worker は役割別に分離し、Planner、Retriever、Patch Worker、Validator、Integrator を主要 Worker とする。
Event Bus は Agent のビルトイン機能として存在し、永続化、再送、Replay、監査ログ、および UI 更新のためのイベント配信を提供する。エージェント間の直接通信は排除し、Event Bus を中心に疎結合・非同期連携を実現する。これにより、リトライ容易性、ログ永続化、障害局所化、非同期化を実現する。
成果物共有は Shared Git Repo を正とし、Event Bus には実体を流さず参照情報のみを流す。Metadata DB はタスク状態と冪等性管理の正であり、Orchestrator 再起動時の復元根拠となる。

#### 4.2 論理構成

論理構成は以下の通り。
- Shared Git Repo
- ソース
- パッチ
- レポート
- LFS ポインタ
- Agent 本体
- Orchestrator
- Workflow Engine
- Task Scheduler
- Agent Registry
- Event Manager
- Retry Controller
- State Manager
- GitOps
- Event Bus
- publish API
- replay API
- subscribe API
- health API
- dlq API
- append-only log(JSONL / NDJSON)
- SQLite index
- Offset Store
- DLQ Manager
- Metadata DB
- task 状態
- attempt
- processed event_id
- 成果物参照
- Worker Agent 群
- Planner
- Retriever
- Patch Worker
- Validator
- Integrator

リポジトリ構成の代表例は以下の通り。multi-agent-system/
├── agent/
│   ├── orchestrator/
│   ├── eventbus/
│   └── workers/
├── shared/
│   ├── schemas/
│   ├── utils/
│   └── protocols/
├── scripts/
├── logs/
└── repositories/

### 5. 役割と責務

#### 5.1 主要コンポーネント一覧

本仕様で採用する主要コンポーネント一覧は以下の通り。
- **Orchestrator**
  - ゴール管理
  - ワークフロー管理
  - タスク投入
  - エージェント割当
  - リトライ
  - 状態管理
  - 最終承認
  - API
  - POST /workflow/start
  - POST /task/create
- **Planner**
  - タスク分解
  - 依存関係生成
  - 作業単位定義
  - 完了条件定義
- **Retriever**
  - RAG 検索
  - 関連コード抽出
  - 関連履歴検索
  - 根拠収集
  - 使用技術
  - 全文検索: ripgrep
  - ベクトル検索: sqlite-vss
  - キャッシュ: sqlite
- **Patch Worker**
  - FIM(Fill In the Middle) 編集
  - 差分生成
  - 局所変更
  - 特徴
  - 1ファイル限定
  - 小規模編集
  - token 削減
- **Validator**
  - lint
  - 型チェック
  - test
  - 実行確認
- **Integrator**
  - patch 統合
  - conflict 解決
  - 最終成果物生成
  - レポート作成
- **Event Bus**
  - Event Bus API
  - 永続ログ
  - Replay
  - Subscribe
  - DLQ
  - Offset 管理

#### 5.2 Event Bus

Event Bus は Orchestrator と Worker 間の通知経路を提供し、永続化、再送、Replay、監査ログ、UI 更新のためのイベント配信を担う。Event Bus は Agent のビルトイン機能としてすでに存在し、内部 publish/subscribe backbone として JSON イベントを処理する。Producer は JSON Event を publish し、Consumer は topic 単位の SSE subscribe および replay によって過去イベントと新規イベントを取得する。
セキュリティモデルは認証や ACL を持たず、単一ノードまたは trusted host 前提でネットワーク境界により保護する。インターネットへ直接公開してはならない。
初期実装では `/publish`、`/replay`、`/subscribe`、`/health`、`/dlq`、`/dlq/{event_id}/requeue` を持つ内部 HTTP API を提供する。

#### 5.3 Git と Git LFS

Git と Git LFS は成果物共有の正である。Event Bus には実体を流さず、commit sha、branch、path、PR URL、LFS 対象パスなどの参照情報のみを流す。Patch Worker は Git commit を作成し、Validator はその commit を checkout して検証し、Integrator が統合を行う。Patch Worker 側では branch 分離と force push 禁止を行う。危険操作である git push、git merge、main ブランチ直接更新、保護ブランチ例外操作は Orchestrator が統制する。

#### 5.4 Metadata DB

Metadata DB はタスク状態、attempt、processed event_id、成果物参照、冪等性情報を保持する状態管理 DB である。状態の正および冪等性の正として機能し、Orchestrator 再起動時の復元根拠となる。Task 状態は PENDING、RUNNING、FAILED、COMPLETED を持つ。task ごとに timeout_sec を設定し、timeout 到達時は FAILED 扱いとして retry ポリシーへ遷移する。max_attempts 超過時は FAILED 確定とし、恒久障害は即時 FAILED として DLQ 登録する。

#### 5.5 シーケンス図

##### 5.5.1 基本フロー

基本フローは以下の通り。User
  │
  ▼
Agent
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

### 6. ワークフロー仕様

#### 6.1 標準フロー

開発系の標準フローは Retriever → PatchWorker → Validator → Integrator とする。Planner はゴールからタスク群と依存関係を生成し、Orchestrator がその依存関係を解決して各 Worker に割り当てる。Orchestrator は Workflow 制御、依存関係解決、実行順序決定、完了判定、Task Scheduling、同時実行数制御、Retry 制御、Timeout 管理、ハング検出、中断と再実行、状態管理、成果物参照の確定、危険操作ガード、監査イベント出力を担当する。

#### 6.2 Workflow 定義形式

Workflow 定義は YAML ベースとする。例として workflows/default.yaml は以下の通り。workflow:
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

### 7. Event Bus 仕様

#### 7.1 位置付け

Event Bus は軽量通知専用とし、ルーティングや依存解決は Orchestrator が担当する。永続ログを正として Replay を提供する。設計方針は高性能よりも単純性、可読性、障害解析容易性を優先する。SQLite を authoritative store とし、JSONL archive は補助的な append-only log として扱う。

#### 7.2 ノード構成

各ホストに Event Bus runtime を配置する。publish と consume/subscribe はローカル runtime を優先する。現行実装は単一ノード / trusted host 前提の internal backbone であり、API には認証や ACL を持たない。DB は SQLite、永続ログは `{storage_dir}/events.jsonl`、offset は `{offsets_dir}`、DLQ は `{deadletter_dir}` を用いる。複数ホスト分散時の replication は将来拡張とする。

#### 7.3 通信方式

現行実装では `POST /publish` により JSON Event を publish し、`GET /replay` により seq ベースの Replay を行い、`GET /subscribe` により topic 単位の SSE subscribe を提供する。`GET /health` は DB と DLQ task の健全性を返し、`GET /dlq` と `POST /dlq/{event_id}/requeue` は DLQ 管理を行う。
subscribe は DB を poll_interval_ms ごとに監視して SSE を流す。consumer_id が指定される場合は offset ファイルを用いて再開位置を復元する。

##### 7.3.1 図式化: 現行実装
[現行実装: Publish / Replay / SSE Subscribe]
Producer / Orchestrator / Worker
   │
   │ POST /publish
   ▼
Event Bus Runtime
   │
   │ write to SQLite (+ JSONL archive)
   ▼
Event Store
   │
   │ GET /replay?since_seq=N
   │ GET /subscribe?topic=<pattern>&since_seq=<n>&consumer_id=<id>
   ▼
Consumer / Worker / UI

#### 7.4 Topic 設計

初期設計の Topic 一覧は以下の通り。
- workflow.started
- task.created
- task.assigned
- patch.completed
- validation.failed
- validation.success
- integration.completed
協調基盤仕様の Topic 設計は以下の通り。
- orch.command
- orch.status
- artifact.notice
- audit.log
- dlq.any
orch.command は Orchestrator から Worker、orch.status は Worker から Orchestrator、artifact.notice は Worker から Orchestrator および UI、audit.log は監査ログ、dlq.any は処理不能隔離を表す。

#### 7.5 event_type 設計

event_type は以下を定義する。
- task.dispatch
- task.started
- task.progress
- task.completed
- task.failed
- patch.generated
- validation.completed
- integration.completed
- artifact.updated
- audit.guard.executed
初期設計の patch.completed、validation.success / validation.failed、integration.completed は上記 event_type に対応づける。

#### 7.6 event envelope

event envelope は schemas/event_envelope.json に定義する。現行 Event Bus 実装では、最低限以下のフィールドを受け付ける。{
  "event_id": "uuid-string",
  "topic": "topic.name",
  "payload": {},
  "producer": "producer-name",
  "published_at": "rfc3339"
}
SQLite 上では events テーブルに `seq`、`event_id`、`topic`、`payload`、`producer`、`published_at`、`acked_at`、`retry_count`、`dlq_at` を保持する。`event_id` は UNIQUE であり、duplicate publish は silently ignored とする。
JSONL archive は `{storage_dir}/events.jsonl` に 1 event 1 行で補助保存する。JSONL append 失敗時でも SQLite commit に成功していれば publish は成功扱いとする。
Replay は `GET /replay?since_seq=N` により `seq > N` のイベントを昇順で返す。subscribe は consumer_id ごとの offset file と中間 checkpoint によって、再接続後の replay 起点を復元する。
再送と冪等性は at least once 配信を前提とし、消費側で event_id による重複排除を行う。
DLQ は `retry_count >= max_retry` かつ `dlq_at IS NULL` のイベントを 60 秒周期のバックグラウンド loop で昇格する。requeue は `dlq_at` を clear し `retry_count` を 1 増やすが、0 に戻さない。

### 8. MCP 連携仕様

#### 8.1 呼び出しモデル

呼び出しモデルは Agent → Orchestrator → Worker とする。Orchestrator と Event Bus は Agent のビルトイン機能であり、外部 MCP サーバではない。Worker Agent は独立 Runtime または内部実行単位として実装され、エージェント間プロトコルは HTTP + JSON を採用する。

#### 8.2 payload 方針

command event の payload に task request JSON を内包する。代表例は以下の通り。{
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
Orchestrator の API は以下の通り。
- POST /workflow/start
- request{
  "goal": "README を改善",
  "repository": "/repo/project"
}
- POST /task/create
- request{
  "type": "patch",
  "target": "src/app.py"
}
Planner の入出力例は以下の通り。{
  "goal": "認証機能追加"
}
{
  "tasks": [
    {
      "id": "task-1",
      "type": "patch",
      "target": "auth.py"
    }
  ]
}
Patch Worker の入出力例は以下の通り。{
  "file": "src/app.py",
  "instruction": "logger追加"
}
+ import logging

### 9. 成果物共有と Artifact Flow

#### 9.1 原則

成果物の実体は Git と Git LFS に置く。
Event Bus は参照情報のみを流す。
Event Bus には commit sha、branch、path、PR URL、LFS 対象パスなどの参照情報を流す。
Patch Worker 側では branch 分離と force push 禁止前提。
危険操作である git push、git merge、main ブランチ直接更新、保護ブランチ例外操作は Orchestrator が統制し、実行結果は audit.guard.executed として監査イベントに残す。

#### 9.2 標準フロー

成果物共有と Artifact Flow の標準フローは以下の通り。
- PatchWorker は作業ブランチ上で patch を生成し、Git commit を作成する。Git LFS 対象があれば追加または更新する。
- Worker は artifact.updated または artifact.notice 相当イベントで成果物参照を通知する。通知内容は repo、branch、commit、paths、lfs.enabled、lfs.paths、pr.url を含む。
- Validator は対象 commit を checkout し、lint、型チェック、test、実行確認を行う。実行例として ruff check .、mypy .、pytest を用いる。
- Integrator は検証済み成果物を統合し、必要に応じて conflict 解決、最終成果物生成、レポート作成を行う。
- push、PR 作成、merge は Worker ではなく Orchestrator が実行する。実行時は対象 repo、branch、commit、実行者、実行時刻を監査イベントへ保存する。
- Host 障害時は Git と Git LFS を正として復旧し、Event Log の replay、Metadata DB の未完了タスク復元により未処理補完を行う。
artifact.updated の例は以下の通り。{
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

### 10. 運用・障害回復・実装方針

#### 10.1 障害回復

Agent 障害時は Orchestrator により retry を実施し、attempt を記録する。
ブランチ命名規約により二重実行の衝突を低減する。
Event Bus 障害時は SQLite authoritative store と JSONL archive を用いて Replay を行う。subscriber は since_seq と consumer offset により再開する。
Host 障害時は Git と Git LFS を正として復旧し、Orchestrator 再起動時には Metadata DB から未完了タスクを復元し、Event Replay で未処理補完を行い、Git 参照と整合させる。

#### 10.2 SPOF 対策

Orchestrator のアクティブスタンバイを想定する。
自動選出は要件外とし、手動切替でも成立すること前提。
必須運用として Metadata DB バックアップおよび Orchestrator 起動時リカバリ手順を整備する。

#### 10.3 OpenRC サービス設計

OpenRC サービス例は以下の通り。起動順は agent -> workers とする。/etc/init.d/
├── agent
├── planner
├── retriever
├── validator

#### 10.4 推奨ライブラリ

推奨ライブラリは以下の通り。
- HTTP: FastAPI
- 非同期: asyncio
- DB: sqlite3
- JSON: orjson
- shell: subprocess
- Git: GitPython

#### 10.5 性能方針

CPU 節約方針は、polling 間隔長め、並列数制限、小さい context、patch 単位分割とする。
メモリ節約方針は、model 共有、process 数最小化、sqlite 利用、queue 非メモリ化とする。
重視項目は単純性、障害解析容易性、CPU 省電力、永続化、ローカル完結、OpenRC 適合とする。

#### 10.6 推奨実装順

推奨実装順は以下の通り。
- Orchestrator
- Planner
- Patch Worker
- Validator
- Integrator
- 分散化

#### 10.7 未確定事項

未確定事項は以下の通り。
- Orchestrator 冗長化方式。手動切替か自動切替か
- 複数ホスト分散時の Event Bus replication トポロジ。全結合、スター、リングなど
- Metadata DB 配置。Orchestrator ローカル SQLite か共有 DB か
- GitHub token の保管と権限設計
