# ローカルLLMエージェントに追加すべき機能提案

## 1. 自己改善ループ（Self-Improving Loop）

### 1.1 機能概要

エージェント実行後に、会話、ツール実行、差分、失敗要因、ユーザー修正指示を自動収集し、次回以降の Skill、Rules、Prompt に反映する機能である。
単発の会話改善ではなく、実行後に改善材料を蓄積し、別セッションで再学習させる「事後学習ループ」の実装である。
また、エージェント自身が実行ログ・失敗履歴・成功パターンを分析し、SKILL.md / RULES.md / Prompt を自動更新する構成も含む。

### 1.2 効果

- 同じ失敗、同じ修正指示の再発防止
- Prompt や Skill の劣化検知
- 手動レビューの知見を半自動で形式知化
- 長期運用時の品質上振れ。特にチーム固有ルールへの追随性向上
- リファクタリング品質の継続改善
- プロジェクト固有知識の蓄積
- 人間レビュー工数削減
- 特に長期開発で効果が大きい

### 1.3 実現方式

#### 1.3.1 推奨アーキテクチャ

```text
Task Execution
  ↓
Execution Log
  ↓
Failure Analyzer
  ↓
Improvement Proposal Generator
  ↓
Human Approval(Optional)
  ↓
Skill/Rule Auto Update
```

#### 1.3.2 ログ収集対象

実行後 Hook を設け、以下を JSONL と SQLite に保存する。

- user prompt
- model output
- tool call
- git diff
- error log
- user correction
- ビルド失敗原因
- テスト失敗原因
- 修正時間
- 成功した修正パターン
- 頻出コマンド

#### 1.3.3 分析レイヤ

収集データは以下 3 層に分離する。

- deterministic facts
- context-extracted facts
- inferred hypotheses

#### 1.3.4 改善バッチ

別ジョブで nightly 改善バッチを実行する。

- 頻出失敗の抽出
- Skill 改善提案の生成
- Rules 差分の提案
- 改善候補の human approval 付き適用

#### 1.3.5 実装候補

- SQLite / DuckDB にログ保存
- Git hook で変更履歴管理
- Reflection Prompt
- 評価用サブエージェント
- Cron / Routines / タイマージョブによる定期改善
- ローカル環境での自動テスト実行
- テスト通過時のみ本体設定へ反映

#### 1.3.6 オーケストレーター統合時の拡張

オーケストレーター配下では、各 Worker ごとの成功率と失敗パターンも集約対象とする。

### 1.4 留意点

エージェントが自律的にルールを書き換えるため、以下のガードレールが必要である。

- デグレード防止
- 意図しない過激なルール追加の抑止
- 自動テストによる検証プロセス
- approval 付き更新

---

## 3. マルチエージェント・オーケストレーション

### 3.1 機能概要

役割別エージェントを並列稼働させる機能である。
単一エージェント万能型ではなく、Planner、Retriever、PatchWorker、Validator、Integrator のような役割分化と、必要に応じた中間管理ロールを持つ階層型オーケストレーションを採用する。
加えて、1 つの巨大なタスクを 1 体の LLM にやらせるのではなく、複数のローカル LLM インスタンスを並列起動し、それぞれに異なる専門役割を付与し、TCP ソケットやローカルファイルシステムを介して議論・同期しながら並列処理を行う能力も対象とする。

### 3.2 効果

- 並列実行による高速化
- 専門特化による品質向上
- 大規模変更への対応
- レビュー品質向上
- コンテキスト分割による品質安定
- 実装、検証、統合の責務境界明確化
- コンテキスト肥大化による精度低下の抑制
- 大規模リファクタリングや複数ファイルにまたがる変更への対応
- 「実装 → テスト失敗 → 議論 → 修正」の自動サイクル化

### 3.3 実現方式

#### 3.3.1 推奨アーキテクチャ

```text
User
  ↓
Orchestrator
  ├─ Planner
  ├─ Coder / PatchWorker
  ├─ Reviewer
  ├─ Tester / Validator
  ├─ Refactorer / Integrator
  ├─ Researcher / Retriever
  └─ Memory Manager
```

#### 3.3.2 推奨役割

- Planner: タスク分解
- Retriever / Researcher: 調査・コンテキスト取得
- Coder / PatchWorker: 実装
- Reviewer: コードレビュー
- Tester / Validator: テスト / 検証
- Refactorer: 改善
- Integrator: 統合
- Memory Manager: 知識管理

#### 3.3.3 オーケストレーター責務

