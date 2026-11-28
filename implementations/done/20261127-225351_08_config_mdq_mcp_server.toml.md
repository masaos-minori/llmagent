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
- Line 28: the comment states the byte unit, so the unit is named in the file. Landed 20261128 as
  "Maximum file size in bytes; a larger file is skipped before it is read" — it names both the unit
  and the skip behavior; the recorded wording is not applied verbatim because the landed one is more
  specific.
- Line 61: the historical-notes comment points to `docs/mdq_config_history.md`, which does not exist
  under `docs/` (UNK-04). Re-verified 20261128: the comment sits at Line 74 in both HEAD and the
  working file (the recorded Line 61 was stale). The stale reference stays untouched — reported here
  for the owner; the rename note is written in `docs/22_mcp/mcp_04_04_mdq.md`, the doc named by
  `docs/00_index.md` "Document References by Task" (procedure seq 16).

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
- As-run 20261128: `test_mdq_config.py` = 36 passed (exercises the renamed key's validation contract;
  it builds payloads, it does not read the deployed file); whole `tests/mcp_servers/mdq/` +
  `tests/mcp_servers/test_mdq_audit.py` = 533 passed; gates clean. The deployed file is validated at
  process startup by `scripts/mcp_servers/mdq/startup_config.py`; the rename was confirmed there by
  the startup-path tests (`tests/mcp_servers/mdq/_startup.py` carries the renamed key).

## Completion criteria
- The deployed config names the byte unit, the startup validation passes with the renamed key, and the
  compatibility note exists in the doc named by the task mapping.
- Note 20261128: the doc note part is carried by procedure seq 16 and is not complete until it lands.

## Out of Scope
- The model field definition (procedure seq 01) and the validated key list (procedure seq 07).
- The documentation text, which is procedure seq 16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the key and state the unit in the comment | Completed | 2026-11-28 | 2026-11-28 | Landed with the batch rename cycle at Lines 28-29; value 100000 unchanged. Comment names the unit and the skip behavior (see Details). Historical-notes reference is at Line 74, not 61 (stale record corrected); left untouched per UNK-04. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | test_mdq_config.py 36 passed; full mdq run 533 passed; toolchain gates clean. Doc note dependency recorded in Completion criteria; owned by procedure seq 16. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-04: the historical-notes comment at Line 74 points to `docs/mdq_config_history.md`, which does not exist under `docs/`. Reported to the owner 20261128; the comment stays untouched pending an owner decision on the target document. Not part of this rename. | No | — |

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
