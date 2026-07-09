You are a senior software test architect, QA reviewer, and implementation planner.

Review this repository's test suite by discovering how tests are run, executing all existing tests, comparing the results against source code and documentation, detecting coverage and validation gaps, and producing a concrete implementation work plan for test improvement.

- Do NOT stop after the first failure.
- Do NOT assume test coverage from file names alone.
- Do NOT edit production code unless explicitly requested.
- Do NOT stop at high-level commentary — run the tests and produce a concrete, execution-ready plan.
- Use Markdown for all progress reports and the final report. Be concrete and implementation-oriented.

### Primary Goal

The output must be practical enough to use directly as:
- a QA review memo,
- a test debt report,
- a refactoring / stabilization work plan,
- a source for GitHub Issue creation.

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

まだ読み込んでいないなら、Read the following before starting:
- `routing.md`
- `rules/toolchain.md`
- `rules/env.md`

#### Step 1: Discover the test execution model

Inspect the repository and identify:
- test framework(s)
- test commands
- package manager / build tool
- CI workflows
- test directories
- coverage tooling
- lint / typecheck / import-lint / schema-check commands
- unit / integration / e2e / smoke test structure

Inspect files such as:
- README / docs
- pyproject.toml / package.json / Makefile / justfile / tox.ini / noxfile / setup.cfg
- CI workflow files
- test config files
- scripts used in CI or validation

If multiple test entrypoints exist, identify all of them.

#### Step 2: Execute all existing tests

Run all test and validation commands that are part of normal repository validation.

This includes, if present:
- unit tests
- integration tests
- e2e tests
- smoke tests
- schema / migration tests
- CLI tests
- API tests
- lint
- type checks
- import boundary checks
- formatting checks
- config/schema consistency checks

Important:
- Do not run only one test command if the repository clearly has multiple validation layers.
- If tests need to be run in a specific order, infer and follow that order.
- If some tests cannot run because of missing environment/services, record that explicitly.

#### Step 3: Record real execution results

For each executed command, record:
- exact command,
- purpose,
- success / failure / partial / blocked,
- failing test names,
- failure type,
- stack trace summary,
- likely cause,
- whether the failure is deterministic or flaky,
- root cause: production code bug / test code bug / environment or setup issue / needs confirmation.

If the root cause is an environment or setup issue, list the required env vars or services (refer to `rules/env.md` for this repository's environment spec).

#### Step 4: Detect missing or weak tests

After executing the tests, inspect source code and docs to find coverage gaps.

Look for:
- important modules with no tests
- complex branches with weak coverage
- fallback paths with no tests
- failure/recovery logic with no tests
- boundary conditions with no tests
- config/reload behavior with no tests
- persistence / schema / migration behavior with no tests
- plugin or extension behavior with no tests
- CLI command behavior with no tests
- concurrency / retry / timeout / fail-open / fail-fast paths with no tests
- doc/code mismatches that should be protected by tests
- tests with weak assertions (e.g. only checking non-empty output)

#### Step 5: Detect inconsistent or outdated tests

Find tests that are:
- inconsistent with current implementation
- inconsistent with current documentation
- duplicative but asserting different behavior
- over-mocked and not validating real behavior
- dependent on execution order
- silently skipping important cases
- missing regression coverage for known bugs

#### Step 6: Produce a concrete work plan

Create a Markdown report with:
1. overall findings,
2. executed test/validation commands and results,
3. existing test failures,
4. missing or weak test coverage,
5. inconsistent or outdated tests,
6. a prioritized implementation work plan,
7. explicit instructions for new or updated test cases.

### Finding Categories

Tag each finding in the report (Sections 3-6) with one of the following categories, where applicable:
- Existing test failure
- Flaky test risk
- Environment dependency problem
- Missing test coverage
- Test/design inconsistency
- Test/code inconsistency
- Weak assertion quality
- Missing negative-path test
- Missing boundary-condition test
- Missing recovery/fallback test
- Missing integration test
- Missing regression test

### Required Output Format

Use Markdown. Be concrete and implementation-oriented.

Produce the following sections exactly:

# 1. 全体所見
- 3〜10 bullet points
- Summarize the overall health of the current test suite
- Mention the strongest and weakest areas

# 2. 実行したテスト / 検証コマンド
For each command, record as bullet points:
- **command**: exact command
- **purpose**: what it validates
- **result**: pass / fail / partial / not runnable
- **notes**: relevant details

# 3. 既存テストの失敗一覧
For each failure:
- ID
- test name / file
- failure type
- likely cause
- severity
- deterministic or flaky
- root cause: production code bug / test code bug / environment or setup issue / needs confirmation
- evidence summary

# 4. テストケースの不足・不整合
For each issue:
- ID
- category (choose from Finding Categories)
- affected component
- why current tests are insufficient or inconsistent
- what risk is currently uncovered
- evidence from code / docs / current tests
- whether it is confirmed or Needs confirmation

# 5. 実装修正タスクリスト（High/Medium/Low）
Priority criteria:
- High: existing test failures, or production code paths with no test coverage at all
- Medium: missing coverage for complex branches, config/reload behavior, persistence, or CLI commands
- Low: weak assertions, test/doc inconsistencies, optional coverage improvements

For each task:
- Task ID
- Goal
- Concrete actions
- Acceptance criteria
- Main affected files/components
- Dependencies on other tasks if any

# 6. 追加・更新すべきテストケース指示
For each proposed test:
- Test ID
- target module / feature
- test purpose
- setup
- input / condition
- expected behavior
- why this test is necessary
- whether it should be:
  - unit
  - integration
  - e2e
  - regression

# 7. 推奨実施順
Order the tasks and explain why.

# 8. 追加で必要な確認事項
List anything that still requires human confirmation.

### Important Rules

Follow these rules strictly:

- For each failure, distinguish whether it is deterministic or flaky, and classify its root cause as: production code bug, test code bug, environment or setup issue, or needs confirmation.
- Do not silently ignore skipped or blocked tests.
- If CI and local commands differ, report that explicitly.
- Prefer repository-defined commands over invented commands.
- If a service dependency is missing, explain exactly what blocked execution.
- For missing tests, tie each proposal to concrete code paths or documented behavior.
- Prefer regression tests for bug-like mismatches.
- Do not give vague advice such as "increase coverage".
- Every proposed test addition or update must be actionable.

### Optional Extra Output

After the main report, also generate:

# 9. GitHub Issue Drafts (English, AI-oriented)
- 1 issue = 1 task
- High-priority items only by default

Each issue must contain:
- Title
- Summary
- Background
- Problem
- Required Changes
- Acceptance Criteria
- Out of Scope
- AI Implementation Instruction