- タスク分解
- Worker 割当
- phase 管理
- barrier 管理
- merge / test / retry 判定

#### 3.3.4 Worker 方針

各 Worker には role-specific prompt と allowed-tools を定義する。
さらに、タスクに応じたペルソナ自動切替を行う。

- coding は senior engineer
- docs は technical writer
- research は analyst

#### 3.3.5 通信方式

- MCP
- TCP Server
- gRPC
- Redis Queue
- ファイルシステム監視ベースの inbox / outbox モデル

#### 3.3.6 実装形態

- tmux 等で複数エージェントプロセスを非同期起動
- 自作 TCP サーバーまたはファイルシステム監視ベースの MCP サーバーで制御
- メッセージング
- フェーズ同期
- バリア同期
- 議論ループ

#### 3.3.7 作業分離

- worktree または branch 単位で分離
- 成果物は Git に集約

### 3.4 留意点

- 複数プロセスのライフサイクル管理
- メッセージのデッドロック防止
- 役割ごとのプロンプト制御
- 分散システム特有の同期設計

---

## 6. 自律ルール生成システム

### 6.1 機能概要

エージェントが開発ルールを自動提案する機能である。
コードベース、会話履歴、PR レビューから、プロジェクト固有のルールや Skill 化候補を抽出し、.claude/rules/ 相当のルールセットや Skill パッケージを生成・更新する機構を中核とする。

### 6.2 効果

- チーム標準化
- レビュー削減
- コード品質安定
- チーム固有流儀の自動学習
- レビュー文化の再利用
- Agent ごとの差異縮小
- コンテキストの無駄な肥大化防止

### 6.3 実現方式

#### 6.3.1 基本ロジック

```text
if same_failure > 3:
  propose_rule()
```

#### 6.3.2 ルール抽出ソース

- codebase
- conversation JSONL
- PR review comment

#### 6.3.3 出力分類

- principles
  - 横断共有可能な原則
- project-specific patterns
  - プロジェクト固有規約
- examples
  - 必要時参照のコード例

#### 6.3.4 自動更新モード

- --from-conversation 相当
  - ユーザー修正発話から抽出
- --from-pr 相当
  - レビューコメントから抽出
- --restructure 相当
  - ルールファイル分割最適化

#### 6.3.5 自動生成対象

- 命名規則
- テスト必須条件
- PR テンプレ
- lint ルール
- dependency policy
- プロジェクト固有スタイル
- プロジェクト定義シンボル
- レイヤ別規約

#### 6.3.6 適用方針

- 自動反映ではなく提案 PR として出す
- レビュー専用 Worker に抽出を担わせる構成も有効

### 6.4 留意点

- 一般論と固有ルールの分離
- ノイズ混入対策
- 妥当性判断の自動化難度
- 改悪の防止

---

## 7. 非同期バックグラウンドエージェント

### 7.1 機能概要

ユーザーが操作していない間もエージェントが動く機能である。
毎日または毎週の定時バッチで、レビュー、失敗ログ、日報、進捗、PR コメントを収集・要約し、Tips、Rules、記憶更新、ダッシュボード更新を行う Routine 機能もここに含む。

### 7.2 効果

- 夜間自動改善
- 自動リファクタリング
- 継続監視
- 先回り修正
- 人が明示的に振り返らなくても知見を蓄積
- チーム知識の鮮度維持
- 記憶とルールの更新漏れ削減
- 継続改善の実運用化

### 7.3 実現方式

#### 7.3.1 常駐ジョブ例

- Dependabot 型更新
- 脆弱性検知
- TODO 消化
- 未使用コード削除
- review-tips-poster
- rule extractor
- memory compactor
- failure summarizer
- dashboard refresh

#### 7.3.2 入力ソース

- gh API
- git log
- session JSONL
- event log
- 日報
- PR コメント

#### 7.3.3 出力先

- memory/
- .rules/
- reports/weekly.md
- dashboard.md

#### 7.3.4 ジョブ基盤

- Temporal
- Celery
- Prefect
- systemd timer
- cron
- OpenRC service + cron

#### 7.3.5 適用方針

- 自動適用よりも PR 作成または approval queue への投入を推奨

---

## 8. 実行トレーサビリティ & Replay

### 8.1 機能概要

全エージェント行動を再現可能にする機能である。
Prompt、Tool Call、Diff、Decision Reason、Token Usage を保存し、デバッグ、監査、事故解析、改善分析に使えるようにする。

### 8.2 効果

- デバッグ容易
- AI 監査
- 事故解析
- 改善分析
- 実行再現性向上

