## Goal

- Keep the recorded size of `tools/generate_reference_table.py` in the tools baseline equal to its actual size after row 01 lands, so the size gate reports the new truth instead of a stale ceiling (`REQ-013`; `AC-011`).

## Scope
**Release unit**: manifest-contract-revision

## Assumptions

- Conditional row: it changes only if the net edit to `tools/generate_reference_table.py` moves its size. A baselined file that grows past its recorded size fails the gate, so a grown file must have its recorded size updated.
- The current recorded value equals the measured size (42762 B), so there is no headroom to absorb growth.

## Design decisions

- Update the recorded number to the post-change measured size, never above it: the baseline is a regression ceiling, and inflating it would hide later growth.
- If row 01's net edit shrinks the file (removing `_ROUTE_ROLE_MAP` handling and the `PRAGMA` branch while adding route parsing), tighten the recorded value to the new measured size.

## Alternatives considered

- Add nothing and let the gate fail: rejected - a failing gate with a stale number is noise, not a finding.
- Raise the recorded size by a margin: rejected by `REQ-013`-adjacent hygiene - a ceiling above the measured size conceals growth.

## Implementation
### Target file
`tools/check_module_size_tools_baseline.txt`
### Procedure
1. After row 01 lands, measure the file: `wc -c tools/generate_reference_table.py`.
2. If the measured size differs from the recorded `generate_reference_table.py` entry, set the entry to the measured value and keep the entry's existing rationale.
3. Leave every other baseline entry untouched.

### Method
- One number in a baseline table; no code change.

### Details
- Current baseline entry: `generate_reference_table.py 42762`; measured file size 42762 B on 2026-11-19.
- The gate command for the tools directory is `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- Row 01's net change is expected to grow the file (route-decorator parsing plus the second agent document registration outweigh the removed constant read and `PRAGMA` branch), so expect a raised number; the exact value is measured, not predicted.

## Compatibility considerations

- The baseline file is read by the CI size gate only; no runtime component reads it.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — passes with the recorded size equal to the measured size (static gate: tools size gate)

## Completion criteria

- The recorded size equals the measured size and the tools size gate passes.

## Out of Scope

- Any other baseline entry.
- Raising `MAX_SIZE` or adding exceptions elsewhere.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure the file after row 01 | Pending | — | — | one measurement |
| 2 | Update or tighten the recorded entry | Pending | — | — | one number |
| 3 | Run the tools size gate | Pending | — | — | gate command above |

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
- **Requirement ID**: `REQ-013` (generated artifacts change only by regeneration)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `tools/check_module_size_tools_baseline.txt`
