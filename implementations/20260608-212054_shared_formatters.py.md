# Implementation and Test Procedure: shared/formatters.py

## Goal
shared/formatters.py ファイルのテストを追加する。

## Scope
- 対象ファイル: shared/formatters.py
- カバレッジ: 26%
- 影響範囲: 中（2 か所からインポート）、8 コミット、1 人作者

## Assumptions
1. ファイルのカバレッジが 26% のため、テストを追加してカバレッジを向上させる
2. テストを追加することで、テスト環境の安定性が向上する可能性がある
3. テキスト整形関数が未テストのため、テストを追加する

## Implementation
### Target file
shared/formatters.py

### Procedure
1. テキスト整形関数の tests を追加
2. テストケースと関数の詳細分析を行う

### Method
- テストカバレッジを向上させるためのテストを作成

### Details
- 現在の shared/formatters.py はカバレッジが 26% で、テストを追加してカバレッジを向上させる
- カバレッジを向上させるためにテストを追加する

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Security | `bandit` | no HIGH unaddressed |
| Tests | `pytest` | all pass |
| Coverage | `diff-cover` | ≥ 90% on changed lines |
| Pre-commit | `pre-commit run --all-files` | pass |