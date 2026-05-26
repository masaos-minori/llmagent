# ファイル分割計画

作成日: 2026-05-26  
対象: `CLAUDE.md` および `docs/*.md`  
方針: Context Loader Pattern (Task → routing.md → Minimal Skills + Shared Rules → Relevant docs → Execution) に基づく minimal loading の実現

**本計画はレビュー待ち。ファイルの分割・書換はレビュー承認後に実施する。**

---

## 現状分析

### 行数サマリ（分割トリガー = 400行 + 複数独立責務）

| ファイル | 行数 | トリガー到達まで | 状態 |
|---|---|---|---|
| `CLAUDE.md` | 284 | 116行 | 設計問題あり（後述） |
| `docs/01_overview.md` | 339 | 61行 | 要監視・分割計画必要 |
| `docs/05_agent-impl.md` | 319 | 81行 | 要監視・分割計画必要 |
| `docs/03_ref-ingestion.md` | 326 | 74行 | 要監視・分割計画必要 |
| `docs/05_agent.md` | 259 | 141行 | 当面不要 |
| 上記以外 | ≤ 209 | — | 対応不要 |

### 設計課題（行数トリガー外）

**CLAUDE.md の minimal loading 問題**

CLAUDE.md はすべてのタスクで必ずロードされる。しかし Architecture セクション（MCP サーバ一覧・DB 層詳細・RAG パイプライン詳細・Plugin Architecture・Slash Commands 全表等）はタスク依存情報であり、常時ロードは不要なコンテキストを増大させる。詳細は既に docs/ に存在するため、CLAUDE.md の Architecture セクションは「高レベル概要 + docs/ へのポインタ」に絞るべきである。

**06_common.md の shared normalization 不足**

現行 11 行のインデックスのみ。共通プロトコル仕様・型定義・エラーコードの集約先として機能していない。

---

## 分割計画

### Plan-A: `CLAUDE.md` の Architecture セクション縮小

**分割トリガー**: 未達（284行）  
**根拠**: minimal loading 原則違反。全タスクにタスク依存情報が常時ロードされている

**実施内容**:

1. Architecture セクションの各サブセクションを以下の方針で整理
   - MCP サーバ一覧 → `docs/04_mcp-servers.md` へのポインタのみ残す
   - DB 層詳細 → `docs/06_ref-sqlite.md` + `docs/06_ref-infra.md` へのポインタ
   - RAG パイプライン詳細 → `docs/06_ref-rag.md` へのポインタ
   - Plugin Architecture → `docs/06_ref-agent-repl.md` へのポインタ（またはそのまま）
   - Slash Commands 全表 → `docs/06_ref-agent-commands.md` へのポインタ
   - Ingestion Pipeline 詳細 → `docs/03_ref-ingestion.md` へのポインタ

2. 削除せず「1〜2行の概要 + 参照先」に圧縮する

**目標行数**: 180〜200行（Architecture セクションを 100 行程度削減）

**routing.md 更新**: 不要（docs/ 側のファイルパスは変わらない）

---

### Plan-B: `docs/01_overview.md` の分割

**分割トリガー**: 339行（61行で到達）  
**複数責務**: アーキテクチャ概要 (セクション 1–2) / ファイル構成 (セクション 3)

**現行セクション構成**:

```
## 1. 概要・目的
## 2. アーキテクチャ
  ### 2.1 プロセス構成
  ### 2.2 取込パイプライン
  ### 2.3 クエリパイプライン
  ### 2.4 MCP サーバ呼出の実現方式と仕様
  ### 2.5 実装済み機能
  ### 2.6 スラッシュコマンド一覧
## 3. ファイル構成
```

**分割案**:

| 新ファイル | 収録セクション | 想定用途 |
|---|---|---|
| `docs/01_overview-arch.md` | セクション 1〜2（概要・アーキテクチャ全体） | システム全体の構造把握タスク |
| `docs/01_overview-files.md` | セクション 3（ファイル構成） | モジュール配置の確認タスク |
| `docs/01_overview.md` | インデックス（リンクリスト）に変換 | — |

