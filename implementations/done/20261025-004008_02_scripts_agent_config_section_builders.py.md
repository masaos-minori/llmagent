# Implementation Procedure: scripts/agent/config_section_builders.py

## Goal

Replace the inert `["file_content"]` fallback in `_build_tool_config` with `["content",
"old_text", "new_text"]` so the builder path agrees with the `ToolConfig` dataclass default
changed in procedure 01.

## Scope

In scope:
- One default-value change in `scripts/agent/config_section_builders.py`.

Out of scope:
- The dataclass default (procedure 01) — both sources must change in the same change set.
- `config/agent.toml` (procedure 03).
- Test updates and additions (procedures 04-06).
- Docs (procedure 07).

## Assumptions

- Assumption: `_build_tool_config` (function at `:180`) is the only place in
  `config_section_builders.py` that supplies a `masked_fields` fallback. Verified: the sole
  occurrence of `"file_content"` in the file is at `:205`, inside the call
  `_get_or_default(cfg, "masked_fields", _get_list, ["file_content"])` at `:204-205`.
- Assumption: the builder does not consult the `ToolConfig` dataclass default — the fallback
  is an independent hardcoded duplicate, so leaving it unchanged while procedure 01 lands
  would produce two different defaults depending on the config path taken. Verified:
  `:204-205` hardcodes the list.
- Note: the plan's target-file table labels this site "ToolConfigBuilder.build"; the
  verified function name at HEAD is `_build_tool_config` (plan Risks name drift, snippet
  and line numbers correct).

## Design decisions

- Decision: use the identical ordered list `["content", "old_text", "new_text"]` as the
  dataclass default so both config paths converge on one value. The plan froze this value
  for both sources.
- Decision: keep the `_get_or_default(cfg, key, getter, default)` call shape; only the
  fallback literal changes.

## Alternatives considered

- Alternative: have `_build_tool_config` fall back to the dataclass default instead of a
  hardcoded literal. Rejected for this task: refactoring the fallback mechanism is a
  structural change beyond the frozen plan; the value fix is the requirement. (Worth a
  follow-up issue if the duplication causes drift.)
- Alternative: change only the dataclass default. Rejected: configs built through the
  builder path while omitting `masked_fields` would keep the inert default.

## Implementation

### Target file

`scripts/agent/config_section_builders.py`

### Procedure

1. Open `_build_tool_config` (function at `:180`, fallback call at `:204-205`).
2. Replace the fallback list literal.

### Method

Change from (verified at `:204-205`):

```python
        masked_fields=_get_or_default(
            cfg, "masked_fields", _get_list, ["file_content"]
        ),
```

to:

```python
        masked_fields=_get_or_default(
            cfg, "masked_fields", _get_list, ["content", "old_text", "new_text"]
        ),
```

No other lines in the file change.

### Details

- This is the config-file/builder path of config loading; the direct-construction path is
  covered by procedure 01. Both feed the same `masked_fields` runtime value read by every
  masking sink (`ctx.cfg.tool.masked_fields`).
- `_get_or_default` returns the fallback only when the key is absent or unset;
  user-configured lists are unaffected (REQ-006).

## Compatibility considerations

- Compatibility risk: same as procedure 01 — configs omitting `masked_fields` now get the
  working default instead of the inert one (REQ-001, AC-1).
- Coupling: `tests/agent/test_config_builders.py` pins the effective default in
  `_TOOL_DEFAULTS` at `:155` (the explicit-override case at `:192` is untouched); procedure
  04 updates the pin. Land 01-04 together.
- Explicitly configured `masked_fields` keep their configured values on both paths (AC-6).

## Security considerations

- Security improvement: the builder path now also enables real masking by default (REQ-001).
- Masking semantics unchanged (see procedure 01); only the default name list changes.
- Over-masking none: the three names are write-tool payload keys only.

## Rollback considerations

- Rollback: revert the fallback literal back to `["file_content"]` together with the revert
  of procedures 01, 03, 04. Git-revert as one change set.
- No config-format or data migration in either direction.

## Validation plan

1. After the change set lands, `uv run pytest tests/agent/test_config_builders.py -q` is
   green, including the updated `_TOOL_DEFAULTS` pin from procedure 04.
2. Confirm the changed line reads `["content", "old_text", "new_text"]`.
3. Full gate: `uv run ruff check . && uv run mypy scripts/ tests/ --strict && uv run bandit
   -r scripts/ -ll`.

## Completion criteria

- The `_build_tool_config` fallback equals `["content", "old_text", "new_text"]`.
- A config dict without a `masked_fields` key produces a `ToolConfig` whose `masked_fields`
  equal the dataclass default (both paths identical).
- Type checks pass on the changed file.

## Out of Scope

- The dataclass default (procedure 01).
- `config/agent.toml` and the deployed copy (procedure 03).
- Test changes (procedures 04-06) and docs (procedure 07).
- Refactoring the duplicated default into a shared constant (see Alternatives considered).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `_build_tool_config` fallback literal at `:204-205` | Completed | 20261025-091340 | 20261025-091340 | Procedure Before/After text matched source exactly (`_get_or_default(cfg, "masked_fields", _get_list, ["file_content"])`); fallback-only change, user-configured lists untouched (REQ-006) |
| 2 | Validation gates | Completed | 20261025-091340 | 20261025-091340 | Builder path verified by `test_empty_dict_returns_defaults` (procedure 04 pin) — 179 passed target gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A |

**Reconcile note (2026-10-25):** the source fixes for this procedure landed on `origin/master` from a separate session (fix commit `0d3ead56e`, archive commit `e6c0d6eef`). A second session independently re-executed and fully validated the same procedure on the pre-reset tree; `origin/master` was then adopted as canonical and the source state re-confirmed there with targeted tests.

## Traceability

- Plan: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- Plan section: Implementation Target Files — row 2 of 7
  (`scripts/agent/config_section_builders.py`)
- Requirements: REQ-001, REQ-006
- Acceptance criteria: AC-1, AC-5, AC-6
- Procedure file:
  `implementations/20261025-004008_02_scripts_agent_config_section_builders.py.md`
- Validation commands: `uv run pytest tests/agent/test_config_builders.py -q`; `uv run mypy
  scripts/ tests/ --strict`
