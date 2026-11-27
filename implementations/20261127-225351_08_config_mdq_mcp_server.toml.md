# Implementation Procedure — config/mdq_mcp_server.toml

## Goal

Rename the size-limit key to its byte unit and state the unit in the comment, so the deployed config
names the same unit the code enforces.

## Scope
**Release unit**: byte-limit-key-rename

Requirement implemented: REQ-004 (the configuration-key rename is a compatibility change).
Acceptance criterion: AC-3.

## Assumptions
- The key is renamed, not accepted under both names (UNK-01); no repository convention supports
  aliasing a config key.
- No decoded-character key is added (UNK-02), so the file gains no new key beyond the rename.
- The model field, the validated key list, the service attribute, and the tests are changed by
  procedures seq 01, 06, 07, and 13 in the same commit.

## Design decisions
- The comment states the unit explicitly, because the ambiguity being removed is a unit ambiguity
  rather than a value change.

## Alternatives considered
- Keeping the old key name and reinterpreting it as bytes: rejected, because the deployed config would
  still read as a character limit.

## Implementation
### Target file
`config/mdq_mcp_server.toml`

### Procedure
Rename one key and rewrite its comment line.

### Method
Configuration content only; no behavior.

### Details
- Line 29: `max_file_chars = 100000` becomes `max_file_bytes` (new) `= 100000`; the value is unchanged.
- Line 28: the comment becomes "Maximum number of bytes to include in a file", so the unit is stated
  in the file.
- Line 61: the historical-notes comment points to `docs/mdq_config_history.md`, which does not exist
  under `docs/` (UNK-04). The stale reference is reported to the owner and is not rewritten to an
  invented target; the rename note is written in `docs/22_mcp/mcp_04_04_mdq.md`, the doc named by
  `docs/00_index.md` "Document References by Task".

## Compatibility considerations
- This is a compatibility change: a deployed config that still uses `max_file_chars` fails startup
  validation once the code changes, so the config, the code, the tests, and the doc must land in one
  commit.
- `deploy/deploy.sh` copies this file with an existing `cp` line, so the deployed content changes
  without adding a deploy line.

## Security considerations
- N/A: no security behavior; the key remains a validated scalar with the same `gt=0` constraint.

## Rollback considerations
- N/A: revert the commit. A revert must revert the code in the same commit, otherwise the deployed
  config no longer validates.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py` — the renamed default and the field list.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The deployed config names the byte unit, the startup validation passes with the renamed key, and the
  compatibility note exists in the doc named by the task mapping.

## Out of Scope
- The model field definition (procedure seq 01) and the validated key list (procedure seq 07).
- The documentation text, which is procedure seq 16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the key and state the unit in the comment | Pending | — | — | REQ-004, AC-3, Phase 4 |
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
- **Requirement ID**: REQ-004 (the size-limit key renamed to its byte unit, documented as a
  compatibility change)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `config/mdq_mcp_server.toml`
