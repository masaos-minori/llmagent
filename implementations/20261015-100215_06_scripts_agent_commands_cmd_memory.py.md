## Goal

Rework the `/memory` subcommand dispatch to the spec subcommand set: no-arguments
runs `status`, the memory-layer-disabled path prints M-02 for non-status
subcommands, and the dispatch lists exactly the spec commands (REQ-003).

## Scope

Modify `scripts/agent/commands/cmd_memory.py` only: rewrite the dispatch dict,
change the no-subcommand default to `status`, and switch the disabled-layer
message to M-02.

## Assumptions

- The spec subcommand set is exactly: `status`, `list`, `delete`, `pin`, `unpin`,
  `prune`, `reindex`, `rebuild` (REQ-003).
- Subcommands other than `status` are removed: `search`, `show`,
  `check-consistency`, `import-jsonl`, `rebuild-fts`, `rebuild-vec`.
- `reindex` delegates to `memory_rebuild_ops.reindex()` (row 8).
- `M-02` is a new message not yet defined in code; the emit is wired by the
  caller. The normative target table/behavior lives in
  `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`.

## Design decisions

- Replace the dispatch dict with the 8 spec commands.
- Move the no-subcommand default from printing `_MEMORY_HELP` to running
  `_memory_status`.
- Keep `status` reachable even when the layer is disabled; for every other
  subcommand when disabled, emit M-02 and return without touching data.

## Alternatives considered

- Keeping `help` as a subcommand: rejected. REQ-003 specifies "exactly" the eight
  commands; anything else must raise `UnknownSubcommandError`.

## Implementation

### Target file

`scripts/agent/commands/cmd_memory.py`

### Procedure

1. Change the no-subcommand default to `status`.
2. Switch the disabled-layer branch to M-02.
3. Rewrite the dispatch dict to the spec set.

### Method

- In the dispatch method, change the guard so a bare invocation runs status:

  ```python
  if not sub:
      self._memory_status(ctx.services_required.memory)
      return
  ```

  (Drop the `sub == "help"` help-printing branch; `help` is not a spec
  subcommand.)

- Change the disabled-layer branch so non-status subcommands print M-02:

  ```python
  if mem is None:
      self._out.write("  [memory] M-02 ...")   # M-02: memory layer disabled
      return
  ```

  (`M-02` text is defined by the spec doc; wire the message constant/emit.)

- Replace the dispatch dict (currently listing 12 entries) with:

  ```python
  dispatch = {
      "list": lambda: self._data_ops.memory_list(mem, sub_tokens),
      "delete": lambda: self._data_ops.memory_delete(mem, sub_tokens),
      "pin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=True),
      "unpin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=False),
      "prune": lambda: self._data_ops.memory_prune(mem, ctx, sub_tokens),
      "reindex": lambda: self._rebuild_ops.reindex(mem, sub_tokens),
      "rebuild": lambda: self._rebuild_ops.rebuild(mem, sub_tokens),
  }
  ```

  (`status` is handled before the dict, as today.)

### Details

- `reindex` routes to `memory_rebuild_ops.reindex()` (row 8); `rebuild` routes to
  `memory_rebuild_ops.rebuild()`.
- `UnknownSubcommandError(sub, tuple(dispatch.keys()))` now reports the reduced
  set automatically.
- `_MEMORY_HELP`: verify whether it is still reachable after this change; if dead,
  remove it (and any test that asserts on it). If the spec doc keeps a help path,
  follow that doc.
- Short-ID routing (M-03/M-04) is performed inside the
  `memory_data_ops` handlers (row 7); this file only selects the handler.

## Compatibility considerations

The dispatch set shrinks; callers/tests using the removed subcommands
(`search`, `show`, `check-consistency`, `import-jsonl`, `rebuild-fts`,
`rebuild-vec`) must be updated. No-subcommand now shows status instead of help.

## Security considerations

N/A: dispatch restructuring only.

## Rollback considerations

Revert the commit; the dispatch rewrite is contained here.

## Validation plan

- `pytest tests/agent/commands/test_cmd_memory.py` covers disabled-layer M-02,
  no-subcommand→status, removed-subcommand rejection, short-ID routing.
- Full suite: `ruff`, `mypy --no-namespace-packages scripts/`, `lint-imports`,
  `bandit`, `pytest` with sandbox config.

## Completion criteria

`/memory` with no args shows status; with the layer disabled only `status` runs
and others print M-02; the dispatch accepts exactly the eight spec subcommands.

## Out of scope

The rebuild/reindex handlers (`memory_rebuild_ops.py`), short-ID resolution and
handlers (`memory_data_ops.py`), and the help text in the registry
(`command_defs_list.py`) are separate target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rework dispatch to spec set; no-args→status; disabled→M-02 | Pending | — | — | REQ-003 |
| 2 | Add/update dispatch tests | Pending | — | — | `test_cmd_memory.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-009`
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261015-074949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261015-100215
- **Related target files**: scripts/agent/commands/cmd_memory.py
