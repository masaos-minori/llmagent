# Split Log

## 設計方針（将来の分割作業でも有効）

### Context Loader Pattern

```
Task → Routing → Minimal Skills → Shared Rules → Execution
```

### 4 原則

| 原則 | 内容 |
|---|---|
| **routing** | 分割後、`routing.md` の "Docs → task mapping" にタスク種別→参照ファイルの対応を追記する |
| **dependency direction** | 新ファイル間の依存は単方向に保つ。循環インポート・循環参照を作らない |
| **minimal loading** | 1 タスクで読む必要があるファイルが最小になるよう責務境界を引く |
| **shared normalization** | 複数ファイルに重複する共通仕様・プロトコル定義は 1 ファイルに集約し、他からは参照のみとする |


## 現状サマリー

### docs/

| ファイル | 行数 | 状態 |
|---|---|---|
| `00_llm-implementation-guide.md` | 24L | index |
| `01_overview.md` | 339L | 変更なし |
| `02_deployment.md` | 239L | 変更なし |
| `03_ingestion-pipeline.md` | 4L | index に変換（分割完了） |
| `03_ingestion-run.md` | 62L | 新規（実行ガイド） |
| `03_ref-ingestion.md` | 326L | 新規（API リファレンス） |
| `04_mcp-servers.md` | 10L | index |
| `04_mcp-web-search.md` | 185L | 分割済 |
| `04_mcp-file.md` | 198L | 分割済 |
| `04_mcp-github.md` | 209L | 分割済 |
| `04_mcp-protocol.md` | 60L | 分割済 |
| `05_agent.md` | 259L | 縮小（s3+s4+s5: ツール仕様・チューニング・実装注意） |
| `05_agent-ops.md` | 85L | 新規（起動・確認・トラブルシューティング） |
| `05_agent-impl.md` | 319L | 分割済 |
| `06_common.md` | 10L | index |
| `06_ref-infra.md` | 189L | 縮小（config_loader/rag_utils/logger/formatters のみ） |
| `06_ref-sqlite.md` | 117L | 新規（sqlite_helper.py） |
| `06_ref-mcp.md` | 181L | 分割済 |
| `06_ref-rag.md` | 143L | 分割済 |
| `06_ref-agent.md` | 14L | index（分割完了） |
| `06_ref-agent-session.md` | — | 分割済（agent_session.py） |
| `06_ref-agent-repl.md` | — | 分割済（agent_repl.py） |
| `06_ref-agent-config.md` | — | 分割済（agent_config.py） |
| `06_ref-agent-context.md` | — | 分割済（agent_context.py） |
| `06_ref-agent-view.md` | — | 分割済（cli_view.py） |
| `06_ref-agent-commands.md` | — | 分割済（agent_commands.py + ミックスイン群） |
| `06_ref-agent-llm.md` | — | 分割済（llm_client.py） |
| `06_ref-agent-history.md` | — | 分割済（history_manager.py） |

### scripts/（分割対象のみ）

| ファイル | 行数 | 状態 |
|---|---|---|
| `agent_repl.py` | 540L | 分割済（残留コア） |
| `agent_repl_debug.py` | 116L | 分割済 |
| `agent_repl_health.py` | 169L | 分割済 |
| `agent_repl_tool_exec.py` | 186L | 分割済 |
| `github_mcp_server.py` | 1043L | 分割済（残留コア） |
| `github_mcp_models.py` | 414L | 分割済 |
| `github_mcp_service.py` | 770L | 分割済 |
| `fileop_mcp_server.py` | 726L | 分割済（残留コア） |
| `fileop_mcp_models.py` | 281L | 分割済 |
| `fileop_mcp_service.py` | 748L | 分割済 |
| `agent_commands.py` | 187L | 分割済（残留コア） |
| `agent_cmd_session.py` | 125L | 分割済 |
| `agent_cmd_mcp.py` | 176L | 分割済 |
| `agent_cmd_config.py` | 318L | 分割済 |
| `agent_cmd_context.py` | 260L | 分割済 |
| `agent_cmd_rag.py` | 253L | 分割済 |
| `agent_cmd_ingest.py` | 162L | 分割済 |
| `agent_rag.py` | 253L | 分割済（残留コア） |
| `rag_types.py` | 45L | 分割済 |
| `rag_repository.py` | 316L | 分割済 |
| `rag_llm.py` | 381L | 分割済 |

