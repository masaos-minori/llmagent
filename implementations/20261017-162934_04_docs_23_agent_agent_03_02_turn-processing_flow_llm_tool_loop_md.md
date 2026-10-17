# Implementation Procedure — `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`

## Goal

Update the Known Limitations bullets to reference the new startup diagnostic that reports the
effective on/off state of the retry-suppression and empty-result guards (`REQ-006`).

## Scope

Modify only the Known Limitations section of `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`. Reference the new startup diagnostic next to the existing
`> 0` effectiveness bullets. Do NOT change other sections. Doc-only change.

## Assumptions

- The Known Limitations section currently contains:
  - "Retry suppression is only effective if `tool_error_retry_max > 0`."
  - "Empty result repeat detection is only effective if `tool_empty_result_max_repeats > 0`."
- Row 1 adds a `ToolLoopGuard.report_effective_state()` startup diagnostic that logs the
  effective on/off state for the resolved config.
- Note: the plan cited doc lines 117–118; the bullets actually sit in the `## Known
  Limitations` heading (locate by content, not line number).

## Adversarial verification findings (plan discrepancies)

- **No discrepancy.** Verified the two bullets exist under `## Known Limitations`. The plan's
  line numbers (117–118) are slightly off relative to the current file; reference by content.

## Design decisions

- Append a sentence to each existing bullet noting that the effective state is reported once
  at startup via the guard's diagnostic log line (e.g. `tool_loop_guard: startup diagnostic:
  retry_suppression=on(1) empty_result_detection=off(0)`).
- Keep the existing `> 0` effectiveness wording intact; add the observability note as an
  additional clause.

## Alternatives considered

- A separate Known Limitations bullet vs. extending the existing ones: extend the existing
  bullets so the semantic (`> 0`) and its observability stay co-located.

## Implementation

### Target file

`docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`

### Procedure

1. Locate the `## Known Limitations` section.
2. After "Retry suppression is only effective if `tool_error_retry_max > 0`.", append a
   clause such as:
   " The effective on/off state is reported once at startup via the tool loop guard
   diagnostic log line (`tool_loop_guard: startup diagnostic: retry_suppression=<on|off>(<n>)
   empty_result_detection=<on|off>(<n>)`). See `scripts/agent/tool_loop_guard.py`."
3. After "Empty result repeat detection is only effective if `tool_empty_result_max_repeats > 0`.",
   append a parallel clause referencing the same diagnostic.
4. Confirm the existing `> 0` wording is preserved verbatim.

### Method

Edit the two Known Limitations bullets; no code change.

### Details

- Match the document's existing prose style.
- Keep the diagnostic name consistent with row 1's emit.

## Compatibility considerations

Doc-only; no runtime effect.

## Security considerations

N/A (documentation only).

## Rollback considerations

Revert the commit to the doc file.

## Validation plan

- Read the Known Limitations section; confirm both bullets reference the diagnostic and the
  `> 0` wording is intact.
- No command required (documentation change).

## Completion criteria

Both Known Limitations bullets reference the startup diagnostic while preserving the
original `> 0` effectiveness semantics.

## Out of scope

The guard code (separate row), the config docstrings (separate row), the test file
(separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Known Limitations bullets to reference the diagnostic | Pending | — | — | doc-only |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: test file is a separate row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-006` (Known Limitations references the diagnostic)
- **Source issue**: `issues/done/20261017-123510_retrysup01_make-retry-suppression-and-empty-result-defaults-observable.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-153234_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162934
- **Related target files**: `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
