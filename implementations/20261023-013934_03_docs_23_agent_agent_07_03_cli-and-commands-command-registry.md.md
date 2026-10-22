## Goal

Document the REPL output tag taxonomy (`[fatal]`, `[error]`, `[usage]`, `[non-fatal]`) and the
component that emits each tag, and state that a command-error surface is not a turn failure
(`REQ-008`).

## Scope

In scope: add an "Output Tags and Severities" section to
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` naming each tag and its
emitter, and stating that a command error is not a turn failure. Out of scope: changing any tag
value (`scripts/agent/output_tags.py`), the `registry.py` implementation (`REQ-001`–`REQ-005`,
separate document), or the test additions (`REQ-007`, separate document).

## Assumptions

- The four tags already exist as distinct `OutputTag` enum values (`FATAL`=`[fatal]`,
  `NON_FATAL`=`[non-fatal]`, `ERROR`=`[error]`, `USAGE`=`[usage]`) and must not be renamed or
  altered.
- This chapter is the canonical home for the `CommandRegistry` tag contract: `docs/00_index.md`
  maps "Agent REPL slash commands (`CommandRegistry`)" to it, and no other chapter documents the
  taxonomy today.

## Design decisions

- **Place the section under the `CommandRegistry` chapter**, since the command-boundary handling
  lives there and a reader investigating a command error lands here first.
- **Assert the boundary, not message wording.** The section states *which component emits each
  tag* and that command errors are not turn failures; it does not pin exact message bodies, so it
  stays stable if wording changes.

## Alternatives considered

Adding the taxonomy to the broader REPL-IO chapter (`agent_07_05`) instead would split the
`CommandRegistry` contract across two chapters; keeping it in this chapter keeps the dispatch
behavior and its output contract co-located.

## Implementation

### Target file

`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure

1. Read the current chapter; confirm it has no tag-taxonomy section (`grep -n "error\|fatal\|usage"`
   matches only the usage-line authoring sentence at L63).
2. Add a `## Output Tags and Severities` section after "Key Constraints" and before
   "Known Limitations".
3. In that section:
   - List each tag and its emitter:
     - `[fatal]` — emitted by `ReplInputLoop._surface_turn_error` for turn-level failures that do
       not originate from a command handler (`repl_input_loop.py`).
     - `[error]` — emitted by `CommandRegistry` (via `OutputPort.write_error`) for a command
       handler exception that is not a command-domain validation/parse error or a `sqlite3.Error`
       (e.g. a runtime error inside a handler), and by the storage path for `sqlite3.Error` with a
       possibly-partial-effect statement.
     - `[usage]` — emitted by `CommandRegistry` (via `OutputPort.write_validation_error`) for a
       command-domain validation/parse error (`CommandValidationError`, `CommandParseError`, and
       subclasses such as `UnknownPresetError` / `UnknownTierError`).
     - `[non-fatal]` — emitted for non-blocking runtime notices (e.g. disabled-memory warning).
   - State explicitly that a command-handler error is handled at the `CommandRegistry` dispatch
     boundary and is **not** a turn failure: it renders `[error]`/`[usage]` and returns a matched
     result, so `_surface_turn_error` (`[fatal]`) is not reached.
   - Note that tag values live in `scripts/agent/output_tags.py` and are not modified by this
     change.
4. Verify the touched chapter against the docs checkers in the Validation plan.

### Method

Append the new section as Markdown under the existing "Key Constraints" section. All changes are
confined to this documentation file.

### Details

- Reference the source of truth for tag values (`scripts/agent/output_tags.py`) and for the
  `[fatal]` emitter (`scripts/agent/repl_input_loop.py`) so readers can trace the contract.
- Do not enumerate every tag in `OutputTag`; document only the four in the command/turn surface
  (`[fatal]`, `[error]`, `[usage]`, `[non-fatal]`) plus the note that others exist.

## Compatibility considerations

Documentation-only change; no code, config, or symbol is affected.

## Security considerations

`N/A`: no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py` ; `uv run python tools/check_docs_structure.py` ;
  `uv run python tools/check_docs_content_policy.py` ;
  `uv run python tools/check_docs_consistency.py --domain agent` ;
  `uv run python tools/check_docs_japanese.py` — all pass; no port/config/symbol drift reported
  for the touched chapter.
- Cross-check `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` and
  `docs/23_agent/agent_07_02_cli-and-commands-cliview.md` for any assertion of the old
  single-`[fatal]` behavior; edit only if a checker reports drift.

## Completion criteria

The chapter contains an "Output Tags and Severities" section that names `[fatal]`, `[error]`,
`[usage]`, and `[non-fatal]`, attributes each to its emitting component, and states that a
command error is not a turn failure; the docs checkers pass with no drift for this chapter.

## Out of scope

`scripts/agent/commands/registry.py` (`REQ-001`–`REQ-005`),
`tests/agent/commands/test_command_registry_dispatch.py` (`REQ-007`),
`scripts/agent/output_tags.py` (tag strings unchanged),
`docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` and
`docs/23_agent/agent_07_02_cli-and-commands-cliview.md` (no edit unless a checker reports drift).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document the REPL tag taxonomy in `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (`REQ-008`) | Pending | — | — | AC-6 |
| 2 | Add or update tests per Validation plan | N/A: documentation-only row | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs checkers |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: this document is the documentation | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains in this Plan | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261021-093421_cmd001-command-failures-surface-as-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-110616_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-013934
- **Related target files**: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
