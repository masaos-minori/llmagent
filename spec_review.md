# 仕様変更案レビュー

対象ファイル: `00_llm_spec_tobe.md`
レビュー日: 2026-05-25

---

## 1. 現状仕様整理

### 実装済み（証跡あり）

| 機能 | 実装状況 | 実装日 |
|---|---|---|
| コンテキスト予算管理 | 完全実装 | 2026-05-20 |
| MCP サーバインストール補助 | 完全実装 | 2026-05-20 |
| 破壊的操作の承認フロー | 部分実装（仕様 1 のみ。マスキング・plan 連携は未実装） | 2026-05-19 |

### 未実装（提案段階）

| 機能 | 優先度 | 難易度 |
|---|---|---|
| `/plan` コマンド | 高 | 中 |
| `/diff` コマンド | 高 | 中 |
| `/rewind` | 中 | 低 |
| `/branch` | 中 | 低 |
| Skills 読み込み機構 | 高 | 高 |
| Subagents | 中 | 高 |
| Hooks | 中 | 中 |
| `/batch` | 中 | 高 |
| 危険パターン検出 | 高 | 高 |

---

## 2. Repository Evidence

### コンテキスト予算管理（実装済み）

- `scripts/agent_config.py:57` — `BUDGET_WARN_RATIO: float = 0.8`
- `scripts/agent_commands.py:44-78` — `_budget_breakdown(messages) -> dict[str, int]`（RAG: `[Reference documents]` / `[Additional context]` プレフィックスで識別）
- `scripts/agent_commands.py:510-540` — `_cmd_context()` に Budget breakdown 表示
- `scripts/agent_repl.py:612-625` — `_run_turn()` 内で `turn == 0` 時に budget チェック、`logger.warning` で内訳付き警告

### 破壊的操作の承認フロー（部分実装）

- `scripts/agent_repl.py:380-392` — `_check_approval(tool_name)` — `require_approval_tools` リストに含まれるツールで y/N 確認
- `scripts/agent_repl.py:451-467` — `_execute_all_tool_calls()` の pre-flight ループで `_check_approval` 呼び出し
- `config/agent.json:105-` — `require_approval_tools` に GitHub 書き込み系 9 ツール定義済み
- 引数マスキング (`mask_args`) — **未実装**（`agent_commands.py` に定義なし）
- `/plan` モードでの自動ブロック — **未実装**（`plan_mode` フラグなし）

### MCP サーバインストール補助（実装済み）

- `scripts/mcp_installer.py` 272 行 — ウィザード本体
- `scripts/agent_commands.py:276-394` — `_cmd_mcp()` / `_cmd_mcp_install()` / `_print_mcp_install_next_steps()`

### 未実装機能の証跡（不在確認）

```
grep -n "plan_mode|_cmd_plan|_cmd_diff|_cmd_branch|_cmd_rewind|_cmd_skill|_cmd_agent|_cmd_batch|_run_hook|_security_check|mask_args|modified_files|extra_system_prompt" scripts/agent_repl.py scripts/agent_commands.py
```

上記シンボルはいずれもコードベースに存在しない。

---

## 3. Affected Modules（変更案ごとの影響モジュール）

### `/plan` コマンド

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_plan(args)` 新規、dispatch テーブル更新 |
| `agent_repl.py` | `plan_mode` フラグ導入、`_execute_one_tool_call()` にブロック処理、`TOOL_DEFINITIONS` フィルタリング |
| `agent_context.py` | `plan_mode: bool` フィールド追加 |
| `config/agent.json` | destructive ツールリスト（`plan_blocked_tools`）追加 |

### `/diff` コマンド

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_diff(args)` 新規 |
| `agent_repl.py` | `_execute_one_tool_call()` で `modified_files` セット更新、スナップショット保存ロジック追加 |
| `agent_context.py` | `modified_files: set[str]` / `file_snapshots: dict[str, str]` フィールド追加 |

