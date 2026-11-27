## Goal

Apply the display policy to `/mcp status`: masked values before truncation, PID/PGID retained, and
no internal log paths in normal output (REQ-005 — normal CLI output is safe for terminal capture).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The endpoint column already receives a redacted value from `scripts/agent/services/mcp_status.py`
  (document 07); this document does not re-redact it.
- The only unmasked display path in this module is `_format_health_interpretation`, which truncates
  `details_summary` at 200 characters before any masking (lines 74-107).
- Raw detail remains available only through the existing `/debug verbose` opt-in, which controls log
  level; display lines themselves are always redacted (Plan D5). No new opt-in is added here.
- Overlap with `plans/20261126-212234_cliplc011_export-command-contracts.md` on this file is
  compatible: that Plan changes command contracts, this one the display content. Sequencing
  dependency only.

## Design decisions

- Redact before truncation at the display boundary (Plan D1), so a truncated tail cannot expose part
  of a credential.
- PID and PGID stay displayed (Plan D5): the documented operator manual-cleanup path depends on them.

## Alternatives considered

- Truncating first and masking after — rejected: it can cut a masked region open and leaks the
  leading credential characters.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`
### Procedure
- In `_format_health_interpretation`, pass each emitted value through the common masker before the
  200-character truncation.
- Keep the table columns unchanged (PID retained, endpoint already redacted upstream).

### Method
- Mask `interp.details_summary` entries, `interp.dependency_summary` entries, and
  `interp.parse_failure_reason` with `_mask_secrets` from `scripts/agent/secrets_masker.py`, then
  truncate; `redact_path` (document 01) is applied to any value that is a filesystem path.

### Details
- The truncation limit and the row shape stay as they are; only the order of masking and truncation
  changes.
- No display line prints the stderr log path; the snapshot value it would print is already a logical
  identifier (document 05).

### Companion test files
- `tests/agent/commands/test_cmd_mcp.py`
  - Procedure: add display-policy assertions for masked detail text; keep the snapshot dict shape
    assertions at lines 347 and 384 unchanged (field name preserved).
  - Validation: `uv run pytest tests/agent/commands/test_cmd_mcp.py`.
  - Step 3b correction: the interpretation section is gated on the row fields
    (`dependency_summary` / `parse_failure_reason` / `details_summary`), not on `body`, so a
    body-only fixture prints no interpretation lines. The added test sets `details_summary` on the
    row and asserts the printed line is masked before the 200-character cut. `redact_path` is
    applied only when the whole display value is an absolute path; paths embedded in free text are
    masked but not path-redacted (confirmed with the user).

## Compatibility considerations

- Output text changes only; the table columns and their order are unchanged.

## Security considerations

- AC-1 boundary for `/mcp status`, the most frequently captured CLI surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_cmd_mcp.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- A health detail containing a credential is masked before it is truncated, PID/PGID are still
  displayed, and no display line contains an absolute path.

## Out of Scope

- Endpoint redaction at the data boundary (document 07).
- Command contract and export behavior (plan cliplc011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-020500 | display helper _display_value added: mask then truncate, whole-value absolute paths reduced to logical identifier; lines 74-107 claim confirmed |
| 2 | Add or update tests per Validation plan | Completed | — | 20261127-020500 | companion `tests/agent/commands/test_cmd_mcp.py` 2 tests added in TestCmdMcpStatusHealthInterpretation; 47 passed; interpretation section gated on row fields, recorded as Step 3b correction |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-095216 | 20261127-095216 | gates pass; bandit clean; mypy 3 baseline errors in test file unchanged; changed files: scripts/agent/commands/cmd_mcp.py, tests/agent/commands/test_cmd_mcp.py; awaiting end-of-batch full suite gates pass; bandit clean; mypy 3 baseline errors in test file unchanged; changed files: scripts/agent/commands/cmd_mcp.py, tests/agent/commands/test_cmd_mcp.py; awaiting end-of-batch full suite |

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
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/test_cmd_mcp.py`