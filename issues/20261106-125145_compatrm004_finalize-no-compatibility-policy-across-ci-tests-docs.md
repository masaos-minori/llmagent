# Finalize the no-compatibility policy across CI, tests, documentation, and runbooks

## Priority
Medium

## Summary
After the implementation issues are complete, remove production compatibility exceptions, add blocking checks for every deleted symbol and path, rewrite active documentation for the current-only policy, and restructure regression tests around rejection rather than migration. Checker configuration, manifest cleanup, CI and pre-commit enforcement, documentation cleanup, runbook updates, and final regression-test alignment are one issue because they all depend on the final implementation state.

## Background
Initiative issue M-2 of `memo-issue.md`. Verified 2026-11-06: the checker is `tools/check_compat_shims.py` with `--check-removed-names`, `--check-doc-symbols`, and `--allowlist`; its exceptions live in `tools/compat_exceptions.toml` (which names `mcp-00-document-guide`, `symbol_stage_allowance`, and `check-compat-shims-source`); pre-commit runs it from `.pre-commit-config.yaml` and `.github/workflows/backward-compat-check.yml` runs it in CI; `docs/22_mcp/mcp_00_document-guide.md` and `docs/22_mcp/mcp_07_tool_schema_export_policy.md` exist; `scripts/db/workflow_schema.py` no longer exists. The manifest mixes production compatibility exceptions, migration-document exceptions, test fixtures, negative test data, and documentation symbol allowances, and active documentation still contains migration history and compatibility terminology.

## Problem
If code is removed without updating these controls, deleted behavior can be reintroduced or documentation can keep promising unsupported upgrade paths; deleting every fixture reference would weaken the tests that intentionally detect removed names.

## Reason for Change
One enforceable policy needs the exceptions, the checks, the documentation, and the tests to agree.

## Implementation Intent
Create one enforceable policy: production code has no backward-compatibility or migration exceptions; active documentation describes only the current supported schema and APIs; history stays in version control, not in active specifications; negative tests may mention deleted names only in narrowly scoped test data; CI and pre-commit reject reintroduction of deleted symbols, modules, import paths, or migration claims.

## Target Files or Areas
`tools/check_compat_shims.py`, `tools/compat_exceptions.toml`, `tests/tools/test_check_compat_shims.py`, `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml` and other CI workflow files, `pyproject.toml`, the task-runner configuration if one exists, the active documentation tree (including `docs/22_mcp/mcp_00_document-guide.md`, `docs/22_mcp/mcp_07_tool_schema_export_policy.md`, and the database documents), the database operations runbook, `tests/db/test_create_schema.py`, and the Workflow database startup and rejection tests.

## Required Changes
Clean the compatibility manifest:
- Remove production migration and compatibility exceptions after their source causes are fixed, including entries such as `mcp-00-document-guide`, `mcp-07-tool-schema-export-policy`, `db-03-migration-and-scaling`, and `check-compat-shims-source` once the associated content is corrected.
- Review every fixture-category entry and keep only narrowly scoped negative-test fixtures that verify removed-name detection; move test-only reset hooks out of the production exception model; move `symbol_stage_allowance` into dedicated configuration if it remains necessary; prefer test-data-directory or exact-pattern exclusions over whole-file allowlisting.

Add blocking checks that reject reintroduction of at least: `_TOKEN_PRINCIPAL_MAP`, `_populate_token_maps`, `principal_map`, `verify_backup_by_path`, `shared.db_migrations`, `db.migrations_workflow`, `eventbus.migrations`, `eventbus.migrate`, `schema_migrations`, `from db.store import`, `import db.store`, `from eventbus.db import`, `import eventbus.db`, and active documentation that claims automatic migration, registered migration paths, or legacy database support.

Rewrite active documentation: remove descriptions of backward-compatible APIs and aliases, re-export stubs, legacy database support, migration registries, ledgers, CLI, dry-run, resume, and row preservation, lower-but-registered versions, `_TOKEN_PRINCIPAL_MAP`, `verify_backup_by_path()`, `schema_migrations`, `dbmig001`, the `_MCP_TOOLS` to `TOOL_LIST` migration policy, and the deleted `workflow_schema.py` entry point. Add the current policy: only the current schema is supported; no automatic migration or version stamping; schema mismatch is fail closed; operators may archive an incompatible database and must recreate it manually; no data-transfer facility; removed APIs and import aliases are unsupported; an archive is not a migration source.