### `/rewind`

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_rewind(args)` 新規 |
| `agent_session.py` | `delete_turns(n)` 新規（複数ターンの DB 削除） |

### `/branch`

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_branch(args)` 新規 |
| `agent_session.py` | `fork_session(name)` 新規（セッションのコピーと新 session_id 生成） |

### Skills 読み込み機構

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_skill(args)` 新規 |
| `agent_repl.py` | `extra_system_prompt` 経路追加（一時システム追記） |
| `config/agent.json` | `skill_paths` キー追加 |
| `skills/<name>/SKILL.md` | 手順テンプレート定義 |

### Subagents

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_agent(args)` 新規 |
| `agent_repl.py` | `_call_llm_with_overrides(...)` 新規（一時設定で LLM 呼び出し） |
| `agents/<name>/AGENT.md` | ロール・プロンプト・ツール定義 |

### Hooks

| モジュール | 変更内容 |
|---|---|
| `agent_repl.py` | `_run_hook(event, payload)` 新規、hook ポイント挿入 |
| `agent_config.py` | `hooks_enabled` フラグ |
| `config/hooks.json` | イベント名 → スクリプトパスのマッピング（新規ファイル） |

### `/batch`

| モジュール | 変更内容 |
|---|---|
| `agent_commands.py` | `_cmd_batch(args)` 新規 |
| `batch_runner.py` | 新規モジュール（git worktree + asyncio 並列実行） |
| `config/agent.json` | `batch_concurrency` / `batch_worktree_root` キー追加 |
| `deploy/deploy.sh` | `batch_runner.py` のコピー行追加 |

### 危険パターン検出

| モジュール | 変更内容 |
|---|---|
| `agent_repl.py` | 書き込み系ツール成功後に `_security_check` 呼び出し |
| `agent_commands.py` | `_security_check(path)` 新規（正規表現 + AST + 軽量 LLM） |
| `config/agent.json` | `security_check_enabled` フラグ |
| `config/security_rules.json` | ルール定義（新規ファイル） |

---

## 4. Blast Radius（影響範囲）

### 高（コア実行パスを変更）

- **`/plan`**: `_execute_one_tool_call()` にブロック処理を挿入 — 全ツール呼び出しの実行パスに条件分岐が増える
- **`危険パターン検出`**: 書き込み系ツール成功後に毎回 `_security_check` を実行 — LLM 追加呼び出しを伴う場合、ターンレイテンシに影響
- **`Hooks`**: `_run_hook` をイベントポイントに挿入 — コマンド・ツール実行パス全体にサブプロセス起動が加わる
- **`/diff`**: `_execute_one_tool_call()` でのスナップショット保存 — ファイル書き込み頻度が高いセッションでメモリ増加

### 中（新機能追加のみ、既存パス無変化）

- **`/rewind`**: `agent_session.py` に DB 削除ロジック追加。誤操作時のデータロスリスクあり
- **`/branch`**: `agent_session.py` に DB コピーロジック追加。既存セッション読み取りのみ
- **`Skills`**: `extra_system_prompt` 経路追加 — システムプロンプトの文字数増加（コンテキスト消費）
- **`Subagents`**: `_call_llm_with_overrides` 追加 — 既存 LLM 呼び出しには無干渉

### 低（独立した新機能）

- **`/batch`**: 独立プロセス / worktree で動作。主 REPL には影響しない
- **`破壊的操作マスキング`**: ログ出力のみの変更。実行ロジック無干渉

---

## 5. Backward Compatibility

| 機能 | 後方互換性 |
|---|---|
| `/plan` | コマンド追加のみ。既存コマンドの動作変更なし |
| `/diff` | コマンド追加 + `AgentContext` フィールド追加（既存フィールドへの影響なし）|
| `/rewind` | コマンド追加のみ |
| `/branch` | コマンド追加のみ |
| `Skills` | `agent.json` への `skill_paths` キー追加（`ConfigLoader` は未知キーを無視するため互換あり）|
| `Subagents` | `agents/` ディレクトリ追加のみ |
| `Hooks` | `hooks_enabled: false` をデフォルトにすれば既存動作への影響なし |
| `/batch` | 新規モジュール追加のみ |
| `危険パターン検出` | `security_check_enabled: false` デフォルトで互換。有効化後は書き込み時に副作用発生 |
| `破壊的操作マスキング` | `masked_fields` をデフォルト空リストにすれば後方互換 |

