## Goal

- Remove the history-style "Transcribed 2026-10-30" comment from `config/adr_authority.toml` per the Plan (`REQ-020`): the toml is the hand-maintained input model of `tools/generate_adr_authority.py`, and history-style notes are out of place under the Current-Specification-Only policy.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: comment-only removal in the target file (Plan target-table row: "comment cleanup").
- Out of scope: any change to the authority-matrix data rows, and the guarded blocks in `docs/10_adr/adr_01_index.md` (generated artifacts, `REQ-022`).

## Assumptions

- `tools/generate_adr_authority.py`'s docstring confirms the toml is the hand-maintained input model (Plan row 4 evidence, verified 2026-11-19); comments in the toml are not consumed by any tool.
- The defective text is line 9: `# Transcribed 2026-10-30 from the prose authorities in docs/10_adr/adr_01_index.md (ADR List)` plus its continuation line 10.

## Design decisions

- Delete the two-line "Transcribed ..." note (lines 9–10) outright rather than rephrasing it: the provenance it records is history, which the governance policy (governance_01 Current-Specification-Only) excludes from spec files. The adjacent "# --- Authority matrix (ADR-016 Decision 1 ...) ---" line is a normative citation, not history, and stays.

## Alternatives considered

- Move the provenance note into a docs file — rejected: no requirement records transcription history; `REQ-020` says drop it.

## Implementation
### Target file
`config/adr_authority.toml`
### Procedure
1. Delete lines 9–10 (the "Transcribed 2026-10-30 ..." note and its continuation).
2. Leave every `[[authority]]`-style data row and the ADR-016 citation comment untouched.
3. Run the drift gates.

### Method
- Comment-only edit; validate by exit codes of the existing gates rather than by new tests (`AC-15`, `T14`).

### Details
- No other line of the file changes; the diff must be comment lines only.

## Compatibility considerations

- Consumers (`tools/generate_adr_authority.py`, `tools/check_adr_authority.py`, guarded blocks in `docs/10_adr/adr_01_index.md`) parse data rows only; comment removal cannot change generated output (`REQ-022`: generated artifacts must not be hand-edited and drift gates must pass).
- rsynced by the deploy flow; no new deploy copy lines (Plan Assumptions).

## Security considerations

- N/A: comment-only configuration change.

## Rollback considerations

- Single-commit revert of the removed comment lines.

## Validation plan

- `uv run python tools/generate_adr_authority.py --check` — exit 0 (`AC-15`, `T14`).
- `uv run python tools/check_adr_authority.py` — exit 0 (`T14`).
- `git diff` shows comment lines only (`AC-15`).
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- `AC-15` holds: the file contains no history-style comment; both adr_authority gates exit 0; no generated artifact changed.

## Out of Scope

- The `REQ-017` governance proposal (seq 05) and any authority-data change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the "Transcribed 2026-10-30" note (lines 9–10) (`REQ-020`) | Pending | — | — | |
| 2 | Run `generate_adr_authority.py --check` and `check_adr_authority.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-020` (drop history-style note)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `config/adr_authority.toml`
