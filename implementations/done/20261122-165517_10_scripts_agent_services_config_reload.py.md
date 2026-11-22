## Goal

Replace the raw prompt-key branch in the reload path with the typed single-source read, keeping the mutation in the commit phase only (REQ-007, reload path).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Prompt content is no longer part of `ConfigReloadRequest`'s config dict after the config-layer removal, so the reload path reads the single source directly through the typed model in row 03 (Plan Assumptions).
- Needs confirmation (non-blocking): the trigger for a prompt change must be redefined because `new_cfg` can no longer contain the removed keys. The procedure below takes "read the single source in the candidate phase and compare with `ctx.conv.system_prompt_content`" as the design, consistent with REQ-007 and the existing observable hot-reloadable behaviour (Plan UNK-01 default). If the owner decides the prompt is startup-only, this row becomes a deletion instead and the reload test asserts only the absence of a prompt mutation.
- The two-phase prepare/commit model already implemented here is reused unchanged; `cliplc005` is not a blocker (Plan Out-of-Scope).
- The outcome report shape (`applied`, `needs_restart`, `skipped`, `startup_only`, `always_live`) is unchanged; the prompt mutation stays unclassified in the report, as it is today.

## Design decisions
- The candidate phase resolves the prompt value through the typed model and stores it as a pending conversation update; the commit phase performs the only mutation, so a prepare-phase failure leaves `ctx.cfg` and `ctx.conv` untouched (AC-4).
- Change detection compares the resolved value with the runtime value rather than reading a config key, because the config dict no longer carries prompt content.
- A read error at the source boundary propagates as the reader's error in the candidate phase, before any mutation, matching REQ-001's read-boundary contract.

## Alternatives considered
- Reusing the registry classification for the prompt through a synthetic entry: rejected, the registry has no prompt entry after row 07 and the prompt is not a config section.
- Applying the prompt update in the candidate phase: rejected, that breaks the commit-phase-only invariant AC-4 tests.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`
### Procedure
Remove the prompt branch that reads `new_cfg`, add a single-source read in the candidate phase, keep the pending-update mechanism.
### Method
- Delete the `if "system_prompt_tool" in new_cfg:` branch (lines 138-142).
- In the same candidate phase, resolve the prompt name (`ctx.conv.system_prompt_name`, default `default`) through the typed model from row 03 and build the pending update only when the resolved content differs from `ctx.conv.system_prompt_content`.
- Leave the commit phase unchanged: `for update in pending_conv_updates: update()` stays the only path that mutates the conversation state.
### Details
- `scripts/agent/conversation_state_manager.py` (lines 81-90) syncs `history[0]` from the runtime value; it is unaffected and must not be touched.
- `scripts/agent/services/session_restore.py` (lines 182-188) reads the runtime value only; unaffected.
- No new entry is added to the outcome report; the test in row 15 asserts the report shape is unchanged.

## Compatibility considerations
- `/reload` keeps the observable behaviour that the prompt is hot-reloadable; the classification report does not list the prompt as a config field after row 07 removes the registry entries.
- `/reload` callers see no change in the report format or in command output.

## Security considerations
- A missing or invalid single source fails in the candidate phase with no live mutation, so a bad file cannot leave the conversation state half-updated.

## Rollback considerations
- Reverting this row restores the raw-key branch; it must be reverted together with rows 03, 04, 05, 06 and 11, otherwise the prompt has no source.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py` (row 15): prompt change applied at commit, prepare-phase failure leaves `ctx.cfg` and `ctx.conv` untouched, outcome shape unchanged.
- `uv run ruff check .`, `uv run mypy scripts/`, `uv run lint-imports`.

## Completion criteria
- The prompt value reaches the conversation state only through the typed model and only in the commit phase; a prepare-phase failure mutates nothing; the outcome report shape is identical (AC-4).

## Out of Scope
- Typed staged reload and rollback (`cliplc005`).
- Prompt-name selection features (Plan UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-180805 | 20261122-180805 | change-detection trigger recorded in Assumptions batch-run; raw-key branch replaced with typed read in candidate phase; mutation stays in commit phase; ruff/mypy pass |
| 2 | Add or update tests per Validation plan | Completed | 20261122-180805 | 20261122-180805 | covered by row 15 no test change here; covered by row 15 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-180805 | 20261122-183359 | tests are row 15; validation deferred to end-of-batch run end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-007` (prompt change applied only in the commit phase through the same typed model)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/services/config_reload.py`