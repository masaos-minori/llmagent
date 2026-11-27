# Implementation Procedure — scripts/mcp_servers/mdq/mdq_security_validation.py

## Goal

Apply the startup validation to the renamed byte-limit key so the renamed configuration key is
validated at startup.

## Scope
**Release unit**: byte-limit-key-rename

Requirement implemented: REQ-004 (startup validation of the renamed key). Acceptance criterion: AC-3.

## Assumptions
- Only the key name changes; the validation behavior is owned by the server-boundary plan and is not
  changed here (cross-plan overlap recorded in the Plan's Assumptions).
- The renamed field itself is defined by procedure seq 01 in `scripts/mcp_servers/mdq/mdq_models.py`.

## Design decisions
- One entry in `_MDQ_SCALAR_SETTINGS` is renamed; no new entry is added, because the decoded-character
  limit is not a configuration key (UNK-02).

## Alternatives considered
- Keeping `max_file_chars` in the list and accepting both names: rejected, because no repository
  convention supports aliasing a config key (UNK-01) and the ambiguous unit would stay validated.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_security_validation.py`

### Procedure
Rename one entry of the validated key tuple.

### Method
A single tuple entry change; no behavior change.

### Details
- `_MDQ_SCALAR_SETTINGS` Line 42: `max_file_chars` becomes `max_file_bytes` (new).

## Compatibility considerations
- A deployed config that still uses `max_file_chars` fails startup validation after the change, which
  is the compatibility risk recorded in the Plan's Risks; the code, the config file, the tests, and the
  doc change in the same commit.

## Security considerations
- The key stays validated at startup with the same `gt=0` constraint; no posture or gate change.

## Rollback considerations
- N/A: revert the commit — one tuple entry.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py` — the renamed key is validated at startup.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The renamed key is present in the validated key list and the startup validation test passes.

## Out of Scope
- Validation behavior, strict-value handling, and the field definition (server-boundary plan and
  procedure seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the entry in `_MDQ_SCALAR_SETTINGS` | Pending | — | — | REQ-004, AC-3, Phase 4 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (startup validation of the renamed byte-limit key)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/mdq_security_validation.py`
