# Implementation Procedure: scripts/agent/config_dataclasses.py

## Goal

Replace the inert `masked_fields` default `["file_content"]` in `ToolConfig` with
the names actually masked by the sandbox path-security layer (`["content", "old_text",
"new_text"]`), so the tool-argument masking feature works against real tool arguments out of
the box.

## Scope

In scope:
- One default-value change in `scripts/agent/config_dataclasses.py`.

Out of scope:
- The parallel fallback in `scripts/agent/config_section_builders.py` (procedure 02; both
  sources must change together — see Compatibility considerations).
- `config/agent.toml` (procedure 03).
- Test updates and additions (procedures 04-06).
- Docs (procedure 07).

## Assumptions

- Assumption: `scripts/mcp_servers/file/write_tools.py` is the authoritative source for the
  argument names to mask. Verified: its `write_file` handler takes `content` (`:22`),
  `edit_file` takes `old_text`/`new_text` (`:31`), and `scripts/agent/sandbox.py:354,365`
  reads exactly `content`, `old_text`, `new_text` under the `data`/`params` keys.
- Assumption: no code anywhere depends on `file_content` being present in
  `security.masked_fields` by default — sandbox path security keys off the tool-name set
  `WRITE_TOOLS` (`sandbox.py:353`), not field names, and no test asserts the old default
  besides `tests/agent/test_config_builders.py` (procedure 04). Verified by repo-wide
  search: `file_content` as a config value appears only in the two code defaults,
  `config/agent.toml`, deployed `/opt/llm/config/agent.toml`, and `docs/23_agent/
  agent_08_03_configuration-tools-memory.md`.

## Design decisions

- Decision: the new default is the exact ordered list `["content", "old_text",
  "new_text"]`, mirroring the nested arg keys the masking layer reads. The plan froze this
  value.
- Decision: keep the existing `field(default_factory=lambda: [...])` form — mutable default
  via factory is required for a `list` dataclass field; only the list contents change.

## Alternatives considered

- Alternative: rename `file_content` to `content` only. Rejected: leaves `edit_file`'s
  `old_text`/`new_text` unmasked, keeping the feature inert for edits.
- Alternative: remove the default (empty list) and require explicit config. Rejected: makes
  the security feature off-by-default; plan froze a working default.
- Alternative: derive the defaults from a shared constant with `sandbox.py`. Rejected for
  this task: cross-module coupling for a 3-element list; can be revisited if the toolset
  grows.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

1. Open the `ToolConfig` dataclass (class starts at `:154`, field at `:182`).
2. Replace the `masked_fields` default list contents.

### Method

Change from (verified at `:182`):

```python
masked_fields: list[str] = field(default_factory=lambda: ["file_content"])
```

to:

```python
masked_fields: list[str] = field(default_factory=lambda: ["content", "old_text", "new_text"])
```

No other lines in the file change.

### Details

- The dataclass default and the `config_section_builders.py` fallback are two independent
  sources of the same value; this file covers the dataclass path only.
- `mcp_servers/github/tools_file.py:94,138` define service-internal methods named
  `file_content` (fetch file content from GitHub); they are unrelated to security config
  and must not be touched.

## Compatibility considerations

- Compatibility risk: any deployment relying on the old default value changes behavior —
  args named `content`/`old_text`/`new_text` become maskable when path security fires. This
  is the intended fix (REQ-001, AC-1).
- Coupling: `tests/agent/test_config_builders.py` pins `["file_content"]` in the
  `_TOOL_DEFAULTS` dict at `:155` (consumed by `test_empty_dict_returns_defaults`); the pin
  fails until procedures 02-04 land. Run them as one change set.
- No API/serialization changes: `masked_fields` stays `list[str]`; config loading and env
  override paths are untouched (REQ-006).

## Security considerations

- Security improvement: the default now actually masks write/edit tool payloads when path
  security triggers (REQ-001).
- Masking semantics unchanged: only the values of listed arg names are replaced with
  `"***"` when the nested path-security path fires; tool names, `ok`, and `duration_ms`
  remain visible in audit events.
- Over-masking none: `content`/`old_text`/`new_text` are write-tool payload names; no read
  tool uses them.

## Rollback considerations

- Rollback is a one-line revert of the default list in this file, together with the paired
  revert in procedures 02-03. Git-revert this change set as a unit with its tests/docs rows.
- Behavior reverts to the previous inert state (masking effectively off unless configured);
  no data or config format migration needed.

## Validation plan

1. After this change set lands, `uv run pytest tests/agent/test_config_builders.py
   tests/agent/test_tool_result_formatter.py tests/agent/test_tool_approval_preflight.py -q`
   is green (procedures 04-06 define the assertions).
2. Confirm the changed line reads `field(default_factory=lambda: ["content", "old_text",
   "new_text"])`.
3. Full gate: `uv run ruff check . && uv run mypy scripts/ tests/ --strict && uv run bandit
   -r scripts/ -ll` (mypy catches any type fallout, e.g. a missed annotation).

## Completion criteria

- `ToolConfig.masked_fields` default equals `["content", "old_text", "new_text"]`.
- The dataclass default is importable and constructible with no config file (REQ-006
  no-config default path).
- Type checks pass on the changed file.

## Out of Scope

- The `config_section_builders.py` fallback (procedure 02).
- `config/agent.toml` and the deployed copy (procedure 03).
- Test changes (procedures 04-06) and docs (procedure 07).
- Any masking-layer logic in `scripts/agent/sandbox.py` or `tool_result_formatter.py`.

## Execution Status

- [ ] Completed
- [ ] Partial — Blocked by: (state explicitly, including partial deploy state)

## Traceability

- Plan: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- Plan section: Implementation Target Files — row 1 of 7 (`scripts/agent/config_dataclasses.py`)
- Requirements: REQ-001, REQ-006
- Acceptance criteria: AC-1, AC-5, AC-6
- Procedure file: `implementations/20261025-004008_01_scripts_agent_config_dataclasses.py.md`
- Validation commands: `uv run pytest tests/agent/test_config_builders.py -q`; `uv run mypy
  scripts/ tests/ --strict`
