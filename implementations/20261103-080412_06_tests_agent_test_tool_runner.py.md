## Goal
Add a round-level regression test proving a duplicated call id executes neither call with wrong
arguments and never reaches the approval prompt (REQ-001, REQ-003; AC-001, AC-002).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `tests/agent/test_tool_runner.py` row (seq 06) of
`plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md`. This row is an own
procedure document (not a companion) because the file is also a target row of other Plans. Executed
after seq 01 and seq 02 land, so the test exercises the final behavior end-to-end.

## Assumptions
- The file's existing stub registries/gateways (`ctx.services_required.gateway` stubs) can record
  executed arguments, so the test can assert what actually ran.
- The overlap with `inflightcancel001`/`blockio001`/`idemaudit001` Plans on this file is additive:
  the new test class touches only duplicate-id flow.

## Design decisions
- Test asserts three things in one round: (a) neither call executes twice or with the other
  call's arguments (stub gateway call log), (b) the approval gate is never prompted for either
  occurrence, (c) each declared id receives a tool result row reporting the `duplicate_id` (new)
  rejection (pairing semantics, REQ-003/D4).

## Alternatives considered
- Covering this only with unit tests in the companion files: rejected — the misexecution hazard
  is the cross-call spec collapse in `tool_runner.py`, which only a round-level test pins.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
1. Add a test class (pattern of the existing round-flow tests) building an assistant message with
   two tool calls sharing one id but different arguments.
2. Drive the round with the stub gateway recording `(call_id, arguments)` pairs.
3. Assert: no recorded execution used the shared id with either argument set in the collapsed
   spec's place; the approval stub recorded zero prompts; the resulting tool rows for both
   declared occurrences report the duplicate rejection.

### Method
Round-level test on existing harness fixtures; no production code change in this document.

### Details
- Keep the test deterministic: fixed ids and args, no timing assumptions.
- If the harness needs an approval-gate stub that fails the test when invoked, reuse the existing
  denial-path fixtures' pattern.

## Compatibility considerations
- Must not alter existing runner tests; new class only.

## Security considerations
- Pins the regression that closes the misexecution hazard.

## Rollback considerations
- Test-only file; removal restores prior coverage state.

## Validation plan
1. `uv run pytest tests/agent/test_tool_runner.py -q` green after seq 01/02 land; the new test
   fails (misexecution or silent drop) without them.
2. Full validation sequence per `rules/toolchain.md` at the end of the plan's execution.

## Completion criteria
- AC-001 and AC-002 are pinned at round level.

## Out of Scope
- Production code changes (seq 01/02), documentation (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261101-073525_dupcallid001_duplicate-call-id-misexecution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-080412
- **Related target files**: `tests/agent/test_tool_runner.py`
