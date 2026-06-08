# Implementation and Test Procedure: scripts/agent/context_detection.py

## Goal
scripts/agent/context_detection.py ファイルを削除または再統合し、関連する deploy.sh の更新を行う。

## Scope
- 削除対象ファイル: scripts/agent/context_detection.py
- 関連ファイル: deploy/deploy.sh (cp コマンドの削除)
- 影響範囲: 0 コミット、1 人作者、低影響

## Assumptions
1. このファイルは参照されていない（カバレッジ 0%）
2. 関連する deploy.sh の更新が必要
3. ファイルが存在することを確認する
4. 日本語文字列リテラルがあるため、再統合の可能性も考慮

## Implementation
### Target file
scripts/agent/context_detection.py

### Procedure
1. scripts/agent/context_detection.py を削除または使用箇所に再統合
2. deploy/deploy.sh から該当の cp 行を削除（再統合の場合は不要）
3. 関連するテストを確認し、必要に応じて更新

### Method
- ファイル削除または再統合と関連ファイルの更新を行う
- 削除前にファイルの存在を確認し、影響範囲を評価する

### Details
- このファイルは参照元ゼロでカバレッジ 0% のため、安全に削除可能
- 日本語文字列リテラルが含まれているため、使用箇所に再統合する可能性もある
- deploy/deploy.sh から cp 行も同時に削除する必要がある（File Split Rule 参照）
- 削除後、関連するテストが正常に動作することを確認

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