### order.txt 対象 — 全完了

| 対象 | 状態 |
|---|---|
| `scripts/github_mcp_server.py` 2098L | 完了 |
| `scripts/fileop_mcp_server.py` 1649L | 完了 |
| `scripts/agent_commands.py` 1286L | 完了 |
| `scripts/agent_rag.py` 954L | 完了 |
| `docs/06_ref-agent.md` 494L | 完了 |

---

## file_divide.txt 分割計画（2026-05-26）

対象: `CLAUDE.md` および `docs/*.md`
方針: Context Loader Pattern + 4 原則 (routing / dependency direction / minimal loading / shared normalization)
制約: 実ファイルの分割・書換は行わない。計画のみ。

### 分割トリガー判定

| ファイル | 行数 | 独立責務数 | トリガー判定 |
|---|---|---|---|
| `CLAUDE.md` | 261L | 複数（Architecture 9 節） | **対象外** — 400L 未満 |
| `docs/01_overview.md` | 339L | 3 (概要/アーキテクチャ/ファイル構成) | **対象外** — 400L 未満 |
| `docs/03_ingestion-pipeline.md` | 385L | 4 (運用手順/web_crawler/chunk_splitter/rag_ingester) | **対象** — 400L 直前 + 責務混在 |
| `docs/05_agent.md` | 344L | 3 (起動・確認/ツール仕様/チューニング) | **対象** — minimal loading 違反が大きい |
| `docs/05_agent-impl.md` | 319L | 2 (REPL パイプライン/実装詳細) | **対象外** — 責務境界が曖昧で分割効果が小さい |
| `docs/06_ref-infra.md` | 307L | 5 (config_loader/rag_utils/sqlite_helper/logger/formatters) | **対象** — sqlite_helper が独立参照されることが多い |

---

### 計画 1: docs/03_ingestion-pipeline.md → 2 ファイル

#### 現状責務

| 節 | 行範囲 | 内容 | タスク種別 |
|---|---|---|---|
| s1 | L1–62 | 運用手順・ファイルライフサイクル | 実行・デプロイ |
| s2 | L64–167 | `web_crawler.py` API リファレンス | コード実装 |
| s3 | L169–265 | `chunk_splitter.py` API リファレンス | コード実装 |
| s4 | L267–361 | `rag_ingester.py` API リファレンス | コード実装 |
| s5 | L363–386 | 実装注意事項・データフロー | コード実装 |

s1 (運用手順) と s2–s5 (API リファレンス群) は異なるタスクから参照される。現状はどちらのタスクでも全 385 行を読む。

#### 提案ファイル構成

| 新ファイル | 内容 | 推定行数 | 担当タスク |
|---|---|---|---|
| `docs/03_ingestion-run.md` | s1: 運用手順・実行コマンド・ファイルライフサイクル | ~62L | 取込実行・デプロイ |
| `docs/03_ref-ingestion.md` | s2–s5: 3 スクリプトの API リファレンス + 実装注意事項 | ~323L | 取込パイプライン実装 |

s2–s5 を 1 ファイルにまとめる理由: 3 スクリプトは `web_crawler → chunk_splitter → rag_ingester` の直列パイプラインであり、コード修正時は必ずパイプライン全体の接続仕様を確認する。これ以上分割すると minimal loading に逆行する。

#### dependency direction

```
docs/03_ingestion-run.md  ──参照→  docs/03_ref-ingestion.md
                                   (逆方向の参照なし)
```

実行手順ドキュメントは API 仕様を参照するが、API 仕様は実行手順を参照しない。

