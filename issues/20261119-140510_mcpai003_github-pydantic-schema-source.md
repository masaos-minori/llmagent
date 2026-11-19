# Make GitHub Pydantic models the single source of truth for schemas and configuration validation

## Priority
High

## Summary
Generate every GitHub tool `inputSchema` from strict Pydantic request models and strengthen request and configuration validation, so discovery-time and runtime validation enforce one contract.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 2). Public tool schemas under `scripts/mcp_servers/github/tools_*.py` are maintained manually next to the runtime models in `github_models_*.py`. Related archived work on schema and coercion: `issues/done/20261118-025551_mcpget001_mcp-models-type-coercion.md` (re-verify against it).

Evidence: `tests/test_github_tool_registry.py` (named by the review) does not exist in the repository (`Explicit in code`, by file check); the correct test location is `Needs confirmation`. The drift claims (missing `dry_run`, inconsistent enums, limits, and unknown-field behavior; truthiness conversion of `"false"`) come from the review and are `Needs confirmation`.

## Problem
Published schemas and runtime models have drifted: write models support `dry_run` but public schemas omit it, so the Agent may present an incomplete contract, accept arguments that fail later, or fail to expose a safety feature. Configuration parsing accepts ambiguous values (the string `"false"` read as true) and weak range and list validation lets invalid limits and malformed repository identifiers reach runtime.

## Reason for Change
The contract is foundational for dry-run (`issues/20261119-140512_mcpai005_structured-execution-context.md`) and the HTTP integration gate (`issues/20261119-140517_mcpai010_github-http-contract-tests.md`); patching individual fields would keep the structural cause of drift.

## Implementation Intent
Use strict Pydantic models (`extra="forbid"`) as the authoritative contract for runtime validation and `/v1/tools` discovery through one reusable, deterministic schema-generation helper shared by all GitHub domains. Preserve `$defs` and `$ref` unless the Agent validator demonstrably requires flattening; if it does, implement one shared, tested resolver. Reject invalid input and configuration before any GitHub API access.

## Target Files or Areas
- `scripts/mcp_servers/github/github_models_base.py`, `github_models_file.py`, `github_models_issues.py`, `github_models_pull_requests.py`, `github_models_repository.py`, `github_models_config.py`
- `scripts/mcp_servers/github/tools_issues.py`, `tools_pull_requests.py`, `tools_repository.py`, `tools_file.py`
- Existing tool-schema tests: `tests/mcp_servers/test_tool_schema.py`, `tests/mcp_servers/test_tool_schema_contract.py`, `tests/mcp_servers/test_mcp_tool_schema_exports.py`

## Required Changes
- Add a common strict request base model and generate every `inputSchema` from `model_json_schema()`, preserving `default`, `enum`, `pattern`, `minimum`, `maximum`, `minLength`, `minItems`, `$defs`, `$ref`, and `additionalProperties`; strip only presentation-only fields.
- Publish `dry_run` on all GitHub write tools.
- Require non-empty owner, repository, branch, path, title, message, and other mandatory text; require issue and pull request numbers of at least 1; require at least one file in push-files; reject pull request updates with no actual update.
- Add justified upper bounds for content, body, labels, assignees, and files per request.
- Parse booleans strictly in GitHub configuration; require positive pagination values and `default_per_page <= max_per_page`; reject NaN and infinity.
- Validate every allowlist entry as a non-empty `owner/repo` identifier; normalize and deduplicate deterministically.

## Constraints
- Schema generation must be deterministic.
- Unknown top-level and nested fields are rejected.
- Public tool behavior may become stricter; the rejected inputs must be listed in the change.

## Acceptance Criteria
- [ ] All GitHub tool schemas are generated from Pydantic request models and every write schema exposes `dry_run`.
- [ ] Discovery-time and runtime validation reject the same invalid arguments, including unknown fields.
- [ ] Empty identifiers, empty file batches, and no-op pull request updates are rejected.
- [ ] Invalid boolean strings, negative limits, NaN, infinity, and malformed repository identifiers are rejected at startup.
- [ ] Schema generation is deterministic and CI fails when a request model and the published schema drift.

## Testing Expectations
- Model-to-tool-schema consistency tests for all GitHub tools; `dry_run` presence in every write schema.
- Tests for enums, patterns, numeric ranges, item counts, defaults, and unknown fields.
- Configuration tests for invalid booleans, limits, repository identifiers, and duplicate normalization.
- HTTP tests proving invalid input never reaches a GitHub service method.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Record that models are the schema source and the rejection rules (intent and boundaries); regenerate any generated contract tables the repository checks.

## Out of Scope
- File, Git, and other MCP servers' schemas (File MCP is in `issues/20261119-140516_mcpai009_file-mcp-hardening.md`).
- Allowlist enforcement and search scoping (`issues/20261119-140509_mcpai002_github-read-security-boundary.md`).

## Dependencies
- Blocks `issues/20261119-140512_mcpai005_structured-execution-context.md` and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`.
- Independent of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` and `issues/20261119-140509_mcpai002_github-read-security-boundary.md`; may be implemented in parallel. Configuration field additions in `issues/20261119-140509_mcpai002_github-read-security-boundary.md` should reuse the strict validators from this issue.

## Unresolved Questions
- `不明`: whether the Agent-side validator can consume `$defs` and `$ref` unflattened.
- `不明`: the upper-bound values for content, body, labels, assignees, and files.
- `不明`: the intended location of the model-to-schema test (the review's `tests/test_github_tool_registry.py` is absent).

## AI Implementation Instruction
Do not fix drift by adding individual missing fields. Introduce the shared helper first, then migrate one domain at a time with tests. Keep unrelated servers untouched and stop and report if flattening turns out to be required.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140510
- **Related target files**: `scripts/mcp_servers/github/github_models_base.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/github/tools_issues.py`, `scripts/mcp_servers/github/tools_pull_requests.py`, `scripts/mcp_servers/github/tools_repository.py`, `scripts/mcp_servers/github/tools_file.py`
