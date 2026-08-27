## Goal

Rewrite the `blob_bytes ≠ 1536` troubleshooting row in
`docs/05_agent_10_05_operations-and-observability-monitoring.md` (REQ-003) so it
no longer hardcodes a stale expected value, per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the Troubleshooting table's `blob_bytes` row (verified at line 29 as
  of 2026-08-27) only.
- Out of scope: any other row of the table; any other section of this document.

## Assumptions

- `scripts/db/store_protocols.py::get_embedding_dims()` returns a fixed constant
  `QWEN3_EMBEDDING_DIMS = 1024` (re-verified 2026-08-27) — the current `1536`
  byte figure (implying 384 float32 dimensions: `384 * 4 = 1536`) is stale;
  `1024 * 4 = 4096` would be the current correct byte count, but per this Plan's
  Implementation intent, the fix should reference the function, not hardcode a
  new number, so a future constant change does not require another doc edit.

## Design decisions

- Replace the hardcoded `1536`/`384` figures with wording that names
  `scripts/db/store_protocols.py::get_embedding_dims()` (and, if useful,
  `get_embedding_bytes()`) as the source of truth for the expected byte count —
  per REQ-003's exact specification ("verify the BLOB byte count matches the
  dimension returned by `get_embedding_dims()`").

## Alternatives considered

- Simply updating `1536` to the new correct value (`4096`) was considered and
  rejected — per this Plan's Implementation intent, restating a specific number
  reproduces the same staleness risk if the constant changes again; naming the
  function as the source of truth is the chosen, more durable fix.

## Implementation
### Target file
`docs/05_agent_10_05_operations-and-observability-monitoring.md`

### Procedure
1. Re-confirm the current line number for the `blob_bytes` troubleshooting row
   immediately before editing (verified at line 29 as of 2026-08-27).
2. Rewrite the row per Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` (or
   `uv run` equivalent) and confirm no new warning/error beyond the recorded
   baseline (23 warnings, none embedding-related).

### Method
Direct text edit (Edit tool) — one table row.

### Details
Current row (verified 2026-08-27, line 29):
```
| `blob_bytes` ≠ 1536 | Embedding dimension mismatch | Verify if the embedding model outputs 384 dimensions |
```
Replace with:
```
| `blob_bytes` ≠ expected | Embedding dimension mismatch | Verify the BLOB byte count matches `scripts/db/store_protocols.py::get_embedding_dims()` (returns a fixed code constant, not a config value) |
```
Adjust exact wording to match this table's column conventions (verify the first
column's format against neighboring rows — some may use a specific comparison
operator or code-formatted condition).

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-row text revert via `git diff`/`git checkout -- <path>`; independent of
  the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/05_agent_10_05_operations-and-observability-monitoring.md` | Manual diff | `git diff docs/05_agent_10_05_operations-and-observability-monitoring.md` | Troubleshooting row no longer hardcodes `1536`/`384` |
| `docs/05_agent_10_05_operations-and-observability-monitoring.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain agent` (or `uv run` equivalent) | No new warning/error beyond the 23-warning baseline |

## Completion criteria

- The troubleshooting note no longer hardcodes `1536`/`384` as the expected
  value.

## Out of scope

- Any other row of the Troubleshooting table.
- Any other section of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Rewrite the `blob_bytes` row | Pending | — | — | |
| 3 | Run `check_docs_consistency.py --domain agent` | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20260821_10_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-151220_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112854
- **Related target files**: `docs/05_agent_10_05_operations-and-observability-monitoring.md`