全案とも**後方互換を維持可能**。ただし `Hooks` と `危険パターン検出` はデフォルト無効フラグが前提条件。

---

## 6. Migration（移行手順）

### `/plan`・`/diff`・`/rewind`・`/branch`

1. `agent_commands.py` に `_cmd_*` メソッドを追加
2. `dispatch()` の `async_cmds` または `prefix_cmds` へ登録
3. 必要に応じて `agent_context.py` / `agent_session.py` にフィールド・メソッドを追加
4. `bash deploy/deploy.sh` で本番環境へコピー
5. `docs/05_agent.md` のコマンド一覧を更新

### Skills 読み込み機構

1. `config/agent.json` に `skill_paths: ["skills/"]` 追加
2. `agent_commands.py` に `_cmd_skill()` 追加
3. 必要に応じて `agent_repl.py` に `extra_system_prompt` 経路追加
4. `skills/` ディレクトリと SKILL.md テンプレートを作成

### Hooks

1. `config/hooks.json` を新規作成（`hooks_enabled` デフォルト `false`）
2. `agent_repl.py` に `_run_hook()` を追加し、hook ポイントに挿入
3. `agent.json` に `hooks_enabled: false` を追加

### /batch

1. `batch_runner.py` を新規作成
2. `deploy/deploy.sh` にコピー行を追記
3. `agent_commands.py` に `_cmd_batch()` を追加

### 危険パターン検出

1. `config/security_rules.json` を新規作成
2. `agent.json` に `security_check_enabled: false` を追加
3. `agent_commands.py` に `_security_check()` を追加
4. `agent_repl.py` に `_execute_one_tool_call()` の呼び出し箇所を追加

### 破壊的操作マスキング（未実装部分）

1. `agent_commands.py` に `mask_args(args, masked_fields)` を追加
2. `_execute_one_tool_call()` の args 表示箇所で `mask_args` を呼び出す
3. `agent.json` に `masked_fields: ["file_content"]` を追加

---

## 7. Rollback Strategy（ロールバック方針）

### 即時ロールバック（コードレベル）

全機能とも `deploy/deploy.sh` で本番環境にコピーされる構成のため、旧バージョンの `scripts/` を再コピーするだけでロールバック可能。

```bash
# 旧スクリプトが git で管理されている前提
git checkout <prev-commit> -- scripts/
bash deploy/deploy.sh
rc-service llama-agent restart
```

### 機能フラグによるロールバック

- `Hooks`: `agent.json` の `hooks_enabled: false` で即時無効化
- `危険パターン検出`: `agent.json` の `security_check_enabled: false` で即時無効化
- 破壊的操作マスキング: `masked_fields: []` で無効化

### DB 操作を伴う機能のリスク

- **`/rewind`**: DB 削除は非可逆。削除前に session バックアップが必要
  - 対策: 削除実行前に y/N 確認を追加し、`sessions` / `messages` テーブルを別テーブルに退避するか、DB ファイルをコピーする
- **`/branch`**: session の INSERT のみ。ロールバックは対象 session の DELETE で可能

### インフラへの影響なし

MCP サーバ・OpenRC サービス・SQLite スキーマの変更を伴う機能はなく、デプロイ・ロールバックの複雑度は低い。

---

## 8. Validation Plan（検証計画）

### 単体テスト方針（`tests/`）