### 8.3 実現方式

#### 8.3.1 保存対象

- Prompt
- Tool Call
- Diff
- Decision Reason
- Token Usage
- Event Log
- Worker ごとの成功 / 失敗履歴

#### 8.3.2 推奨構成

- OpenTelemetry + Event Store
- JSONL / SQLite を使った軽量イベントストア
- Replay による再現
- 可視化ダッシュボード連携

---

## 2026年版 ローカルLLMエージェント推奨アーキテクチャ

```text
┌─────────────────┐
│ User Interface  │
└────────┬────────┘
         │
┌────────▼───────────────┐
│ Orchestrator           │
│ - Task decomposition   │
│ - Scheduling           │
│ - Retry / Timeout      │
│ - Rule / Memory bridge │
└────────┬───────────────┘
         │
┌────────┼──────────────────────────────────────┐
│        │                                      │
│  ┌─────▼─────┐   ┌───────────────▼──────────┐ │
│  │ Planner   │   │ Coding / Patch Agents    │ │
│  └─────┬─────┘   └───────────────┬──────────┘ │
│        │                          │            │
│  ┌─────▼─────┐   ┌───────────────▼──────────┐ │
│  │ Retriever │   │ Reviewer / Validator     │ │
│  └─────┬─────┘   └───────────────┬──────────┘ │
│        │                          │            │
│  ┌─────▼──────────────────────────▼─────────┐ │
│  │ Integrator / Refactorer / Memory Manager │ │
│  └──────────────────────┬───────────────────┘ │
└─────────────────────────┼─────────────────────┘
                          │
                ┌─────────▼─────────┐
                │ Persistent Memory │
                │ - JSONL           │
                │ - SQLite          │
                │ - Vector Index    │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Rule / Skill Base │
                │ - RULES.md        │
                │ - SKILL.md        │
                │ - Examples        │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ MCP Tool Servers  │
                │ - Git             │
                │ - FS              │
                │ - DB              │
                │ - Docker          │
                │ - Browser         │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Trace / Event Log │
                │ - OpenTelemetry   │
                │ - Event Store     │
                │ - Replay          │
                └───────────────────┘
```

---

## 優先順位（現実的導入順）

### 第1優先

- Markdown 圧縮 / Context Compression Engine
- 永続記憶
- MCP 統合
- 実行トレース

理由。
単体エージェントの品質を最短で上げやすく、ローカル運用との相性が良い。

### 第2優先

- マルチエージェント
- 自己改善

理由。
基盤価値は高いが、ログ設計・権限設計・通信設計が必要である。

### 第3優先

- 自律ルール生成
- 完全自律バックグラウンド

理由。
複数 Worker を本格運用する段階で真価が出る。

### 別表: 実装観点を含めた優先群

#### 優先群 A

- 永続記憶レイヤー
- Markdown 専用索引
- Rules / Skill 自動抽出
- Routine とナレッジ蒸留ジョブ

#### 優先群 B

- 自己改善ループ
- MCP Gateway
- Agent 間メッセージング

#### 優先群 C

- 階層型オーケストレーション高度化
- 自動ペルソナ切替
- 常設ダッシュボード

---

## 最重要ポイント

今回の記事群から読み取れる本質は、**「単発プロンプト実行」から「長期的に進化するソフトウェア開発組織」へ LLMエージェントが変化していること** である。
つまり重要なのはモデル性能だけではない。設計すべき中心は以下である。

- 記憶
- 改善
- 分業
- コンテキスト圧縮
- ツール接続
- 監査可能性

小規模なローカルLLMエージェントを実務で強くするなら、最初に追加すべきは以下の 4 点である。

- 永続記憶
- Markdown 局所検索
- Rules / Skill 自動抽出
- 定期蒸留 Routine

この 4 点で、以下の典型的な弱点をかなり潰せる。

- 毎回忘れる
- 毎回全文を読む
- 毎回同じ指摘を繰り返す
- 改善が蓄積しない

その上で、オーケストレーター中心の運用を強めるなら、自己改善ループ、MCP Gateway、Agent-to-Agent 通信を足していく順序が妥当である。

---

## 付録. 次段の具体化候補

必要なら次段として、上記機能群を以下の粒度まで落として提示可能である。

- Must / Should / Could に分けた導入計画
- 既存の中央オーケストレーター型アーキテクチャへの埋込設計
- Python ベースのモジュール構成案
- ディレクトリ構成案
- Event Bus / Memory / MCP の統合仕様案
