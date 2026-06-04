[tasks]
Show progress as you work.
以下の内容を実行

1. `02_implement_plan.md` に基づき、実装手順をステップ単位で作成
 - `routing.md` を経由し実装対象機能の情報を取得

2. 各ステップの実証内容が実装済かどうか、正しく実装されているかどうかを確認
 - `rules/coding.md` : coding conventions and prohibited patterns
 - `rules/toolchain.md` : validation sequence (format → lint → type → arch → security → test → coverage)

3. 未実装の機能を実装し、テスト実施
 - `rules/toolchain.md` : validation sequence (format → lint → type → arch → security → test → coverage)
 - `skills/python-lint-typecheck/SKILL.md` : lint, ruff, mypy, pyright, type error, CI, pre-commit
 - `skills/python-debug-root-cause/SKILL.md` : debug, error, exception, crash, trace, log, slow, hang
 - `skills/python-test-and-fix/SKILL.md` : Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression

4. 実装結果をファイル単位でレポート

5. 実装により更新されたファイルの仕様を `docs/*.md` に反映
