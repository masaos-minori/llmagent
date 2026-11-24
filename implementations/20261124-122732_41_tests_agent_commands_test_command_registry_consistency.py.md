## Goal

Extend the registry consistency test so it asserts the job commands are completion candidates and that the handler shape and mixin counts still hold after the job handler is added (REQ-010: the registry is the source of truth for command lists; AC-7).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the completion-name assertions and the mixin-count assertions at `tests/agent/commands/test_command_registry_consistency.py:155-173`.

## Assumptions

- The counts stay 10 and 8, so this test asserts the same numbers; the change is that `/jobs` is now expected in the completion set and the handler is expected inside an existing mixin.
- The handler lives in an existing mixin, per the plan decision (2026-11-24), recorded in row 10.

## Design decisions

- Assert through the public derivation (`completion_command_names()`), not by importing private constants, so the test follows the registry as the source of truth.

## Alternatives considered

- Adding a new test file for the job commands — rejected: this file already owns the completion and handler-shape contract; a second file would duplicate it.

## Implementation
### Target file
`tests/agent/commands/test_command_registry_consistency.py`

### Procedure
1. Extend the completion assertions to include `/jobs`.
2. Extend the handler-shape assertions to the `_cmd_jobs` handler in an existing mixin.
3. Keep the mixin-count assertions at 10 and 8 unchanged.

### Method

- No new fixture; the test reads the registry instance built by the existing factory path.

### Details

- The counts are asserted at `:155-164` (MRO `*Mixin` classes) and `:166-173` (direct `*Mixin` bases); both must still pass with the handler added.

### Companion test files

- None; this row is its own document. It is named by rows 10 and 11.

## Compatibility considerations

- Runs with rows 9, 10, 11 in the same phase.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_command_registry_consistency.py` | Unit | `uv run pytest tests/agent/commands/test_command_registry_consistency.py -q` | `/jobs` is a completion candidate, handler present, counts unchanged (AC-7) |

## Completion criteria

- The test fails if `/jobs` is not in the completion set or if the handler is placed outside the existing mixins, and the pinned counts still pass.

## Out of Scope

- The registration list, the handler, the completion derivation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the completion and handler-shape assertions | Pending | — | — | Phase 2 |
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
- **Requirement ID**: REQ-010 (registry as the source of command lists)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_command_registry_consistency.py`
