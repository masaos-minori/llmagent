# 所有者質問パケット — compat001 / compat002 / compat003 Block解除用

## 目的
`compat001`・`compat002`・`compat003`は、リポジトリ内のコードでは**導出不可**な入力が必要で Blocking 状態です。
このパケットは所有者への照会事項をまとめた作業文档で、回答を取得・記録することで各計画書の Frozen化と実装へ進めます。

## 使い方
1. 各 issue の所有者（ステークホルダー）を特定する。
2. 下記の質問を送付する。
3. 回答を「回答記録表」（末尾）に追記する。
4. **回答が記録された質問のみ**、対応する計画書を Frozen化し実装へ進む。未回答質問が残る計画書は Draft のまま。

## 共通原則
- 回答は「推測せず記録する」。コードから推測して決定しない（各 issue の AI Implementation Instruction に準拠）。
- 「調べる事実」と「決定事項」は分けて聞く。事実はデプロイ状態、事項は所有者の判断。
- 回答は英語でも日本語どちらでも可。原文まま記録する。

---

## compat001 — デプロイ済みスキーマインベントリと最小対応スキーマの決定

**Blocking**: 各 DB の最小対応ソーススキーマ（現在のリリースがアップグレードすべき最古スキーマ）が未定義。

### 調べる事実（所有者のデプロイ状態）
各データベースについて、現在デプロイされている状態を教えてください。

- `workflow.sqlite`: 記録済みの schema version は何か（`workflow_schema_version`テーブル）
- `eventbus.sqlite`: `events` テーブルと `consumer_delivery` のカラム構成はどうか
- `mdq.sqlite`: `chunks` の形状はどうか
- 現リリースは**どのリリースからのアップグレードを保証すべきか**。現行ベースラインより古い導入はまだ存在するか

### 決定事項（所有者の判断）
- 各 DB の**最小対応ソーススキーマ**を決定してください（これが削除可否の基準になる）。
- EventBus の第2 migration パス（`scripts/eventbus/schema.py`）は意図的に分離されているか、残骸か。
- EventBus の schema-version マーカー缺失は意図的か。
- 失敗 migration に対する rollback 要件はあるか（デプロメント文書の事前バックアップ以外）。

---

## compat002 — EventBus レガシ offset インポートの終了条件と保持方針

**Blocking**: デプロイ済み offset ファイルの状態と、インポート終了条件が未定義。`compat001`に依存。

### 調べる事実（所有者のデプロイ状態）
- `offsets_dir` に**今も legacy offset または `.map` ファイルが残っている導入があるか**
- そのファイルを必要とする consumer がまだ存在するか

### 決定事項（所有者の判断）
- インポートの**終了条件**を決定してください（例：legacyファイルを保持する導入皆無＋最小対応schemaがfile eraを超えた）。
- 旧 offset ファイルの**保持方針**を決定してください（rollback/audit用維持、アーカイブ、削除）。削除する場合の権限とバックアップ取扱いも併せて。
- consumer-id collision は startup を停止すべきか、ログ出力のインポート一部省略で許容すべきか。
- completion マーカーを付けるか。
- ファイルベースの `write_offset()` / `read_offset()` はインポートとともに削除すべきか（削除は別issue）。

---

## compat003 — Agent パッケージ再エクスポート名の削除

**Blocking**: リポジトリ外からのインポート有無の所有者確認。in-repo では12名へのcallerはゼロ確認済み。

### 調べる事実（所有者の確認）
- リポジトリ外のスクリプト・プラグイン・opsツールが、`agent`パッケージから以下の12名のいずれかをインポートしていないことの確認：
  `ReplInputLoop`, `SessionPersister`, `WalCheckpointManager`, `ResourceShutdownCoordinator`, `StartupBanner`, `SignalHandler`, `AgentREPL`, `BgTaskMonitor`, `AuditEventEmitter`, `ConversationStateManager`, `LlmTurnExecutor`, `WorkflowEngineAdapter`

### 決定事項（所有者の判断）
- 公開パス削除前の**リリース/サポート通知方針**があるか（事前通知が必要か）。
- （依存：`compat009` で Glossary 引用を削除後の実施）

---

## 回答記録表

記録日: 2026-10-21。「回答者/日」の区分は次のとおり。

- **owner**: ユーザーが owner として決定・承認した事項。
- **実測**: 本番ホスト(`/opt/llm`)を read-only で確認した事実(Claude が取得)。
- **導出案**: 検証済みの挙動から Claude が文面を導出した事項。**owner の明示的な承認は未取得**。
- **未決**: 回答なし。docs に open decision として記録済み。

