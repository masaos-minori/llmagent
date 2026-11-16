# Add compatibility-regression guards for removed workflow defaults and lease-less attempts

## Priority
Medium

## Summary
Extend `tools/check_compat_shims.py` so that the workflow-definition defaults and the lease-less attempt path removed by the sibling issues cannot silently return. The existing guards for the deleted `db.store` and `eventbus.db` facades stay as they are.

## Background
Source: `memo-issue.md` Issue 4 (items M-05, L-01), re-verified against current source.

- Explicit in code: `tools/check_compat_shims.py` already forbids `from db.store import`, `from eventbus.db import`, `import eventbus.db`, and `from eventbus import db` (the `compatrm003` pattern group), and both `scripts/db/store.py` and `scripts/eventbus/db.py` are absent. The L-01 part of the memo (protect the `db.store` facade) is therefore already satisfied for imports.
- Explicit in code: the checker is wired into `.pre-commit-config.yaml` (`check-compat-shims`, running `--check-removed-names --check-doc-symbols`) and into `.github/workflows/backward-compat-check.yml` with the same flags.
- Explicit in code: `tools/check_compat_shims.py` uses regex pattern tables and a few `ast`-based checks (for example `check_mcp_health_reexport_import()` and `check_gateless_discovery_construction()`); it has no check for dataclass field defaults, function-parameter defaults, or nullable DDL columns.
- Tests for the checker live in `tests/tools/test_check_compat_shims.py`, `tests/tools/test_compat_checker_precompiled.py`, and `tests/tools/test_no_compatibility_policy_gate.py`.
- The surfaces to protect are defined by the workflow-definition and lease issues listed under Dependencies. Whether a regex-only rule can catch a changed default or optional parameter is `Needs confirmation`; the memo asks for semantic or AST-based checks where practical.

## Problem
The checker detects removed names, not removed behavior. Optional `retry_on`, default `WorkflowDef.stages` and `retry_policy`, an optional `lease_duration_sec`, and nullable lease columns can all come back while every symbol name stays unchanged, so no current rule would fail. The "legacy age threshold" wording can also reappear in current-tense documentation without a rule to flag it.

## Reason for Change
Without enforcement, the one-time cleanup in the sibling issues relies on manual review to stay in place. The guards add value only after those issues land, so this is not time-sensitive on its own; it is maintainability and regression-prevention work.

## Implementation Intent
Convert the cleanup decisions into repository invariants that fail locally and in CI with a specific diagnostic. Prefer small `ast`-based rules over regexes for signature and default checks, and a source check for the canonical DDL. Keep historical references legal when clearly marked removed or historical. Use the existing exception mechanism sparingly; no permanent production exception is added for any removed behavior.

## Target Files or Areas
- `tools/check_compat_shims.py`
- `tools/_compat_leftover_phrases.py`
- `tools/compat_exceptions.toml`
- `tests/tools/test_check_compat_shims.py`
- `.pre-commit-config.yaml` (confirm the hook's `files` filter covers the files the new rules read)
- `.github/workflows/backward-compat-check.yml`
- `tools/TOOL_DESCRIPTIONS.md` (if the tool's described behavior changes)

## Required Changes
- Add rules that fail when: `RetryPolicy.retry_on` has a default; `WorkflowDef.stages` or `WorkflowDef.retry_policy` has a default or default factory; the attempt writer or its `StateStore` facade accepts an optional or defaulted `lease_duration_sec`.
- Add a check that the canonical `attempts` DDL does not declare `owner_id` or `lease_expires_at` nullable.
- Add a documentation check for current-tense `legacy age threshold` wording, with an allowance for text marked `removed`, `historical`, or `withdrawn`.
- Keep the existing `db.store` and `eventbus.db` prohibitions unchanged.
- Add tests for every new rule: a positive case (reintroduction fails), a negative case (current code passes), and an allowed historical reference.
- Confirm that the pre-commit hook's file filter and the CI path filter cover every file the new rules inspect, and extend them if not.
- Update `tools/TOOL_DESCRIPTIONS.md` if the described behavior changes.

## Constraints
- Must run after the workflow-definition and lease issues land; the new rules would fail on current source otherwise.
- Follow `routing.md` "Adding a new tool" validation for `tools/` changes (ruff, mypy, bandit, a smoke run against live repository data, tool-description sync).
- The checker is a `repo_scan` test target: run `uv run pytest -m repo_scan` for it (`rules/toolchain.md` section 6).
- Exceptions must stay limited, owned, justified, and time-bounded.
- Keep `tools/check_module_size.py` limits in mind; `tools/check_compat_shims.py` may already be near its baseline size, so a new helper module may be needed (`Needs confirmation`).

## Acceptance Criteria
- [ ] Reintroducing a default on `RetryPolicy.retry_on`, `WorkflowDef.stages`, or `WorkflowDef.retry_policy` fails the checker with a specific diagnostic.
- [ ] Making `lease_duration_sec` optional or defaulted in the attempt writer or facade fails the checker.
- [ ] Making either canonical lease column nullable fails the checker or a schema test.
- [ ] Current-tense `legacy age threshold` wording in `docs/` fails the checker; text marked historical does not.
- [ ] The existing `db.store` and `eventbus.db` prohibitions still fail on a reintroduced import.
- [ ] Each new rule has positive, negative, and allowed-historical test cases.
- [ ] The pre-commit hook and the CI job run the checker mode that includes the new rules.

## Testing Expectations
- Unit tests in `tests/tools/test_check_compat_shims.py` using isolated fixtures that intentionally reintroduce each prohibited pattern.
- Run `uv run pytest tests/tools -v` and `uv run pytest -m repo_scan -v`.
- Run `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` against the live repository and confirm it passes after the sibling issues.
- Run `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`, and the tool validation steps in `routing.md`.
- Confirm by inspection that `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` invoke the checker with the new rules enabled.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` if behavior changes. If `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` describes the facade prohibition and the checker, keep it consistent; whether it needs any change is `Needs confirmation`.

## Out of Scope
- Changing the workflow definition, lease writer, schema, or documentation (sibling issues).
- Re-adding or altering the `db.store` and `eventbus.db` rules.
- The EventBus facade question: `scripts/eventbus/db.py` is already deleted and guarded.
- Broad refactoring of `tools/check_compat_shims.py`.

## Dependencies
- Depends on `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`, `issues/20261116-114834_compat002_mandatory-attempt-leases.md`, and `issues/20261116-114912_compat003_workflow-lease-docs-runbook.md` (the rules enforce the end state those issues create).
- Sibling check: no other open issue or in-flight plan touches `tools/check_compat_shims.py`.

## Unresolved Questions
- Can the default and optional-parameter checks be expressed robustly with `ast` against the model and writer definitions, or is a narrow pattern rule enough? `Needs confirmation`; decide at plan time.
- Does the checker's file-size baseline force a new module? `Needs confirmation`.
- Whether the doc check for the legacy threshold belongs in `tools/_compat_leftover_phrases.py` or a separate documentation checker: `不明`.

## AI Implementation Instruction
Change only the checker, its rule modules, its tests, the pre-commit and CI wiring if needed, and the tool description. Do not touch the existing `db.store` and `eventbus.db` rules. Do not add permanent exceptions. Keep rules specific enough that current code passes without exceptions. Stop and report if a rule cannot be made precise without exceptions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261116-114953
- **Related target files**: `tools/check_compat_shims.py`, `tools/_compat_leftover_phrases.py`, `tools/compat_exceptions.toml`, `tests/tools/test_check_compat_shims.py`, `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`, `tools/TOOL_DESCRIPTIONS.md`
