## Goal
Add a `class_enum` field to `tools/_front_matter_schema.py`'s `FrontMatterSchema`
dataclass and parse it in `load_front_matter_schema()` (`REQ-003`).

## Scope
In scope: this one module's dataclass and loader function. Out of scope: any
change to `tools/manage_frontmatter.py` or `tools/check_docs_structure.py`'s own
logic (they consume this module's output; their own edits are seq 03 and a
separate, out-of-scope follow-up respectively — see the source Plan's Risks).

## Assumptions
- Module structure unchanged since the Plan was written — re-confirmed:
  `FrontMatterSchema` dataclass (line 35) with `required_fields`, `area_enum`,
  `status_enum`, `source` fields; `_default_schema()` (line 49);
  `load_front_matter_schema()` (line 58) parsing `area_enum`/`status_enum` from
  the schema's `properties.area.enum`/`properties.status.enum`.
- Depends on seq 01 (`schemas/doc_front_matter.json`) having added the `class`
  property first for `class_enum` to actually populate from the real schema
  file — this module's own fallback (`class_enum=None` when absent) keeps it
  safe to land independently of seq 01's timing, but full functionality
  requires both.

## Design decisions
Mirror the existing `area_enum`/`status_enum` handling exactly: add
`class_enum: tuple[str, ...] | None` to the dataclass, add the same
`isinstance(class_prop, dict)` + `enum` extraction block in
`load_front_matter_schema()`, and default to `None` in `_default_schema()` (no
class enforcement when no schema file exists — matching today's behavior for
`area`/`status` before a schema existed).

## Alternatives considered
A generic `properties: dict[str, tuple[str, ...] | None]` mapping (instead of
one named field per property) was considered, as it would scale better to
future new properties — but rejected to keep this change minimal and consistent
with the existing per-property-named-field pattern; a broader refactor of this
module's shape is out of scope for this Plan (per `AGENTS.md` Global Rule 5).

## Implementation
### Target file
tools/_front_matter_schema.py

### Procedure
1. Add `class_enum: tuple[str, ...] | None` to the `FrontMatterSchema` dataclass
   (after `status_enum`).
2. Add `class_enum=None` to `_default_schema()`'s return.
3. In `load_front_matter_schema()`, add a `class_prop = properties.get("class")`
   block mirroring the existing `area_prop`/`status_prop` blocks, and include
   `class_enum=class_enum` in the final `FrontMatterSchema(...)` return.

### Method
Direct code edit (`Edit` tool) — additive dataclass field + mirrored parsing
block, no restructuring of existing `area_enum`/`status_enum` logic.

### Details
- Update the module's own docstring (lines 1-17) to mention `class_enum`
  alongside `area`/`status`, keeping the "single source of truth" framing
  accurate.
- No change to `DEFAULT_REQUIRED_FIELDS` — `class` is optional, never required.

## Compatibility considerations
Additive dataclass field — any existing code constructing `FrontMatterSchema`
positionally (rather than by keyword) would break; re-confirm both call sites
(`_default_schema()`, `load_front_matter_schema()`'s own return) use keyword
arguments already (they do, per current source) so this addition is safe.

## Security considerations
N/A: no credentials or runtime code beyond local file parsing (already the case
for this module).

## Rollback considerations
`git checkout -- tools/_front_matter_schema.py` reverts this row independently
— seq 03's `classify` subcommand depends on `class_enum` existing, so reverting
this row alone (while seq 03 has landed) would break seq 03's import; revert
both together if either is reverted.

## Validation plan
- `uv run pytest tests/tools/test_front_matter_schema.py -v` (seq 06's new
  tests).
- `uv run ruff check tools/_front_matter_schema.py`
- `uv run mypy tools/_front_matter_schema.py`

## Completion criteria
- `FrontMatterSchema.class_enum` exists and is populated from
  `schemas/doc_front_matter.json`'s `properties.class.enum` when present,
  `None` otherwise.
- Existing `area_enum`/`status_enum` behavior is unchanged (regression-tested by
  seq 06).

## Out of scope
Changes to `tools/manage_frontmatter.py` (seq 03) or `tools/check_docs_structure.py`
(explicitly out of scope per the source Plan's Risks/Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in seq 06's document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `tools/`-scoped lighter sequence |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: internal module, no docs/*.md reference |

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
- **Requirement ID**: REQ-003 (add class_enum to FrontMatterSchema)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: tools/_front_matter_schema.py