**dependency direction**: `01_overview-arch.md` は `01_overview-files.md` を参照しない。逆も同様。相互参照なし。

**routing.md 更新**:

```
# 変更前
| システム概要確認 | docs/01_overview.md |

# 変更後
| システム全体アーキテクチャ確認 | docs/01_overview-arch.md |
| ファイル・モジュール配置確認   | docs/01_overview-files.md |
```

---

### Plan-C: `docs/05_agent-impl.md` の分割

**分割トリガー**: 319行（81行で到達）  
**複数責務**: クラス API 詳細 (セクション 1) / REPL 処理フロー + 実装詳細 (セクション 2〜3)

**現行セクション構成**:

```
## 1. agent.py 実装詳細
  ### 1.1–1.7 機能概要・実装方式・IO・エラー・ログ・設定・クラスAPI
  #### AgentREPL / AgentContext / CLIView / CommandRegistry / RagPipeline
## 2. REPL パイプライン処理フロー
## 3. 実装詳細
  ### 3.1 RAG パラメータとホットリロード
  ### 3.2 LLM 生成パラメータ
  ### 3.3 コンテキスト管理
  ### 3.4 ツール実行
  ### 3.5 高度な RAG 機能
  ### 3.6 セッション管理・ノート
  ### 3.7 運用・保守
```

**分割案**:

| 新ファイル | 収録セクション | 想定用途 |
|---|---|---|
| `docs/05_agent-impl-class.md` | セクション 1（クラス API・構造） | クラス設計・コンストラクタ修正タスク |
| `docs/05_agent-impl-flow.md` | セクション 2〜3（フロー・実装詳細） | Orchestrator・ツール実行・RAG 修正タスク |
| `docs/05_agent-impl.md` | インデックスに変換 | — |

**dependency direction**: `05_agent-impl-class.md` → `06_ref-agent-context.md` 参照可。`05_agent-impl-flow.md` → `06_ref-rag.md` 参照可。両者間の相互参照なし。

**routing.md 更新**:

```
# 変更前
| Agent REPL loop / tool execution | docs/05_agent-impl.md + docs/06_ref-agent-repl.md + docs/06_ref-agent-history.md |

# 変更後
| Agent REPL クラス構造           | docs/05_agent-impl-class.md + docs/06_ref-agent-repl.md |
| Agent REPL フロー / tool execution | docs/05_agent-impl-flow.md + docs/06_ref-agent-history.md |
```

---

### Plan-D: `docs/03_ref-ingestion.md` の分割

**分割トリガー**: 326行（74行で到達）  
**複数責務**: web_crawler API (セクション 2) / chunk_splitter API (セクション 3) / rag_ingester API (セクション 4) / 共通実装注意事項 (セクション 5)

**現行セクション構成**:

```
## 2. web_crawler.py  （API リファレンス）
## 3. chunk_splitter.py （API リファレンス）
## 4. rag_ingester.py  （API リファレンス）
## 5. 実装注意事項（パイプラインデータフロー・FTS5 仕様）  ← 共有事項
```

**分割案**:

| 新ファイル | 収録セクション | 想定用途 |
|---|---|---|
| `docs/03_ref-crawler.md` | セクション 2（web_crawler.py API） | クローラ修正タスク |
| `docs/03_ref-splitter.md` | セクション 3（chunk_splitter.py API） | チャンク分割修正タスク |
| `docs/03_ref-ingester.md` | セクション 4（rag_ingester.py API） | インジェスタ修正タスク |
| `docs/03_ref-ingestion.md` | セクション 5（共通実装注意事項）をインデックス化 | — |

**shared normalization**: セクション 5（`5.1 パイプラインデータフロー`・`5.2 FTS5 クエリ`・`5.3 FTS5/LLM コンテンツ分離`）は全スクリプト共通の仕様であるため、元ファイルに保持してサブファイルから参照させる。

