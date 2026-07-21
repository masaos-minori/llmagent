# docs フォルダのドキュメント品質監査結果

## 概要

docs/以下の201ファイルの構造化監査を実施。前回（2026-07-21）の修正で構造的な問題は全てクリア済み。今回は実装ギャップ・懸念事項に焦点を当てて洗い出した。

## クリア済み（前回修正済み）

| チェック項目 | 件数 | 備考 |
|---|---|---|
| コードブロックの言語指定なし | 0 | |
| 閉じられていないコードブロック | 0 | |
| YAML Front Matter必須フィールド欠落 | 0 | |
| 見出しレベルのジャンプ | 0 | |
| 空段落（3つ以上の空白行） | 0 | |
| テーブルの末尾空カラム | 0 | |
| 内部アンカー参照の欠損 | 0 | |
| 外部リンク | 0 | |
| TODO/FIXME/HACK/WIP/placeholder/dummy/tbd | 0 | |
| 同一ファイル内の重複アンカー | 0 | |

## ファイル間の重複アンカー（77箇所）— GitHubでは問題なし

GitHub-flavored Markdownはファイルごとに一意なアンカーを生成するため、ファイル間での重複は問題にならない。ただし一貫性のために整理する価値あり。

主な重複パターン：
- `#related-documents`, `#keywords` — ほぼ全ファイルで共通
- `#1-目的` — 4ファイル
- `#ファイル構成`, `#3-ファイル構成` — 11ファイル
- `#agent-cli-and-commands` — 11ファイル
- `#db-api-and-operations` — 4ファイル
- その他、類似のセクション名が複数ファイルで重複

## 要対応：不明な挙動（7箇所）

### 1. gitops_force_push_blocked / gitops_protected_branches が参照されていない

**ファイル:** `05_agent_06_02_tool-execution-and-approval-approval.md:106-107`, `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md:36`

**状況:** `agent/config_dataclasses.py` に設定フィールドとして存在するが、`tool_policy.py` / `tool_approve` から参照されていない。実際にブランチエスケープレベルを評価していない可能性がある。

**優先度:** 高

### 2. UNKNOWN ステートの意味

**ファイル:** `05_agent_02_runtime-architecture-part2.md:161`, `90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md:54`

**状況:** `McpServerHealthState.UNKNOWN` は初期/不明な状態として定義されているが、いつこの状態になるのか明確ではない。

**優先度:** 中

### 3. DAGスケジューリングの分岐ロジック

**ファイル:** `05_agent_06_01_tool-execution-and-approval-execution.md:56`

**状況:** ツール呼び出し実行関数は `if not ctx.cfg.tool.serial_tool_calls: DAGスケジューリング(...) else: 標準実行(...)` という2分岐のみで構成。serial_tool_callsがFalseの場合のDAGスケジューリングの詳細が不明。

**優先度:** 中

### 4. 安全な解釈の前提

**ファイル:** `04_mcp_90_inconsistencies_and_known_issues.md:22`, `05_agent_90_inconsistencies_and_known_issues.md:22`

**状況:** 「不明な場合に前提とすべき内容」という記述があるが、具体的な前提条件が不明。

**優先度:** 低

## 要対応：要確認事項（3箇所）

### 1. RAGインデックスの閾値

**ファイル:** `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md:118,121,134`

**状況:** 実際の閾値はハードウェアと埋め込み次元数に依存すると記載されているが、具体的な数値が不明。

**優先度:** 中

## 意図的使用（そのまま）

### 未実装（14箇所）— 既知の問題記録として意図的

- `04_mcp_90_inconsistencies_and_known_issues.md`: MCPレイヤーの既知の未実装機能（要件15のdisabled_reason等）
- `05_agent_90_inconsistencies_and_known_issues.md`: agent層の既知の未実装領域
- `90_shared_90_inconsistencies_and_known_issues.md`: shared/db層の既知の未実装機能
- `06_eventbus_01_system-overview.md:62,66`: Event Busの未実装機能（mTLS、Agent側publish）
- `04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md:56`: idle_timeout_secの設定値説明
- `04_mcp_06_07_reading-audit-logs.md:67,97`: audit_log_pathが予約済みだが未実装
- `04_mcp_00_document-guide.md:45,50`: ドキュメントガイドでの既知の不具合記録

### XXX（4箇所）— ファイルパスの例示として意図的

- `01_overview-files-01-build.md:34`: xxx.sh
- `03_rag_04_04_dto-models_config.md:82`: xxx.toml
- `90_shared_03_01_runtime_and_execution-config-and-logging.md:77,101`: xxx.toml

### 検討（6箇所）— アーキテクチャの見直しに関する記載

- `04_mcp_03_01_dispatch-and-routing.md:154`: メカニズムの統合を検討
- `04_mcp_04_04_mdq.md:43`: 設定キーの導入を検討したが既存の共有audit logを採用
- `04_mcp_05_04_mdq-rag-boundary.md:117`: MDQからRAGへの移行を検討する場合
- `04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md:30`: 廃止に関する注記
- `05_agent_08_01_configuration-loading-agent-config-part1.md:173`: backoffフィールドの削除
- `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md:144`: アーキテクチャの見直しを検討

### 確認（104箇所）— ヘルスチェックや検証手順の記載として意図的

### エスケープされたパイプ文字（80箇所）— Pythonの型注釈表記として意図的

`\|` の使用はPythonの型注釈（`list[tuple[str, str]] \| None = None` など）であり、修正不要。

### 日本語箇条書き文字「・」（276箇所）— 意図的使用

日本語文脈でのリストアイテム、区切り文字として意図的に使用。

## まとめ

**即時対応が必要なのは1箇所のみ：**

- **gitops_force_push_blocked / gitops_protected_branches が参照されていない**（優先度高）

これは承認ゲートのセキュリティ上の懸念につながるため、早急に対応が必要。