| 機能 | テスト対象 | モック対象 |
|---|---|---|
| `/plan` | `_cmd_plan()` トグル、`_execute_one_tool_call()` のブロック動作 | `input()` → `mocker.patch` |
| `/diff` | `modified_files` 追跡、`git diff` / 内部 diff 出力 | ファイル書き込みツール → `respx.mock` |
| `/rewind` | `delete_turns(n)` の DB 削除件数 | SQLite インメモリ DB |
| `/branch` | `fork_session()` の session コピー正確性 | SQLite インメモリ DB |
| `Skills` | SKILL.md ロード、システムプロンプト追記の内容 | ファイル I/O → `mocker.patch` |
| `Subagents` | `_call_llm_with_overrides()` のペイロード構成 | `respx.mock` |
| `Hooks` | `_run_hook()` のサブプロセス起動、失敗時の無視動作 | `pytest-subprocess` (`fake_process`) |
| `/batch` | タスク分割・並列実行・集約レポート | worktree → `mocker.patch` |
| `危険パターン検出` | 正規表現マッチ、AST 解析、LLM 呼び出しフォールバック | `respx.mock` |
| `破壊的操作マスキング` | `mask_args()` の各フィールドマスク | なし（純粋関数） |

### 統合テスト方針

- `pytest --timeout=10` で LLM 呼び出しを伴うテストのハング検知
- `pytest -n auto` で並列実行して環境依存の競合状態を検出
- `diff-cover coverage.xml --compare-branch=main --fail-under=90` で変更行カバレッジを確保

### 手動検証チェックリスト

- [ ] `/plan` モードで write ツールが実際にブロックされること
- [ ] `/diff` がセッション中の変更ファイルを正確に列挙すること
- [ ] `/rewind 2` が直前 2 ターンを DB から削除すること
- [ ] `/branch foo` でフォークされたセッションが独立して履歴を保持すること
- [ ] `/skill <name>` がシステムプロンプトに SKILL.md の内容を追記すること
- [ ] `hooks.json` に登録されたスクリプトがイベント発生時に実行されること
- [ ] `security_check_enabled: true` でサンプル危険パターンが検出されること

---

## 9. Deploy Impact（デプロイ影響）

### 全案共通

- `bash deploy/deploy.sh` で `scripts/` を `/opt/llm/scripts/` にコピー
- 新規モジュール（`batch_runner.py` 等）を追加した場合は `deploy.sh` のコピーリストに追記が必要
- OpenRC サービス再起動が必要: `rc-service llama-agent restart`
- SQLite スキーマ変更なし（全案）

### 新規 config ファイルを追加する案

| 機能 | 新規ファイル | 対応作業 |
|---|---|---|
| `Hooks` | `config/hooks.json` | `deploy.sh` にコピー行追加 |
| `危険パターン検出` | `config/security_rules.json` | `deploy.sh` にコピー行追加 |

### ダウンタイム

全案とも設定ファイル + スクリプトのコピー後にサービス再起動のみ。ダウンタイムは数秒以内。

---

## 10. Unknowns（不明点）

| 機能 | 不明点 |
|---|---|
| `/plan` | destructive ツールの定義範囲（`write_file` のみか、`delete_file` / `move_file` も含むか）|
| `/diff` | スナップショット保存の対象（書き込んだ全ファイルか、指定ディレクトリ配下のみか）|
| `/diff` | `git diff` が使えない環境での内部 diff の差分形式（unified diff か JSON か）|
| `/rewind` | ファイル変更の巻き戻しを行うか（履歴のみか、ファイルシステムも対象か）|
| `Skills` | システムプロンプトへの追記タイミング（起動時一括か、コマンド呼び出し時のみか）|
| `Subagents` | サブエージェントのセッション履歴を主セッションへ統合するか否か |
| `Hooks` | フック失敗（スクリプト終了コード != 0）時の主 REPL の動作（エラー停止か無視か）|
| `/batch` | git worktree の作業ブランチ戦略（main 分岐か current branch 分岐か）|
| `/batch` | タスクファイルのフォーマット仕様（Markdown セクション区切りか YAML か）|
| `危険パターン検出` | 軽量 LLM レビューで使用するモデル（chat / code のどちらか）|
| `危険パターン検出` | false positive の許容方針（警告のみか、書き込み自体をブロックするか）|
| `破壊的操作マスキング` | `masked_fields` の適用対象（全ツールか特定ツールのみか）|

---

## 11. Alternative Designs（代替設計）

### `/plan` コマンド

