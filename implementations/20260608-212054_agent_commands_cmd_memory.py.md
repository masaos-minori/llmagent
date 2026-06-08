# Implementation and Test Procedure: agent/commands/cmd_memory.py

## Goal
agent/commands/cmd_memory.py ファイルの characterization tests を追加し、リファクタリングを行う。

## Scope
- 対象ファイル: agent/commands/cmd_memory.py
- カバレッジ: 41%
- 影響範囲: 高（3 か所からインポート）、12 コミット、1 人作者

## Assumptions
1. _memory_list 関数の複雑度が高いため、テストを追加してリファクタリングの準備をする
2. カバレッジが 41% のため、characterization tests を追加してカバレッジを向上させる
3. characterization tests を追加する

## Implementation
### Target file
agent/commands/cmd_memory.py

### Procedure
1. _memory_list 関数の characterization tests を追加
2. _memory_list 関数のリファクタリングを計画
3. テストケースと関数の詳細分析を行う

### Method
- テストカバレッジを向上させるための characterization tests を作成
- 関数のサブロジックを抽出し、よりシンプルな構造にする

### Details
- 現在の _memory_list 関数はカバレッジが 41% で、テストを追加してリファクタリングの準備をする
- カバレッジを向上させるために characterization tests を追加する
- テスト作成方法: tests/conftest.py の _make_ctx() ヘルパーを使い、モック AgentContext で各スラッシュコマンドを呼び出す

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