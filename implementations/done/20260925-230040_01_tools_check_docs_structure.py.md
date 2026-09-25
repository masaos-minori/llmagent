## Goal

Make GV-002 status enum validation default-on in `check_docs_structure.py`, so that invalid `status` front-matter values are detected automatically without requiring the `--schema` flag. REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-009.

## Scope

- Add `check_status_value()` function that validates against `[stable, draft]`
- Integrate the check into `validate_file()`
- Update `main()` to make `--schema` default behavior
- Preserve backward compatibility — documents without a `status` field continue to pass

## Assumptions

- `schemas/doc_front_matter.json` already defines `status_enum: ["stable", "draft"]` — confirmed by repository evidence
- The preferred approach is schema-based (make `--schema` default behavior) since the schema file already exists with the correct enum values
- Documents without a `status` field should continue to pass validation (backward compatibility)
- Error message format follows existing style in `check_schema_compliance()` (lines 143-150)

## Design decisions

- Prefer schema-based approach: make `--schema` flag default behavior, using `schemas/doc_front_matter.json` as the default schema path when no argument is passed
- Add `check_status_value()` as a fallback inline validator that hardcodes `[stable, draft]` directly — provides resilience if the schema file is absent or malformed
- In `validate_file()`, call `check_status_value()` unconditionally (not gated by `if schema is not None`) after `check_front_matter()` but before `check_tail_sections()`

## Alternatives considered

- Inline validation only (no schema integration): would duplicate the enum values from the schema file and diverge over time
- Schema-only approach (no standalone function): would require callers to always pass a schema object; `check_status_value()` provides a clean public API for both the tool's own use and external consumers

## Implementation
### Target file

`tools/check_docs_structure.py`

### Procedure

1. Add `check_status_value(path, data)` function
2. Integrate `check_status_value()` into `validate_file()`
3. Update `main()` to make `--schema` default behavior

### Method

#### Step 1: Add `check_status_value()` function

Add a new function after `check_schema_compliance()` (around line 152):

```python
def check_status_value(path: Path, data: dict[str, Any]) -> list[str]:
    """Validate the 'status' field against allowed values [stable, draft].

    Returns empty list when the 'status' field is absent (defaults to stable).
    Returns error list when the value is invalid.
    """
    status = data.get("status")
    if status is None:
        return []
    if status not in ("stable", "draft"):
        return [
            f"{path.name}: 'status' value {status!r} is not one of ['stable', 'draft']"
        ]
    return []
```

This mirrors the pattern used in `check_schema_compliance()` for `area` enum violations (lines 135-142), using the same `{path.name}: '{field}' value {value!r} is not one of [...]` format.

#### Step 2: Integrate `check_status_value()` into `validate_file()`

In `validate_file()` (line 225-244), add the call after `check_front_matter()` but before `check_tail_sections()`:

Current code at line 238-241:
```python
issues.extend(check_front_matter(path, content, expected_area))
if schema is not None:
    issues.extend(check_schema_compliance(path, content, schema))
issues.extend(check_tail_sections(path, content))
```

Change to:
```python
issues.extend(check_front_matter(path, content, expected_area))
# Parse front matter once for downstream checks
data = {}
try:
    end = content.find("\n---", 3)
    if end != -1:
        raw = content[3:end]
        data = yaml.safe_load(raw) or {}
except yaml.YAMLError:
    pass
issues.extend(check_status_value(path, data))
if schema is not None:
    issues.extend(check_schema_compliance(path, content, schema))
issues.extend(check_tail_sections(path, content))
```

The `data` dict is parsed once here to avoid duplicating YAML parsing logic across `check_front_matter()`, `check_status_value()`, and `check_schema_compliance()`. This is a minor refactoring that reduces redundant work.

#### Step 3: Update `main()` to make `--schema` default behavior

In `main()` (line 247-307), change the schema loading logic around line 282-285:

Current code:
```python
schema: FrontMatterSchema | None = None
if args.schema is not None:
    schema_path = None if args.schema == "__default__" else Path(args.schema)
    schema = load_front_matter_schema(schema_path)
```

Change to:
```python
schema: FrontMatterSchema | None = None
if args.schema is not None:
    schema_path = None if args.schema == "__default__" else Path(args.schema)
    schema = load_front_matter_schema(schema_path)
else:
    # Default-on: use the canonical schema when no --schema argument is passed
    schema = load_front_matter_schema(None)
```

When no `--schema` argument is passed, `load_front_matter_schema(None)` loads `schemas/doc_front_matter.json` (the canonical schema), making status enum validation automatic alongside other structural checks.

## Compatibility considerations

- Backward compatibility preserved: documents without a `status` field continue to pass (REQ-002, REQ-010)
- Existing `--schema` usage unchanged: users who explicitly pass `--schema` get the same behavior as before
- Making `--schema` default may surface previously undetected invalid status values in existing documents — this is intentional (the goal of the change)

## Security considerations

N/A — this change adds validation, does not modify security-sensitive behavior.

## Rollback considerations

If the change causes CI failures due to invalid status values in existing documents:
1. Revert the `main()` change to restore opt-in behavior (remove the `else` branch added in Step 3)
2. Fix invalid documents first, then re-apply the change

## Validation plan

- Unit test for `check_status_value()` with valid values (`stable`, `draft`) — REQ-007
- Unit test for `check_status_value()` with invalid values (e.g., `deprecated`, `superseded`, `stabel`) — REQ-007
- Unit test for `check_status_value()` with missing `status` field — REQ-007
- Integration test confirming the check runs in `validate_file()` flow — REQ-008
- Manual verification: `uv run python tools/check_docs_structure.py docs/*.md` reports errors for invalid values

## Completion criteria

- `check_status_value()` returns empty list for documents without `status` field
- `check_status_value()` returns empty list for documents with `status: stable` or `status: draft`
- `check_status_value()` returns error for documents with invalid `status` values
- `validate_file()` calls `check_status_value()` unconditionally
- `main()` uses `schemas/doc_front_matter.json` as default schema when `--schema` is omitted

## Out of scope

- Adding new status values (would require governance policy change first)
- Changing the default value from `stable`
- Validating status across related documents (only per-document validation)
- Modifying any existing document files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-009
- **Source issue**: issues/20260925-220411_gv002_valid_document_status_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-222320_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-230040
- **Related target files**: tools/check_docs_structure.py