**案 A（提案通り）**: `plan_mode` フラグ + `TOOL_DEFINITIONS` フィルタリングでツール定義ごと LLM に送らない
**案 B**: ツール定義は送るが `_execute_one_tool_call()` で実行のみブロック（LLM は tool_call を発行するが実行されない）
**案 C**: 専用システムプロンプトに「ファイル操作を行わず計画のみ回答せよ」を追記し、ソフトコントロールに留める

差異: 案 A がもっとも強制力が高い（LLM がツールを知らないため誤呼び出しなし）。案 C は実装コスト最小だが LLM 依存でバイパスリスクあり。

### `/diff` コマンド

**案 A（提案通り）**: スナップショット保存（メモリ使用量が増加するが正確な差分を取得可能）
**案 B**: `git diff` のみに依存（git 管理下ファイルのみ対象。未追跡ファイルは不可）
**案 C**: ファイルパスのリストのみ記録し、差分は表示時に現在ファイルと比較（中間状態の差分は取得不可）

差異: 案 A は実装コスト中・メモリ中。案 B は実装コスト最小だが制約あり。案 C は案 A より軽量だが中間差分が消える。

### Skills 読み込み機構

**案 A（提案通り）**: `skills/<name>/SKILL.md` をシステムプロンプトに追記
**案 B**: SKILL.md の内容を初回ユーザーメッセージの先頭に埋め込む（system と history の分離を維持）
**案 C**: `/skill` を単なるユーザーメッセージのショートカット（スラッシュコマンドとして受け取り、LLM に直接渡す）

差異: 案 A は手順を LLM に確実に与えられるが system トークン増加。案 B はコンテキスト汚染が軽微。案 C は実装最小だが LLM の解釈に依存。

### Hooks

**案 A（提案通り）**: 外部スクリプト実行（`subprocess.run`）
**案 B**: Python callable を `config/hooks.json` ではなく `hooks.py` に定義（スクリプトパス不要、型安全）
**案 C**: Hooks 専用 MCP サーバに通知を送る（既存 MCP アーキテクチャと整合）

差異: 案 A は汎用性高いが subprocess の管理が必要。案 B はデプロイシンプルだが Python 以外のスクリプト不可。案 C は最も複雑。

### 危険パターン検出

**案 A（提案通り）**: 正規表現 + AST + 軽量 LLM の 3 段構成
**案 B**: `bandit` を subprocess 経由で呼び出す（既存ツールチェーンを再利用）
**案 C**: 警告のみで書き込み自体はブロックしない（false positive によるユーザー体験悪化を防ぐ）

差異: 案 A は独自ルールの柔軟性が高いが実装コスト最大。案 B は bandit 既存ルールに依存するが実装コスト最小。案 C は最も安全だが検知した問題を放置するリスクあり。

---

## 12. Risk Comparison（リスク比較）

| 機能 | 実装コスト | 実行時リスク | データロスリスク | テスト困難度 | 総合リスク |
|---|---|---|---|---|---|
| `/plan` | 中 | 低（既存ツール動作に影響なし） | なし | 低 | **低** |
| `/diff` | 中 | 中（スナップショット保存によるメモリ増加） | なし | 低 | **低〜中** |
| `/rewind` | 低 | 低 | **高**（DB 削除は非可逆） | 中 | **中** |
| `/branch` | 低 | 低 | 低 | 低 | **低** |
| `Skills` | 中 | 低 | なし | 低 | **低** |
| `Subagents` | 高 | 中（LLM 多重呼び出しによるコスト増） | なし | 高（LLM モック） | **高** |
| `Hooks` | 中 | **高**（外部スクリプトの暴走・エラーが主 REPL に伝播） | 低 | 高（subprocess） | **高** |
| `/batch` | 高 | **高**（worktree 管理・マージ衝突） | 中（worktree 残留） | 高 | **高** |
| `危険パターン検出` | 高 | 中（LLM 呼び出しがレイテンシに影響） | なし | 高（LLM モック） | **中〜高** |
| `破壊的操作マスキング` | 低 | なし | なし | 低 | **低** |