#### routing.md 変更

削除:
```
| Ingestion pipeline | `docs/03_ingestion-pipeline.md` |
```

追加:
```
| Ingestion pipeline run (execute commands, file lifecycle) | `docs/03_ingestion-run.md` |
| Ingestion pipeline code (web_crawler / chunk_splitter / rag_ingester API) | `docs/03_ref-ingestion.md` |
```

#### shared normalization チェック

パイプラインデータフロー図は s5 (実装注意事項) にある。`03_ref-ingestion.md` に集約し、`03_ingestion-run.md` からはリンクのみとする。重複なし。

---

### 計画 2: docs/06_ref-infra.md → 2 ファイル

#### 現状責務

| 節 | 行範囲 | 内容 | 参照頻度 |
|---|---|---|---|
| s1 | L15–50 | `config_loader.py` — 設定ファイル読み込み | 中 |
| s2 | L51–83 | `rag_utils.py` — テキスト正規化ユーティリティ | 低 |
| s3 | L84–199 | `sqlite_helper.py` — DB 接続マネージャ | **高** (DB 関連タスクで単独参照) |
| s4 | L200–262 | `logger.py` — ロギング設定 | 低 |
| s5 | L263–307 | `formatters.py` — 出力フォーマッタ | 低 |

`sqlite_helper.py` はセッション管理・RAG 取込・DB メンテナンス・tool_result_store など多数のモジュールから参照される。DB 関連タスクでは `sqlite_helper.py` の仕様のみが必要だが、現状は s1–s2–s4–s5 も含む 307 行を読む。

#### 提案ファイル構成

| 新ファイル | 内容 | 推定行数 | 担当タスク |
|---|---|---|---|
| `docs/06_ref-sqlite.md` | s3: `sqlite_helper.py` API + WAL/トランザクション仕様 | ~116L | DB 操作・セッション・取込 |
| `docs/06_ref-infra.md` (縮小) | s1+s2+s4+s5: config_loader / rag_utils / logger / formatters | ~190L | 設定・ロギング・フォーマット |

#### dependency direction

```
docs/06_ref-infra.md  ──参照→  docs/06_ref-sqlite.md
                               (逆方向の参照なし)
```

config_loader は DB を参照しない。rag_utils / logger / formatters も同様。

#### routing.md 変更

変更:
```
# 変更前
| Config / DB / logger / formatters | `docs/06_ref-infra.md` |
| Session / DB persistence          | `docs/06_ref-agent-session.md` |

# 変更後
| SQLite / DB connection / WAL / transactions | `docs/06_ref-sqlite.md` |
| Config / logger / formatters / rag_utils   | `docs/06_ref-infra.md` |
| Session / DB persistence                   | `docs/06_ref-agent-session.md` + `docs/06_ref-sqlite.md` |
```

#### shared normalization チェック

WAL モード・`busy_timeout`・`synchronous=NORMAL` の説明は `sqlite_helper.py` に集約済み。`rag_ingester.py` の API リファレンス (`03_ref-ingestion.md`) が WAL に言及する場合は `06_ref-sqlite.md` への参照リンクに変更し、重複記述を排除する。

---

### 計画 3: docs/05_agent.md → 2 ファイル

#### 現状責務

| 節 | 行範囲 | 行数 | 内容 | タスク種別 |
|---|---|---|---|---|
| s1 | L3–20 | 18L | エージェント起動コマンド | 運用 |
| s2 | L21–71 | 51L | 動作確認・ヘルスチェック | 運用 |
| s3 | L72–271 | 200L | ツールコーリング仕様・ツール一覧 | ツール仕様参照・実装 |
| s4 | L272–316 | 45L | チューニング指針 | 開発調整 |
| s5 | L317–329 | 13L | 主要な実装注意事項 | 開発参照 |
| s6 | L330–344 | 15L | トラブルシューティング | 運用 |