Restructure tests: delete migration-success tests; add legacy Workflow and EventBus database rejection, existing unversioned database rejection, and current-version malformed database rejection tests with a no-mutation check; verify fresh current-schema creation, that `schema_migrations` is absent, `AuthzGeneration`-only authentication state, mandatory `consumer_id` for NACK, removed import-path rejection, and that rotation, archive, and recovery stay operational.

Align automation: make CI and pre-commit invoke the same checker options, keep the checker blocking for production findings, and add self-tests for true positives and historical-text false positives.

## Constraints
The common policy of the initiative applies:

Common policy (shared by all four issues of this initiative):

1. Support only the current database schema, API, import path, and authentication model.
2. Do not provide automatic database migration, version stamping, compatibility aliases, re-export facades, or deprecated call signatures.
3. Reject incompatible existing databases before mutation.
4. Do not automatically delete an incompatible database.
5. Permit an operator to archive an incompatible database and recreate it manually.
6. Preserve rotation, archive validation, and supported corruption recovery: they protect current data and are not backward-compatibility features.
7. Prevent deleted symbols, modules, imports, and specifications from being reintroduced through CI and pre-commit checks.

Do not add compatibility exceptions without a separate approved policy change. A change to `tools/check_compat_shims.py` follows `routing.md` "Adding a new tool".

## Acceptance Criteria
- [ ] Production compatibility and migration exceptions are zero; fixture allowances and documentation symbol allowances are configured separately from the production policy.
- [ ] Deleted names, modules, and imports fail CI when reintroduced.
- [ ] CI and pre-commit use the same blocking checker options.
- [ ] Active documentation contains no supported backward-compatibility or migration behavior.
- [ ] Tests no longer expect legacy data to be upgraded or preserved; rejection tests verify that incompatible database files remain unchanged.
- [ ] Current-schema creation and startup tests pass; rotation, archive, and recovery regression tests pass.
- [ ] Code, tests, documentation, CI, and runbooks describe one consistent current-only policy.
- [ ] Initiative completion gate: the four issues of the backward-compatibility removal initiative are closed, legacy databases are rejected without mutation, fresh current-schema databases can be created, removed authentication aliases, import facades, and call signatures cannot be reintroduced, rotation, archive validation, and supported recovery still work, CI and pre-commit enforce the same policy, and the complete test suite passes.

## Testing Expectations
Run `tools/check_compat_shims.py` with the removed-name and documentation-symbol checks enabled; run the checker self-tests; run pre-commit locally and the complete CI workflow; search the active documentation tree for all removed terminology and symbols; follow the database runbook's recreate procedure in an isolated test environment; run the documentation checkers `routing.md` names for edited `docs/` files.

## Documentation Impact
Yes: this issue is the documentation rewrite itself (all active documents, runbooks). Documents are written in English (`skills/DESIGN.md` Output language); name the target documents through `docs/00_index.md`; do not copy configuration values or implementation counts into them.

## Out of Scope
Preserving migration history in active documentation, adding deprecation periods, adding compatibility exceptions without a separate approved policy change, and replacing Git history with an active archive document.

## Dependencies
Start after `issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md`, `issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md`, and `issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md` have established the final deleted-symbol and deleted-module set.

## Unresolved Questions
- Whether `symbol_stage_allowance` is still needed after the documentation is rewritten.
- Whether a task-runner configuration (a `Makefile` or similar) exists that also invokes the checker.

## AI Implementation Instruction
Wait for the three implementation issues to land; then change the checker configuration, documentation, and tests together so the policy is enforced from one consistent state.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-125145
- **Related target files**: `tools/check_compat_shims.py`, `tools/compat_exceptions.toml`, `tests/tools/test_check_compat_shims.py`, `.pre-commit-config.yaml`, `.github/workflows/backward-compat-check.yml`
