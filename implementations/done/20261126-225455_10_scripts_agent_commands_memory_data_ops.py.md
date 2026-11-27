## Goal

Mask Memory entry content and summary before they are written to normal CLI output (REQ-005 — normal
CLI output is safe for terminal capture).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The display path writes `entry.summary` and `entry.content` unmasked at lines 356-357; this is the
  only Memory display path in this module that emits stored user data.
- Step 3b correction: the assumption is incomplete. `_summary_preview` (lines 39-40) also emits stored
  user data through the list and search display paths. Per the confirmed decision it masks before the
  60-character cap, so every Memory display path satisfies AC-1.
- No overlap with a sibling Plan on this file.

## Design decisions

- Masking is applied at the display boundary (Plan D5); stored entries are not rewritten, so the
  persisted record keeps its original content.
- The common masker is used rather than a Memory-specific pattern set, keeping one redaction model.

## Alternatives considered

- Masking at storage time — rejected: it would alter persisted data and is outside this Plan's scope.

## Implementation
### Target file
`scripts/agent/commands/memory_data_ops.py`
### Procedure
- Pass `entry.summary` and `entry.content` through `_mask_secrets` before writing them.

### Method
- In the display method at lines 353-357, write `_mask_secrets(entry.summary)` and
  `_mask_secrets(entry.content)`; path-shaped content additionally goes through `redact_path`
  (document 01).

### Details
- Truncation of summary elsewhere in the module is unaffected; masking happens before any truncation
  of the displayed value.

### Companion test files
- `tests/agent/commands/test_memory_data_ops.py`
  - Procedure: assert the displayed summary and content are masked for credential-bearing input.
  - Validation: `uv run pytest tests/agent/commands/test_memory_data_ops.py`.

## Compatibility considerations

- Display text changes only; stored entries and the existing summary-fallback behavior are unchanged.

## Security considerations

- AC-1 boundary: Memory content is user-supplied text that can carry credentials.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_memory_data_ops.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A Memory entry whose content contains a credential displays a masked value while non-sensitive
  content is displayed unchanged.

## Out of Scope

- Storage-time masking.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-023500 | show path masks summary and content via _display_text; Step 3b: _summary_preview also emits stored data and now masks before the 60-char cap |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-023500 | companion `tests/agent/commands/test_memory_data_ops.py` TestMemoryDisplayMasking added, 4 tests covering list preview, search preview, show, and path value; 49 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; mypy clean; bandit 1 pre-existing B101 unchanged; changed files: scripts/agent/commands/memory_data_ops.py, tests/agent/commands/test_memory_data_ops.py; awaiting end-of-batch full suite gates pass; mypy clean; bandit 1 pre-existing B101 unchanged; changed files: scripts/agent/commands/memory_data_ops.py, tests/agent/commands/test_memory_data_ops.py; awaiting end-of-batch full suite |

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
- **Requirement ID**: `REQ-005` (normal CLI output carries no credential or absolute path)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/commands/memory_data_ops.py`, `tests/agent/commands/test_memory_data_ops.py`