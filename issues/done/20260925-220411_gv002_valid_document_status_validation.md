# [Governance] Implement Valid Document Status value validation

## Priority
High

## Summary
Add automated validation that the `status` front-matter field values are one of `stable` or `draft`, enforcing GV-002 from the Governance Verification Matrix.

## Background
GV-002 requires that any `status` field present in a document's Front Matter must use one of the allowed values defined in `governance_02_documentation-metadata.md`: `stable` (default when absent) or `draft`. Currently no tool validates this constraint. The existing `check_docs_structure.py` already has a `--schema` mode that validates `area` and `status` enums against a JSON Schema, but this is opt-in and not wired into CI. Without enforcement, invalid status values can silently enter the documentation set.

## Problem
Documents can contain arbitrary `status` values (e.g., `deprecated`, `superseded`, typos like `stabel`) without any automated detection. This breaks downstream tooling that relies on the status enum for filtering, routing, and display logic.

## Reason for Change
The governance policy explicitly defines only two valid values (`stable`, `draft`). Without validation, non-conforming documents accumulate over time, degrading the reliability of the documentation metadata layer.

## Implementation Intent
Extend the existing schema-based validation in `check_docs_structure.py` to make GV-002 enforcement default-on (not just opt-in via `--schema`). Two approaches are viable:

1. **Schema-based approach** (preferred): Make the `--schema` flag default behavior so that `status` enum validation runs automatically alongside other structural checks. The schema already supports `status_enum` (see `FrontMatterSchema.status_enum` at `tools/_front_matter_schema.py`).

2. **Inline validation approach**: Add a dedicated `check_status_value()` function in `check_docs_structure.py` that mirrors the existing `check_schema_compliance()` pattern but hardcodes the allowed values `[stable, draft]` directly, avoiding the schema dependency.

Either way, the check should report a clear error message indicating which document has an invalid status value and what the allowed values are.

## Target Files or Areas
- `tools/check_docs_structure.py`
- `tools/_front_matter_schema.py`
- `schemas/doc_front_matter.json` (if using schema-based approach)
- `.github/workflows/governance-docs-consistency.yml` (CI wiring)

## Required Changes
- Add `check_status_value(path, data)` function that validates `status` field against allowed values `[stable, draft]`
- Integrate the check into `validate_file()` so it runs alongside other structural checks
- Update `main()` to call the new check for every document processed
- Report errors with format: `{filename}: 'status' value '{value}' is not one of ['stable', 'draft']`
- Wire the check into CI pipeline (same gate as GV-001, GV-003, etc.)

## Constraints
- Must preserve backward compatibility: documents without a `status` field must continue to pass (default is `stable`)
- Error messages must match the style of existing validation messages in `check_docs_structure.py`
- Cannot change the allowed values — they are defined by the governance policy

## Acceptance Criteria
- Running `uv run python tools/check_docs_structure.py docs/*.md` reports an error for any document with `status: <invalid_value>`
- Documents without a `status` field pass validation (defaults to `stable`)
- Documents with `status: stable` or `status: draft` pass validation
- The check is included in the CI pipeline alongside other blocking checks

## Testing Expectations
- Unit test for `check_status_value()` with valid values (`stable`, `draft`)
- Unit test for `check_status_value()` with invalid values (e.g., `deprecated`, `superseded`, `stabel`)
- Unit test for `check_status_value()` with missing `status` field (should return empty list)
- Integration test confirming the check runs in `validate_file()` flow

## Documentation Impact
Update `docs/00_governance/governance_04_documentation-checks.md` to update GV-002 status from "Missing" to "Existing" in the Governance Verification Matrix table.

## Out of Scope
- Adding new status values (that would require a governance policy change first)
- Changing the default value from `stable`
- Validating status across related documents (only per-document validation)

## Dependencies
- Depends on understanding of existing `check_docs_structure.py` patterns (already read)
- May depend on schema infrastructure in `tools/_front_matter_schema.py` if using schema-based approach

## Unresolved Questions
- Should the check also validate that `status` is not used inconsistently between front matter and body text? (Out of scope for now — tracked separately as GV-019)
- Is the schema-based approach preferred over inline validation? Both are viable; decision depends on whether the team wants to centralize validation rules in schemas.

## AI Implementation Instruction
Implement the status validation check in `tools/check_docs_structure.py`. Follow the existing pattern: add a `check_status_value(path, data)` function, integrate it into `validate_file()`, and ensure error messages match the existing style. Prefer the schema-based approach if `FrontMatterSchema.status_enum` is already populated with `[stable, draft]`; otherwise implement inline validation. Do not modify any existing document files.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-220411
- **Related target files**: tools/check_docs_structure.py, tools/_front_matter_schema.py, schemas/doc_front_matter.json