| Issue | 質問ID | 質問（要約） | 分類 | 回答 | 回答者/日 | Frozen判定 |
|---|---|---|---|---|---|---|
| compat001 | C001-fact-1 | workflow.sqlite の current schema version | 事実 | `1.1.0`(コードの `WORKFLOW_SCHEMA_VERSION` と一致) | 実測 / 2026-10-21 | Frozen済・docs反映済(`plans/done/20261020-233138_plan.md`) |
| compat001 | C001-fact-2 | events / consumer_delivery のカラム構成 | 事実 | `eventbus.sqlite` は 2026-10-21 に現行DDLから再作成済み。`events` は `retry_count` 無し、`consumer_delivery` は `acked` 有り・`acked_at` 無し、`consumer_offsets` は `offset` 列。再作成前はテストが書き込んだ汚染schema(`last_offset` 列、`retry_count` 有り)だった | 実測 / 2026-10-21 | 同上 |
| compat001 | C001-fact-3 | chunks の形状 | 事実 | 先頭列が `chunk_id`(現行形。legacyの `id` ではない) | 実測 / 2026-10-21 | 同上 |
| compat001 | C001-fact-4 | 現リリースが保証すべきアップグレード元 / 現行より古い導入の有無 | 事実 | 導入は `/opt/llm` の単一ホストのみで、全DBが現行schema。現行より古い導入は無い | owner(単一ホストの範囲)+実測 / 2026-10-21 | 同上 |
| compat001 | C001-dec-1 | 各DBの最小対応ソーススキーマ | 決定 | 全DBとも現行リリースのschema。それより古いDBは migrate せず再作成する。`db_03` section 8e に記録済み | owner / 2026-10-21 | 同上 |
| compat001 | C001-dec-2 | EventBus 第2パス・マーカー欠如の意図 | 決定 | 未決。`db_03` section 8e の Open decisions に Owner(EventBus service)付きで記録済み。削除issue(`rmebmig`)は両パスを同時に削除する | 未決 | 同上(REQ-003 は「未決を owner 付きで記録」で充足) |
| compat001 | C001-dec-3 | 失敗migrationのrollback要件(デプロイ文書の事前バックアップ以外) | 決定 | 未決。`db_03` section 8e の Open decisions に Owner(repository maintainers)付きで記録済み | 未決 | 同上 |
| compat002 | C002-fact-1 | offsets_dir に現行のlegacyファイルがあるか | 事実 | `/opt/llm/offsets` は空(0ファイル)。`consumer_offsets` も0行(DB再作成後) | 実測 / 2026-10-21 | Frozen済・docs反映済(`plans/done/20261020-233641_plan.md`) |
| compat002 | C002-dec-1 | インポート終了条件 | 決定 | サポート対象の導入に `offsets_dir` のファイルが無くなった時点で import を削除できる。現状は条件成立のため削除issue(`rmoffimp`)を起票済み。`eventbus_07` に記録済み | 導出案(owner承認待ち) / 2026-10-21 | 同上 |
| compat002 | C002-dec-2 | ファイル保持方針 | 決定 | サービスは旧ファイルを変更・削除しない。全consumerが `consumer_offsets` に行を持った後は operator が archive/削除してよい。DBが唯一のresume元。`eventbus_05`・`eventbus_07` に記録済み。削除時の権限・バックアップの取扱いは未規定 | 導出案(owner承認待ち) / 2026-10-21 | 同上 |
| compat002 | C002-dec-3 | collision 扱い・completionマーカー・helper削除 | 決定 | 未決(4項目: 衝突時の挙動、完了marker、commit動作、`write_offset()`/`read_offset()` の削除)。`eventbus_05` に Open decisions として記録済み。import を削除すれば前3項目は不要になる。なお、importは自身ではcommitしないことを実測で確認した | 未決 / 2026-10-21 | 同上 |
| compat003 | C003-fact-1 | 12名の外部インポートなしの確認 | 事実 | 外部利用なし。確認範囲: リポジトリ、`/opt/llm/plugins`、`/opt/llm/bin`、`/opt/llm/start_agent.sh`、ホーム配下のスクリプト | owner+実測 / 2026-10-21 | Frozen済・実装済(`plans/done/20261020-235040_plan.md`、commit `44a0c37f5`) |
| compat003 | C003-dec-1 | 削除前の通知方針 | 決定 | 該当する通知方針なし。削除を承認 | owner / 2026-10-21 | 同上 |

## 未回答・承認待ちの項目(要約)

- **未決**: C001-dec-2、C001-dec-3、C002-dec-3。いずれも docs に Owner 付きの open decision として記録済み。
- **owner承認待ち**: C002-dec-1、C002-dec-2。文面は検証済みの挙動からの導出案で、owner の明示的な承認は未取得。
- **ADR-006**: import の記述を含む。削除issue(`rmoffimp`)の実施時に、ADR本文を編集するか決定が必要。

> 回答が記録された行に対応する計画書の Frozen化を進める。未回答行が残る計画書は Draft のまま維持する。(compat001・002 は未決行が open decision として docs に記録されることで、REQ-003 が許す形で Frozen 化・完了済み。)