s3 のツールコーリング仕様 (200 行) は全タスクで読み込まれるが、デプロイ・起動確認タスクには不要。逆にツール実装タスクでは s1/s2/s6 の運用節は不要。

#### 提案ファイル構成

| 新ファイル | 内容 | 推定行数 | 担当タスク |
|---|---|---|---|
| `docs/05_agent-ops.md` | s1+s2+s6: 起動・確認・トラブルシューティング | ~84L | デプロイ・運用・ヘルスチェック |
| `docs/05_agent.md` (縮小) | s3+s4+s5: ツール仕様・チューニング・実装注意 | ~258L | ツール実装・エージェント機能追加 |

#### dependency direction

```
docs/05_agent-ops.md  (運用)   — 参照なし (standalone)
docs/05_agent.md      (仕様)   — 参照なし (standalone)
```

運用手順とツール仕様の間に技術的な依存関係はない。

#### routing.md 変更

変更:
```
# 変更前
| Agent features / slash commands | `docs/05_agent.md` + `docs/06_ref-agent-commands.md` |

# 変更後
| Agent startup / verification / troubleshooting | `docs/05_agent-ops.md` |
| Agent features / slash commands / tool calling | `docs/05_agent.md` + `docs/06_ref-agent-commands.md` |
```

また `Deploy / production` タスクの参照先に `docs/05_agent-ops.md` を追加する:
```
| Deploy / production | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent-ops.md` |
```

#### shared normalization チェック

ツール名・ポート番号は `rules/env.md` が正とする。`05_agent.md` (縮小後) がポート番号を記載している場合は `rules/env.md` への参照リンクに置き換え、重複を除去する。

---

### CLAUDE.md — 分割不要の判断

| 項目 | 値 |
|---|---|
| 行数 | 261L |
| 400L トリガー | 未達 |
| Architecture 節の行数 | L75–220 = 146L |

**判断: 分割しない。**

Architecture 節は 9 サブシステムを 146 行で記述しており、1 節あたり平均 16 行。サブシステム単位での分割は読み込みファイル数を増やすだけで minimal loading に逆行する。各サブシステムの詳細仕様はすでに `docs/06_ref-*.md` に分離されており、CLAUDE.md は「どこを読むべきか」の索引として機能している。

ただし以下は改善余地あり:

| 問題 | 対処方針 |
|---|---|
| Architecture 節の各節末尾に「詳細は `docs/XX_YY.md` 参照」リンクがない | docs 参照リンクを各節末尾に追記（書換ではなくリンク追記のため分割不要） |
| `docs/04_mcp-servers.md` と `docs/06_common.md` が 10L の空インデックスのまま日本語 | 内容を英語インデックスに書き換えるか削除（分割ではなく書換タスク） |

---

### 実施優先順位

| 優先度 | 対象 | 理由 |
|---|---|---|
| 1 | `docs/03_ingestion-pipeline.md` | 385L で 400L トリガー直前。コンテンツ追加で即トリガー到達 |
| 2 | `docs/05_agent.md` | s3 (ツール仕様 200L) が不要なタスクにまで読まれており minimal loading 違反が最大 |
| 3 | `docs/06_ref-infra.md` | sqlite_helper の独立参照頻度が高く、分割後の routing 効果が大きい |

---

### 実施手順（分割時の参照用）

CLAUDE.md の File Split Rule に定義された手順を再掲。

1. このファイル (`04_split_plan.md`) の計画を確認し、分割グループと新ファイル名を確定する
2. 実ファイルを分割し、元ファイルをインデックス（リンクリスト）または空ファイルに変換する
3. `routing.md` の "Docs → task mapping" を「計画」列の通りに更新する
4. `rules/env.md`・スキルファイル・`docs/00_llm-implementation-guide.md` 内のファイル参照を新パスに修正する
5. `CLAUDE.md` の Documentation layout 節を更新する
6. `ruff` / `mypy` / `pytest` は docs 分割では不要。リンク切れを `grep` で確認する
