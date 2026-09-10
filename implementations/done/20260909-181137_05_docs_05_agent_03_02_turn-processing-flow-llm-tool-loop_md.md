# Implementation Procedure: Update Documentation for Empty Result Repeat Guard

## Goal

Update the documentation for ToolLoopGuard to include the new fifth guard (empty result repeat detection) and its corresponding hint.

## Scope

- Modify `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`: add documentation for the new guard and hint.
- No other files modified in this document.

## Assumptions

- The new guard follows the same naming convention as existing guards (e.g., "Empty Result Repeat").
- The hint content should follow the same format as existing hints.
- The documentation should be updated to reflect the current state of the codebase.

## Design decisions

- Add the new guard to the list of four existing guards (making it five total).
- Add the new hint to the hints table.
- Update the operational notes section to mention the new guard.
- Keep the documentation concise and focused on the guard's purpose.

## Alternatives considered

1. **Create a separate document**: Would isolate the new guard's documentation but would fragment the guard documentation across multiple files.
2. **Use a diagram**: Would provide visual clarity but would require additional maintenance effort.
3. **Add to the Known Limitations section**: Would highlight the limitation but wouldn't provide a complete description of the guard's behavior.

## Implementation

### Target file
`docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md`

### Procedure

1. Update the list of guards to include the new fifth guard.
2. Add the new hint to the hints table.
3. Update the operational notes section to mention the new guard.
4. Update the Known Limitations section if applicable.

### Method

#### Update the list of guards

```markdown
Within the tool loop, an LLM may potentially call the same tool infinitely. To prevent this, `ToolLoopGuard` sequentially executes five guards:

1. **Cycle Detection** — If the same set of tool calls is repeated within the last $N$ rounds.
2. **Deduplication** — If the same `(name, args)` is detected more than a certain number of times.
3. **Retry Suppression** — If a failed tool call is invoked again with the same arguments.
4. **Consecutive Errors** — If all tools in a round fail consecutively for a certain number of rounds.
5. **Empty Result Repeat** — If the same tool returns empty results repeatedly within a single turn.
```

#### Add the new hint to the hints table

```markdown
| Guard Type | Hint Content |
|---|---|
| cycle | "A cyclic planning pattern was detected: the same set of tool calls is being requested repeatedly across multiple rounds." |
| dedup | "The same tool was called with identical arguments multiple times." |
| retry | "A tool call that previously failed is being retried with the same arguments." |
| empty_result_repeat | "A tool returned empty results repeatedly within a single turn." |
```

#### Update the operational notes section

```markdown
## Operational Notes

- The final answer fallback after a guard trigger uses a temporary system message to prompt the LLM to respond without tools.
- Incomplete outputs can be checked via the `/stats` command but cannot be accessed via normal conversation history.
- Empty result repeat detection requires `tool_empty_result_max_repeats > 0` to be enabled.
```

### Details

- Added "Empty Result Repeat" as the fifth guard in the list.
- Added "empty_result_repeat" hint to the hints table.
- Updated the operational notes section to mention the new guard's configuration requirement.
- Kept the documentation concise and focused on the guard's purpose.

## Compatibility considerations

- Updating documentation does not change the codebase behavior.
- The new guard's documentation should be consistent with existing guard documentation.
- The hint content should follow the same format as existing hints.

## Security considerations

- No security impact. This change only affects documentation.

## Rollback considerations

- Revert: remove the new guard entry from the list and the new hint from the table.
- No migration needed since the default `None` value ensures backward compatibility.

## Validation plan

1. Verify the new guard is listed in the guards section.
2. Verify the new hint is included in the hints table.
3. Verify the operational notes section mentions the new guard.
4. Verify the documentation is consistent with existing guard documentation.

## Completion criteria

- [ ] New guard is listed in the guards section.
- [ ] New hint is included in the hints table.
- [ ] Operational notes section mentions the new guard.
- [ ] Documentation is consistent with existing guard documentation.

## Out of scope

- Implementing the guard logic itself (covered in `scripts/agent/tool_loop_guard.py`).
- Adding the config field (covered in `scripts/agent/config_dataclasses.py`).
- Wiring tool results into guard state (covered in `scripts/agent/tool_runner.py`).
- Updating tests (covered in respective documents).

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
- **Requirement ID**: REQ-001 (Detect repeated empty tool results within a single turn)
- **Source issue**: issues/done/20260908-194034_toolloop002_detect-empty-tool-result-repetition.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-221112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-181137
- **Related target files**: docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md