**dependency direction**:
- `03_ref-crawler.md` → `03_ref-ingestion.md`（セクション5）参照可
- `03_ref-splitter.md` → `03_ref-ingestion.md`（セクション5）参照可
- `03_ref-ingester.md` → `03_ref-ingestion.md`（セクション5）参照可
- サブファイル間の相互参照なし

**routing.md 更新**:

```
# 変更前
| Ingestion pipeline code (web_crawler / chunk_splitter / rag_ingester API) | docs/03_ref-ingestion.md |

# 変更後
| web_crawler.py 修正          | docs/03_ref-crawler.md |
| chunk_splitter.py 修正       | docs/03_ref-splitter.md |
| rag_ingester.py 修正         | docs/03_ref-ingester.md |
| Ingestion 共通実装注意事項    | docs/03_ref-ingestion.md |
```

---

### Plan-E: `docs/06_common.md` の shared normalization 強化

**分割トリガー**: 対象外（分割ではなく拡充）  
**根拠**: 現行 11 行のインデックスのみで、shared normalization 先として機能していない

**拡充候補**:

| 追加項目 | 現在の所在 | 移動後 |
|---|---|---|
| MCP `CallToolRequest` / `CallToolResponse` 共通フォーマット | `docs/04_mcp-protocol.md` 内に分散 | `docs/06_common.md` |
| `RagHit` / `LLMMessage` TypedDict 定義 | `rag_types.py` の説明が `06_ref-rag.md` に | `docs/06_common.md` |
| ツール結果 `(str, bool)` 戻り値規約 | `CLAUDE.md` Plugin Architecture 節 | `docs/06_common.md` |

**dependency direction**: `06_common.md` は他の `docs/` ファイルを参照しない（被参照のみ）

---

## 実施順序（依存関係順）

```
Step 1: Plan-E（06_common.md 拡充） ← 他ファイルが参照するため先行
Step 2: Plan-A（CLAUDE.md Architecture 縮小） ← routing.md 変更なし
Step 3: Plan-B（01_overview 分割）         ← routing.md 更新を伴う
Step 4: Plan-C（05_agent-impl 分割）       ← routing.md 更新を伴う
Step 5: Plan-D（03_ref-ingestion 分割）    ← routing.md 更新を伴う
```

Step 3〜5 は 400 行トリガー到達後に実施。**現時点では Step 1・2 のみが着手可能**。

---

## 設計方針チェックリスト

| 方針 | 確認ポイント |
|---|---|
| **routing** | 分割後の全サブファイルを routing.md の「Docs → task mapping」に追加。インデックスファイルは routing.md に載せない（サブファイルを直接指定） |
| **dependency direction** | サブファイル間の相互参照ゼロを維持。共有事項は shared normalization ファイルにのみ記述し、サブファイルはそれを参照する |
| **minimal loading** | 1 タスクで読み込む docs/ ファイル数を最大 2 本に抑える。`CLAUDE.md` → `routing.md` → `rules/` (1〜2本) + `docs/` (1〜2本) のフローを維持 |
| **shared normalization** | 複数サブファイルが参照する仕様は必ず 1 ファイルに集約（`06_common.md` または分割元インデックス）。重複記述禁止 |

---

## 実施後の検証コマンド（参考）

```bash
# 行数確認（400行超がないこと）
wc -l docs/*.md | sort -rn | head -10

# 相互参照チェック（サブファイル同士のリンクがないこと）
grep -rn "03_ref-crawler\|03_ref-splitter\|03_ref-ingester" docs/03_ref-*.md

# routing.md への反映漏れチェック（新ファイルが routing.md に記載されているか）
for f in docs/01_overview-*.md docs/05_agent-impl-*.md docs/03_ref-{crawler,splitter,ingester}.md; do
  grep -l "$f" routing.md || echo "MISSING in routing.md: $f"
done
```
