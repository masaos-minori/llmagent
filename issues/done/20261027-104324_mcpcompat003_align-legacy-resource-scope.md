# Align the legacy resource_scope statement and the schema-2.0 validator contract

## Priority
Medium

## Summary
Make the document, the validator and the discovery path agree on what happens to a legacy singular `resource_scope` field and on which layer owns the four mandatory schema-2.0 fields.

## Background
Source: `memo-issue.md` items H-03 and M-03 (responsibility part), re-verified against current source on 2026-10-27 (Confirmed by repository search). The memo's earlier claim that two scope fields are optional is withdrawn by the memo itself; the checks below confirm that.

- Document claim: `docs/22_mcp/mcp_03_02_tool-registry.md` (line 70) says "`status`, legacy singular `resource_scope`, and `enabled` are validated only if present".
- Code: `_entry_optional_field_error()` in `scripts/agent/services/mcp_tool_discovery_fetch.py` validates only `status` (str), `enabled` (bool) and `capabilities`. No code in `scripts/` reads or validates a singular `resource_scope` key on a tool-list entry (the other `resource_scope` hits in `scripts/agent/` are audit and scheduler fields, unrelated). A legacy entry carrying it is accepted and the field is silently ignored. No MCP server definition under `scripts/` or `tests/` emits a singular `resource_scope` tool field.
- Four mandatory fields: `_fetch` layer `_REQUIRED_SCHEMA_V2_FIELDS` (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`) rejects a missing field before `validate_tool_schema_v2()` runs, and `scripts/agent/services/mcp_tool_discovery_registry.py` indexes the four fields directly. So the Discovery path as a whole requires all four, matching the document's "mandatory" statement.
- Validator: `validate_tool_schema_v2()` in `scripts/shared/resource_scope.py` requires `is_write` and `requires_serial` itself, but defaults a missing `resource_scope_kind` to `""` (a member of `_KNOWN_SCOPE_KINDS`) and a missing `resource_scope_keys` to `[]`. Its docstring says it "never coerces or defaults a missing/mistyped field". The validator is also used by `tests/mcp_servers/test_tool_schema_contract.py`, which checks the in-tree tool lists, so the contract differs between the two callers.

## Problem
- The document states a validation of the legacy field that does not exist; a reader would expect a legacy declaration to be checked or rejected.
- Required-field enforcement is split: two fields in the validator, all four in the fetch layer. The validator's docstring promises no defaulting but defaults two fields, so a caller that uses the validator alone accepts entries the Discovery path rejects.

## Reason for Change
Documentation/code mismatch about a validation rule and a validator whose documented contract is not its actual contract; non-critical, since the production Discovery path is already strict, hence Medium. Not time-sensitive.

## Implementation Intent
Decide the legacy-field policy, then make code, tests and document state the same thing. Recommended direction from the memo: reject an entry that carries a singular `resource_scope` with an explicit schema error so migration mistakes are visible. Single-source the mandatory-field check: either move all four presence checks into the validator and let the fetch layer use its result, or keep the fetch-layer pre-check and state in the validator docstring and tests that presence is the caller's responsibility. Prefer the first, because the validator is documented as the last line of defense.

## Target Files or Areas
- `scripts/shared/resource_scope.py` (`validate_tool_schema_v2`)
- `scripts/agent/services/mcp_tool_discovery_fetch.py`
- `scripts/agent/services/mcp_tool_discovery_registry.py` (read-only confirmation of direct indexing)
- `tests/shared/test_resource_scope.py`, `tests/mcp_servers/test_tool_schema_contract.py`, discovery fetch tests under `tests/agent/services/`
- `docs/22_mcp/mcp_03_02_tool-registry.md`

## Required Changes
- Decide and record the legacy policy (explicit rejection recommended, or ignore and document as unsupported).
- Implement the chosen policy in the validator or fetch layer with a test using an entry that carries a singular `resource_scope`.
- Make the validator enforce presence of all four mandatory fields, or correct its docstring and add tests stating the split; keep the fetch layer and registry consistent with the choice and avoid double reporting of the same missing field.
- Confirm by test that every in-tree MCP server tool list satisfies the four-field contract (the existing contract test should cover this; verify and extend if not).
- Rewrite the document sentence: remove the claim that the legacy field is validated, state the adopted policy and the unchanged four-field requirement.

## Constraints
- A tool with a missing or invalid field must stay excluded from the registry; no silent defaulting (existing document rule).
- Finding severity (WARNING versus FATAL for required servers) must not change.
- Error message wording that existing tests assert may change only together with those tests.

## Acceptance Criteria
- The document no longer says the legacy singular `resource_scope` is "validated only if present" and states the actual policy.
- An entry with a singular `resource_scope` behaves as the policy states, covered by a test.
- Calling `validate_tool_schema_v2()` on an entry missing `resource_scope_kind` or `resource_scope_keys` behaves as the validator docstring states, covered by a test, and the docstring and implementation agree.
- All in-tree MCP tool lists still pass the contract test.

## Testing Expectations
- `uv run pytest tests/shared/test_resource_scope.py tests/mcp_servers/test_tool_schema_contract.py tests/agent/services -q`, then the full suite, mypy (`--no-namespace-packages`), ruff, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_docs_consistency.py --domain mcp` and the docs checkers for the edited document.

## Documentation Impact
Yes. Fix the stated validation rule and state the legacy-field policy and where mandatory-field presence is enforced (responsibility boundary only). Optionally state, in one sentence each, that the fetch module owns `/v1/tools` fetch and entry validation and the registry module owns duplicate exclusion and registry build, if the current text does not (not verified; the discovery document text beyond line 70 was not read).

## Out of Scope
- Changing the set of known scope kinds or the scope-conflict logic.
- Posture gating and the Health re-export (see `issues/*mcpcompat001*`).
- Schema fields other than the four mandatory fields and the legacy `resource_scope`.

## Dependencies
- Shares `docs/22_mcp/` documents with `mcpcompat001` (different files, no ordering required) and may add a checker rule in `tools/check_compat_shims.py` only if the owner wants the legacy field guarded there; otherwise no overlap.
- No open issue or in-flight plan touches `resource_scope.py` or the discovery fetch module.

## Unresolved Questions
- 不明: owner decision on the legacy policy (explicit rejection recommended, not yet approved).
- 不明: whether any external or deployed MCP server still emits a singular `resource_scope`; only in-tree definitions were searched.
- 不明: whether `tests/mcp_servers/test_tool_schema_contract.py` already asserts presence of the two scope fields on every tool list (not read).

## AI Implementation Instruction
Keep the change to the validator, the fetch-layer pre-check, their tests and the one document sentence. Do not alter registry building or severity handling. Do not start before the legacy policy is recorded. Stop and report if a server emitting the legacy field is found.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-104324
- **Related target files**: scripts/shared/resource_scope.py, scripts/agent/services/mcp_tool_discovery_fetch.py, scripts/agent/services/mcp_tool_discovery_registry.py, tests/shared/test_resource_scope.py, tests/mcp_servers/test_tool_schema_contract.py, docs/22_mcp/mcp_03_02_tool-registry.md
