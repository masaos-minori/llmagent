# Evaluate a shared base class for the `repo_path` field across `git_models.py`'s 10 request models

## Priority
Low

## Summary
`scripts/mcp_servers/git/git_models.py` defines 10 Pydantic request models, each with an
identical `repo_path` field (same type, same description, added via a shared `_REPO_PATH_DESC`
constant as of the 2026-08-14 refactor). A shared base class/mixin carrying this field was
considered but not implemented.

## Reason for Change
Introducing inheritance for the `repo_path` field would reduce remaining duplication (the field
declaration itself, not just its description string, is still repeated 10 times), but Pydantic's
generated JSON Schema can change shape when fields come from a base class (e.g. `$defs`/`allOf`
referencing, field ordering in `model_fields`) unless `model_config` is carefully tuned. Since
these models' JSON schemas are consumed by MCP clients, this requires explicit before/after
schema verification that was out of scope for the original no-behavior-change refactor cycle.

## Implementation Intent
Before implementing, generate `model_json_schema()` for all 10 affected models and record the
current output as a baseline. Introduce the mixin/base class, regenerate the schemas, and diff
byte-for-byte against the baseline. Only proceed if the diff shows zero unintended changes (or
get explicit sign-off if some restructuring, e.g. `allOf` wrapping, is unavoidable but judged
acceptable).

## Target Files or Areas
- `scripts/mcp_servers/git/git_models.py` (all 10 request models with a `repo_path` field)
- `scripts/mcp_servers/git/git_server.py` (tool schema registration, consumes these models)

## Required Changes
- Snapshot `model_json_schema()` output for all 10 models before any change.
- Introduce a shared base class/mixin carrying the `repo_path` field.
- Regenerate schemas and diff against the snapshot.
- If MCP tool-schema consumers (`git_server.py`'s tool registration, any `TOOL_LIST`-schema
  contract tests) are affected, re-verify them explicitly.

## Acceptance Criteria
- `model_json_schema()` output for all 10 models is byte-identical before and after (or any
  difference is explicitly documented and signed off).
- `tests/mcp_servers/test_tool_schema_contract.py` and any other schema-contract tests pass
  unchanged.
- No change to any model's runtime validation behavior (field name, type, requiredness).

## Testing Expectations
Schema-diff verification (see Implementation Intent) plus full `tests/mcp_servers/git/` and
schema-contract test suite runs before and after.

## Documentation Impact
None expected unless tool schemas are documented verbatim in `docs/04_mcp_*` files — check
before assuming no impact.

## Out of Scope
- Do not change the `repo_path` field's type, description text, or validation behavior — only
  its declaration mechanism (direct field vs. inherited).
- Do not touch any of the other model-specific fields.

## AI Implementation Instruction
Do not implement the mixin until the before/after `model_json_schema()` diff is verified
byte-identical (or an intentional difference is explicitly signed off) — this is the primary
risk this issue exists to gate.
