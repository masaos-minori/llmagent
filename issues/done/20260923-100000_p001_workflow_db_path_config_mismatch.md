# P0-001: `workflow_db_path` の設定値不一致 — agent.toml にキーが存在しない

## Priority
High

## Summary
`docs/02_deployment.md` が記載する `workflow.sqlite` の Config key `workflow_db_path` は `config/agent.toml` に存在せず、Pythonレベルのデフォルト値に依存している。本文と自動生成テーブルの情報が矛盾しており、デプロイメント手順の実行者が誤った設定を期待する可能性がある。

## Background
`docs/02_deployment.md:227` では `workflow.sqlite` の Config key を `workflow_db_path` と記載し、`docs/02_deployment.md:277` の自動生成テーブルでは `No (Python-level default)` と表示されている。両者の間に矛盾がある。`scripts/db/config.py` の `DbConfig` クラスが Pythonレベルのデフォルト値を提供しているが、この動作はドキュメントで明確に説明されていない。

## Problem
デプロイメント手順を実行する開発者が `workflow_db_path` キーを `agent.toml` に追加しようとする可能性があり、実際には不要な設定である。また、自動生成テーブルの「No」表示が意図的に「Python-level default」であることを示していないため、混乱の原因となる。

## Reason for Change
ドキュメントと実装の設定値の乖離により、デプロイメント手順の信頼性が損なわれている。実行時にデフォルト値が使われることは確認済みだが、そのことを明示的に文書化し、自動生成テーブルの表示も改善する必要がある。

## Implementation Intent
1. `docs/02_deployment.md` の本文（227行目付近）で、`workflow_db_path` が `agent.toml` に存在しない理由を明記する
2. 自動生成テーブル（277行目付近）の表示を改善し、「No (Python-level default)」から「No — falls back to DbConfig default」など、より明確な表現に変更する
3. 自動生成スクリプト `tools/generate_reference_table.py --type deployment` の出力ロジックを確認し、Python-level default のケースでも明確に表示されるようにする

## Target Files or Areas
- `docs/02_deployment.md`
- `scripts/db/config.py`
- `config/agent.toml`
- `tools/generate_reference_table.py --type deployment`

## Required Changes
- `docs/02_deployment.md:227` で `workflow_db_path` が `agent.toml` に存在しない旨を明記
- `docs/02_deployment.md:277` の自動生成テーブルの表示を改善
- 必要に応じて `tools/generate_reference_table.py --type deployment` の出力ロジックを修正

## Constraints
- Pythonレベルのデフォルト値の動作を変更してはならない
- 既存のデプロイメント手順の互換性を保つこと

## Acceptance Criteria
- [ ] `docs/02_deployment.md` の本文で `workflow_db_path` が `agent.toml` に存在しない理由が明記されている
- [ ] 自動生成テーブルで Python-level default のケースが明確に表示されている
- [ ] `uv run python tools/check_docs_consistency.py --domain deployment` で関連警告が減っている

## Testing Expectations
- ドキュメントの一貫性チェックツールで警告がないことを確認
- デプロイメント手順の手動検証

## Documentation Impact
- `docs/02_deployment.md` の更新が必要
- 自動生成テーブルの出力形式の変更があれば、他の参照ドキュメントにも影響の可能性

## Out of Scope
- `workflow_db_path` キーを `agent.toml` に追加すること
- Pythonレベルのデフォルト値の変更

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- `docs/02_deployment.md` の本文と自動生成テーブルの両方を修正する
- Pythonレベルのデフォルト値の動作を変更しない
- 自動生成テーブルの表示を改善するには `tools/generate_reference_table.py --type deployment` のロジック変更が必要な場合がある

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-100000
- **Related target files**: docs/02_deployment.md, scripts/db/config.py, config/agent.toml, tools/generate_reference_table.py --type deployment
