# Harden `delete_models.py` request validation and config immutability

## Priority
Low

## Summary
Three related, deferred hardening ideas from `scripts/mcp_servers/file/delete_models.py`'s
2026-08-14 refactor cycle:
1. `DeleteFileRequest`/`DeleteDirectoryRequest`'s `path: str` field has no validation rejecting
   empty strings or relative paths.
2. `path`/`dry_run` field description text differs slightly between `DeleteFileRequest` and
   `DeleteDirectoryRequest` ("file" vs. "directory" wording) — could be unified via a shared
   Mixin.
3. `FileDeleteConfig` is a mutable dataclass with no `frozen=True`, and the Pydantic request
   models have no `extra="forbid"`, so unexpected fields are silently accepted.

## Reason for Change
All three were identified but not implemented because each is a genuine behavior change, not a
pure refactor:
1. Adding path validation would newly reject requests that previously succeeded (e.g. relative
   paths), a behavior change requiring explicit scope decision on what should be rejected.
2. Unifying description text changes the generated JSON Schema `description` field, which MCP
   clients may pass verbatim into an LLM prompt — a visible-output change.
3. `frozen=True`/`extra="forbid"` would newly raise on field reassignment or unknown-field
   requests that currently succeed silently — a behavior change, and it's unconfirmed whether
   any caller currently relies on either being permissive.

## Implementation Intent
Each of the three needs its own scoped decision before implementation:
1. Confirm via `rg` whether any current caller sends relative paths; if enforcement is desired,
   define the exact validation (e.g. require absolute path) and add a `model_validator`.
2. Decide the unified wording (if any) with schema-diff verification before/after.
3. Confirm via `rg` that no caller reassigns `FileDeleteConfig` fields post-construction or sends
   extra fields in requests, before adding the stricter guards.

## Target Files or Areas
- `scripts/mcp_servers/file/delete_models.py` (`FileDeleteConfig`, `DeleteFileRequest`,
  `DeleteDirectoryRequest`)
- `scripts/mcp_servers/file/delete_service.py` (consumer of these models)

## Required Changes
- For (1): add explicit path validation only after confirming no legitimate caller depends on
  current permissive behavior; add characterization tests for the new rejection.
- For (2): unify wording only with an explicit before/after JSON-schema diff reviewed.
- For (3): add `frozen=True`/`extra="forbid"` only after confirming via `rg` that no caller
  mutates the config or sends extra fields; add tests for the new rejection behavior.

## Acceptance Criteria
- Each sub-change has its own characterization tests for the newly-rejected cases.
- Existing valid requests/config usage continue to work unchanged.
- Any JSON-schema description change is explicitly reviewed and documented.

## Testing Expectations
Full `tests/mcp_servers/file/` regression suite; new tests for each newly-enforced validation
rule; schema-contract tests if description text changes.

## Documentation Impact
None expected unless field descriptions visible in `docs/04_mcp_*` tool-schema examples change.

## Out of Scope
- Do not implement any of the three sub-changes without first confirming (via `rg` and/or
  explicit sign-off) that no current caller depends on the permissive behavior being tightened.
- Do not bundle this with unrelated `delete_models.py` changes.

## AI Implementation Instruction
Treat the three sub-items as independently schedulable — implement and review each separately.
Do not implement any of them speculatively; confirm via `rg` (and sign-off where behavior newly
rejects previously-valid input) before writing code, per `rules/coding.md`'s explicit sign-off
gates.