---

## 13. 最終判定

### 推奨案（実装を推進する）

#### 第一優先（早期着手）

1. **`/branch`（セッション分岐）**
   - 難易度低・データロスリスク低。`agent_session.py` への追加のみで完結。

2. **`/rewind`（巻き戻し）**
   - 難易度低。ただし DB 削除の非可逆性に対し、実行前に確認プロンプト + DB バックアップを実装することを条件とする。

3. **`/plan` コマンド**
   - 難易度中・リスク低。案 A（`TOOL_DEFINITIONS` フィルタリング）を採用。破壊的操作の承認フロー（実装済み）の `/plan` 連携未実装部分の補完にもなる。

4. **`/diff` コマンド**
   - 難易度中・リスク中。案 C（パスリスト記録 + 表示時比較）を採用することで、スナップショット保存のメモリリスクを回避しつつ、変更追跡を実現する。

5. **破壊的操作マスキング（未実装部分）**
   - コスト最小（`mask_args()` の追加のみ）。セキュリティ向上に直結。

6. **`Skills` 読み込み機構**
   - 優先度高・既存 Skills ディレクトリ（`skills/`）が存在する。案 B（ユーザーメッセージ先頭埋め込み）を採用することで system プロンプトのトークン増加を抑制。

#### 第二優先（時期を選んで着手）

7. **`危険パターン検出`**
   - 優先度高だが実装コスト高。まず案 B（`bandit` subprocess 呼び出し）で最小構成を実装し、独自ルールは段階追加とする。`security_check_enabled: false` デフォルトで本番影響なし。

---

### 非推奨案（現時点では着手しない）

8. **`Subagents`**
   - 実装コスト高・テスト困難度高。`Skills` 読み込み機構で大部分の要求を代替できる。専門エージェント委譲が本当に必要になった段階で再評価する。

9. **`Hooks`**
   - `_run_hook()` の挿入箇所が多く、外部スクリプト失敗時の主 REPL への伝播リスクが許容しがたい。設計上 `subprocess.run` のタイムアウト・エラーハンドリングを十全に実装しない限り、本番環境での採用は危険。Hooks の用途は `危険パターン検出` と `/diff` の組み合わせでほぼ代替可能。

10. **`/batch`**
    - 実装コスト高・worktree 管理の複雑性・マージ衝突リスクが高い。N100 (CPU のみ) の本環境では並列 LLM 呼び出しによるキューイング遅延が顕著になる可能性が高く、性能面でのメリットが得にくい。

---

### 採用理由サマリー

| 判定 | 機能 | 採用理由 |
|---|---|---|
| 推奨 | `/branch` | 実装コスト最小・リスク最小・履歴保護の安全弁として即効性高 |
| 推奨 | `/rewind` | 低コストで `/undo` の重大な機能不足を解消。DB バックアップを条件に安全化可能 |
| 推奨 | `/plan` | 破壊的操作防止の完成に直結。承認フロー（実装済み）との連携により安全性が飛躍的に向上 |
| 推奨 | `/diff` | 変更可視化による事故防止。案 C でメモリリスクを排除しつつ主要ニーズを満たせる |
| 推奨 | `破壊的操作マスキング` | 既存承認フローの補完。コスト最小・セキュリティ向上に直結 |
| 推奨 | `Skills` | 現在 Claude Code の skills/ として既に存在。agent 側の読み込み機構を加えるだけで再利用性が向上 |
| 条件付き推奨 | `危険パターン検出` | bandit 案で最小実装から開始し、段階的に拡充。デフォルト無効で安全に導入可能 |
| 非推奨 | `Subagents` | Skills で代替可能。実装コスト・テスト困難度が高すぎる |
| 非推奨 | `Hooks` | 外部スクリプト失敗時の REPL 安定性リスクが高く、本番環境での採用リスクが許容水準を超える |
| 非推奨 | `/batch` | 本環境（CPU のみ・N100）では並列 LLM 呼び出しの効果が薄く、worktree 管理の複雑性対比でコストが高い |
