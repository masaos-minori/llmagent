## Goal

Collapse the duplicated `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` definitions in
`config.py` and replace the inaccurate "no authentication" runtime message with the current
loopback-defense rationale, with no behavior change.

## Scope

- Modify only `scripts/eventbus/config.py`: the duplicate constant block (lines 23-24) and
  the two runtime messages (lines 69 and 124).

## Assumptions

- Collapsing one of the two byte-identical `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH`
  assignments leaves the module-level names resolving to the same values they resolve to
  today (read at `config.py:29`, `:34`, `:280`).
- The rewritten message must retain the substring `non-loopback` because
  `tests/eventbus/test_eventbus_config.py::test_non_loopback_host_raises_value_error`
  asserts `match="non-loopback"` (lines 181, 193); the old string is not asserted anywhere.
- No test references the old message text, so the wording change cannot break a test.

## Design decisions

- **Keep the first definition, drop the duplicate.** Keep lines 13-14 and delete the
  duplicate at lines 23-24 (both are byte-identical). The names are read at
  `config.py:29,34,280`, so collapsing to one assignment is behavior-preserving.
- **Merge the two-line message into one.** Each message is currently an implicit string
  concatenation of an f-string prefix (`f"...non-loopback address {host}. "`) and a literal
  (`"The API has no authentication — this is a security risk."`). Replace BOTH lines of each
  concatenation with a single corrected f-string so the phrase "non-loopback address" is not
  duplicated.

## Alternatives considered

- Replacing only the second literal line (69/124) while leaving the f-string prefix would
  emit "Event Bus bound to non-loopback address {host}. Event Bus bound to non-loopback
  address {host} without..." — a duplicated phrase. Rejected.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Collapse the duplicate constants. Delete lines 23-24:
   ```python
   _DEFAULT_CONFIG_PATH = Path("/opt/llm/config/eventbus.toml")
   _DEFAULT_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
   ```
   Keep the identical definition at lines 13-14. Verify no other definition remains
   (`grep -n "_DEFAULT_CONFIG_PATH\|_DEFAULT_SCHEMA_PATH" scripts/eventbus/config.py` →
   definition once, reads at 29/34/280).
2. Rewrite the message in `_validate_deployment_mode` (lines 66-70). Replace the two-line
   concatenation with a single f-string:
   ```python
   raise ValueError(
       f"Event Bus bound to non-loopback address {cfg.host} without "
       "authentication configured; set auth_token or bind to loopback."
   )
   ```
3. Rewrite the message in `EventBusConfig.__post_init__` (lines 121-125) identically, using
   `self.host` instead of `cfg.host`.
4. Keep both as `ValueError` raised by the same two callers.

### Method

Two targeted edits in one file; no new symbols.

### Details

- Do not touch any import, dataclass field, or other validation branch.
- The new message states the loopback-defense rationale (ADR-013): the real exposure is a
  non-loopback bind without auth, and it is actionable ("set auth_token or bind to
  loopback"). It retains `non-loopback` for the existing test.

## Compatibility considerations

- Behavior is unchanged except the error string wording. The non-loopback-without-auth path
  still raises `ValueError`; the config test's `match="non-loopback"` still holds.

## Security considerations

- The corrected message no longer misstates the contract as "no authentication"; it points at
  the actual exposure (non-loopback bind without auth), consistent with ADR-013.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_config.py` — config loads,
  `get_config_path()`/`get_schema_path()` resolve, and
  `test_non_loopback_host_raises_value_error` still raises on non-loopback hosts.
- `uv run pytest tests/eventbus/` — full suite passes.
- `uv run ruff format scripts/eventbus/config.py` and `uv run ruff check
  scripts/eventbus/config.py`; `uv run mypy scripts/eventbus/config.py`;
  `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.

## Completion criteria

- Exactly one `_DEFAULT_CONFIG_PATH` / `_DEFAULT_SCHEMA_PATH` definition remains; both
  runtime messages state the loopback-defense rationale and contain `non-loopback`; the
  config test passes.

## Out of Scope

- Any change outside `config.py`.
- Changing the validation logic or the fail-closed non-loopback rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Collapse duplicate constants + rewrite runtime message | Pending | — | — | keep first def (13-14); merge message into one f-string |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no new assertions |
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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124800_eventbus008_documentation-comment-drift-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-100803
- **Related target files**: `scripts/eventbus/config.py`
