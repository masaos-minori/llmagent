# 04_mcp_05_security_and_safety_model — Implementation Procedure

## Goal
MCPシステムのセキュリティモデルと安全機構を体系的に文書化する。許可リスト/拒否リスト、サイズ制限、タイムアウト、サンドボックス、fail-open/closed 方針を網羅する。

## Scope
- allowlist/denylist (allowed_dirs, allowed_repo_paths, db_allowlist, repo_allowlist, workflow_allowlist, command_allowlist)
- セキュリティフラグ (read_only, auth_token, protected_branches, path_denylist)
- ファイル/出力サイズ制限、タイムアウト、サンドボックスバックエンド
- fail-open vs fail-closed 方針; dry_run サポート; リスクティア分類

## Assumptions
- セキュリティ設定はサーバーごとの独立したコンフィグファイルで管理される
- fail-closed がデフォルト; 明示的に許可されない操作は拒否される

## Implementation

### Target file
`docs/04_mcp_05_security_and_safety_model.md`

### Procedure
- 許可チェック順序の概念図を示す
- 許可リスト/拒否リストを設定キー別テーブルで整理する（キー名・適用サーバー・型・デフォルト）
- サイズ/タイムアウト制限テーブル、リスクティア分類、fail-open/closed 方針、dry_run 動作を記載する

### Method
各サーバーの設定ドキュメントとソースコードからセキュリティ関連設定を横断的に収集し、このファイルに集約する。

### Details
- allowed_dirs: file-read/write/delete / パスプレフィックスマッチ
- repo_allowlist: github/git / org/repo 形式; db_allowlist: sqlite / DBファイルパス許可リスト
- command_allowlist: shell / 実行可能コマンド名; path_denylist: /etc, /sys 等デフォルト拒否
- リスクティア: 高=file-delete/shell, 中=file-write/github, 低=file-read/web-search
- auth_token: Bearer 検証; 未設定は認証なし（開発環境のみ許容）

## Validation plan
- 全許可リスト設定キーがテーブルに網羅されていることを確認する
- リスクティア分類が運用ポリシーと整合することをレビューする
- fail-closed の動作をテストケースで検証する
