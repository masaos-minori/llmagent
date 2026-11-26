## Goal
- Add the explicit `config_dependent: bool = False` field to `RuntimeTool` and to `build_runtime_tool` in `scripts/shared/runtime_tool.py` so the producer-declared value is carried, not inferred (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the dataclass field, the builder keyword, and the test companion.
- Out of scope: the fetch validation (seq 10), the registry diagnostics (seq 13).

## Assumptions
- Verified in Step 3a: `RuntimeTool` (`runtime_tool.py:44-105`) has no `config_dependent` field; `build_runtime_tool` (`:108-198`) does not accept it; 14 test files call `build_runtime_tool` directly.
- D-7: the field is optional with default `False`; the default applies only to non-discovery construction, since the field is diagnostic-only.

## Design decisions
- Frozen dataclass field with default `False` and an optional keyword in the builder, keeping all 14 direct-construction test call sites valid.

## Alternatives considered
- Required keyword with no default (rejected by D-7: would force edits in 14 test files for a diagnostic-only field).

## Implementation
### Target file
`scripts/shared/runtime_tool.py`

### Procedure
1. Add `config_dependent: bool = False` to the `RuntimeTool` dataclass.
2. Add an optional `config_dependent` keyword to `build_runtime_tool` and pass it through.

### Method
- No validation here; the fetch layer (seq 10) guarantees the discovery path passes a strict bool.

### Details
- Field equality changes only for tools that actually carry a non-default value (Plan Risk: run the full suite).

### Companion test files
- `tests/shared/test_runtime_tool.py`
  - Procedure: assert the field defaults to `False`, the builder passes it through, and equality reflects the value (T-07).
  - Validation: `uv run pytest tests/shared/test_runtime_tool.py`.

## Compatibility considerations
- Additive field with default; existing constructions and the 14 test files stay valid.

## Security considerations
- N/A: diagnostic-only field; no credential or secret content.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The field exists with default `False`; the builder carries it; tests pass.

## Out of Scope
- Diagnostics rendering and the fetch validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the field and builder keyword | Pending | — | — | |
| 2 | Update the companion tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (explicit `config_dependent` on `RuntimeTool`)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/shared/runtime_tool.py`, `tests/shared/test_runtime_tool.py`
