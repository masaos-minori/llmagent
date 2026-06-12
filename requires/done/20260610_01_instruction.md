# DB モジュール改修指示書

### 1-1. 方針

* 後方互換性は **完全に考慮しない**
* 旧スキーマ・旧コードを救済する処理は **すべて削除**
* すべての処理は **fail-fast（異常時は即例外）**
* 「とりあえず動くための fallback」は **禁止**
* DB 操作は常に **整合性・明確性・再現性を優先**

***

### 1-2. 設計ルール

以下のルールを必ず守ること：

#### 設定

* 設定値が不正・不足の場合は即例外を投げる
* デフォルト値による救済は禁止

#### DB接続

* 接続確立に失敗した場合は必ず例外を投げる
* sqlite-vec は必要な場合のみロードする

#### トランザクション

* 書き込み処理はすべて明示的トランザクション内で実行する
* 暗黙 commit に依存しない

#### スキーマ

* スキーマは常に「最新形」
* migration / IF NOT EXISTS による救済は禁止
* schema\_version を使わないなら削除する

#### 例外

* except Exception: で握りつぶすコードは禁止
* 必ずログ出力＋再throw

#### 保守系処理

* ライブ DB を unsafe にコピーする処理は禁止
* 成否が曖昧になる戻り値は禁止

***

## 2. ファイル単位指示

***

## 2-1. `helper.py`

### 目的

SQLite接続管理の責務を「純粋な接続制御」に限定する

***

### High

* `_ensure_config()` を削除し、**DbConfig をコンストラクタで注入する設計へ変更**

* 設定ロード失敗時の warning 継続を禁止 → 必ず例外にする

* `open()` の挙動を修正：
  * sqlite-vec のロードは **オプション化**
  * session DB 操作ではロードしない

* 書き込み用 API を再設計：
  * `transaction()` context manager を追加
  * 書き込みは必ずこの中で実行する

* `assert conn is not None` をすべて削除し、
  * 未初期化時は RuntimeError を投げる

***

### Medium

* class変数キャッシュ（\_RAG\_PATH 等）を削除
* DB\_PATH property を廃止し、インスタンス変数化
* PRAGMA適用処理を関数に分離

***

### Low

* メソッド命名を snake\_case に統一（DB\_PATH → db\_path）
* fetchall の戻り型を明示
* logging の粒度を整理

***

## 2-2. `maintenance.py`

### 目的

運用処理を「安全かつ確実に結果が分かる」ものに再構成する

***

### High

* `VACUUM失敗でも success=True` を返す実装を削除
  * 失敗時は success=False にする

* DBローテーション処理を修正：
  * ファイルコピーによるバックアップは禁止
  * 一貫性のあるバックアップ方式に変更すること（checkpoint 等）

* `recover_corruption()` を汎用化：
  * rag 固定をやめ、DB対象を引数にする

* Config読み込み fallback（{}）を削除
  * 読み込み失敗は例外

***

### Medium

* purge\_old\_sessions のロジックを SQL ベースに書き換え
* dry\_run の action を明確化（would\_\* に変更）
* 関数群を `MaintenanceService` クラスに統合

***

### Low

* RetentionConfig の入力バリデーションを追加
* ログに DB ファイル名・件数を必ず含める

***

## 2-3. `store.py`

### 目的

CRUD層を「安全・一貫・副作用明示」にする

***

### High

* `get_embedding_dims()` の fallback を削除
  * 設定取得失敗時は例外

* `doc_upsert()` を UPSERT に置換
  * SELECT → UPDATE/INSERT の二段階を廃止

* `SQLiteMemoryDeleteStore` の部分成功を廃止
  * 1つでも失敗したら全体失敗にする

* commit責務を明確化：
  * 書き込みは transaction 内でしか呼べない設計に変更

***

### Medium

* 引数バリデーション追加（limit, k など）
* Protocol が必要か再評価し、不要なら削除
* 一覧APIにページングを追加

***

### Low

* dict生成の重複処理を削減（row\_factory活用）
* 命名統一（index → chunk\_index）
* docstringを簡潔化

***

## 2-4. `tool_results.py`

### 目的

ツール実行ログを「確実に保存される構造」にする

***

### High

* 例外握りつぶしを全面禁止：
  * store / get / list\_recent で例外を再throw

* list\_recent から full\_text を除外
  * summary のみ返すように変更

***

### Medium

* 保存件数制御（limit or TTL）を導入
* 引数を dataclass にまとめる
* session\_id の扱い方針（FK or 独立）を明確化

***

### Low

* 並び順仕様を明文化
* logging を統一

***

## 2-5. `config.py`

### 目的

設定責務を分離し、DB専用設定に特化させる

***

### High

* embed\_url を DbConfig から削除（別設定へ分離）
* sqlite\_vec\_so を必須条件から分離（ベクトル用設定へ）

***

### Medium

* build\_db\_config を廃止し、DIに変更
* Path型を使用する

***

### Low

* エラーメッセージに設定キー情報を含める
* 設定名称を整理

***

## 2-6. `create_schema.py`

### 目的

「最新スキーマを作成するだけのモジュール」にする

***

### High

* migration系コードをすべて削除：

  以下を削除すること：

  * `_RUN_MIGRATIONS`
  * `_RAG_MIGRATE_SQL`
  * `_SESSION_MIGRATE_SQL`
  * `_SAFE_MIGRATION_ERRORS`

* IF NOT EXISTS を削除する（必要に応じて）

* schema\_version を削除 or 正式運用にする

* `memories_vec` の dim 固定値を削除し、統一

* 旧スキーマ前提コードを完全削除

***

### Medium

* DDLテンプレートの string replace を廃止し構造化
* FTS トリガの整合性を確認（memories系）

***

### Low

* ログ内容の簡略化
* 不要なコメント削除（Phase表記など）

***

## 3. 明示的削除対象

以下は必ず削除すること：

* fallback系処理（すべて）
* silent failure（すべて）
* migration救済ロジック
* schema互換処理
* 「存在しないかもしれない前提」のコード
* 不整合を許容する分岐

***

## 4. 実装順序（AIはこの順で実行）

1. config.py の責務削減
2. helper.py の再設計（DI + transaction）
3. create\_schema.py の全面整理（migration削除）
4. store.py の安全化（UPSERT・例外化）
5. maintenance.py の安全化
6. tool\_results.py の例外整備
7. 全体テスト

***

## 5. 完了条件

以下を満たしたら完了とする：

* 不正設定時に必ず例外で停止する
* DB整合性エラーが黙殺されない
* すべての書き込みが transaction 内で実行される
* スキーマが単一の最新版のみ存在する
* fallback / silent failure がゼロ
