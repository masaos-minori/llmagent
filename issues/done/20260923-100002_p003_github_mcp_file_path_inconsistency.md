# P0-003: GitHub MCP ドキュメントのファイルパス不一致 — `models_config.py` は存在しない

## Priority
High

## Summary
`docs/04_mcp_04_01_web-search-file-read-github.md:173` が参照する `scripts/mcp_servers/github/models_config.py` は存在しない。実際のファイルは `github_models_config.py` であり、このパス不一致は実装者の混乱を招く。

## Background
GitHub MCP サーバーのファイル構成は `scripts/mcp_servers/github/` ディレクトリにあり、ファイル命名規則は `github_*` プレフィックスを使用している。`models_config.py` という名前のファイルは存在せず、代わりに `github_models_config.py` が同じ役割を果たしている。

## Problem
`docs/04_mcp_04_01_web-search-file-read-github.md:173` で `scripts/mcp_servers/github/models_config.py` を参照しているが、このファイルは存在しない。実際には `github_models_config.py` が例外定義（`GitHubNotFoundError`, `GitHubAuthorizationError` など）をエクスポートしている。

## Reason for Change
ドキュメントの参照パスが実態と一致しておらず、開発者が間違ったファイルを探す可能性がある。また、例外定義の実装場所の誤解は、エラーハンドリングのカスタマイズ時に問題を引き起こす。

## Implementation Intent
1. `docs/04_mcp_04_01_web-search-file-read-github.md:173` の参照を `github_models_config.py` に更新
2. 同ファイル内で `models_config.py` への参照が他にあるか確認し、全て修正する
3. `scripts/mcp_servers/github/` のファイル一覧を確認し、他のドキュメントとの整合性を取る

## Target Files or Areas
- `docs/04_mcp_04_01_web-search-file-read-github.md`
- `scripts/mcp_servers/github/github_models_config.py`

## Required Changes
- `docs/04_mcp_04_01_web-search-file-read-github.md:173` のパスを `github_models_config.py` に更新
- 同ファイル内の他の `models_config.py` 参照の確認と修正

## Constraints
- ファイルのリネームを行ってはならない
- 既存のインポート構造を変更してはならない

## Acceptance Criteria
- [ ] `docs/04_mcp_04_01_web-search-file-read-github.md` に `models_config.py` の参照が残っていない
- [ ] 全ての参照が `scripts/mcp_servers/github/` 配下の実際のファイル名を指している
- [ ] `uv run python tools/check_docs_consistency.py --domain mcp` で関連警告が減っている

## Testing Expectations
- ドキュメントの一貫性チェックツールで警告がないことを確認
- GitHub MCP サーバーの起動テスト（オプション）

## Documentation Impact
- `docs/04_mcp_04_01_web-search-file-read-github.md` の更新が必要
- 他の MCP ドキュメントで同種のパス不一致が残っていないか確認すべき

## Out of Scope
- GitHub MCP サーバーのファイルリネーム
- インポート構造の変更
- ドキュメント外のコード修正

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- `docs/04_mcp_04_01_web-search-file-read-github.md` のみ修正する
- `models_config.py` の参照を `github_models_config.py` に置き換える
- ファイルのリネームやインポート構造の変更は行わない

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-100002
- **Related target files**: docs/04_mcp_04_01_web-search-file-read-github.md, scripts/mcp_servers/github/github_models_config.py
