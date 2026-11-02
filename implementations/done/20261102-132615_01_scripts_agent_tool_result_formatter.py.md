# Content scrub in `mask_args`' string branch

## Goal

Add a content-pattern pass to `scripts/agent/tool_result_formatter.py` at the single choke point
— the string leaf of `_mask_value()` — calling the shared `_mask_secrets()`, so audit, runner-log
and REPL sinks inherit free-form secret scrubbing without touching any call site (Plan REQ-001
content scrub at any depth, REQ-002 key-based masking precedence, REQ-005 approval preview
untouched).

## Scope

- `from agent.secrets_masker import _mask_secrets` (new import) into the `from agent.` group.
- String branch in `_mask_value()`: `return _mask_secrets(value)` after the dict/list recursion
  checks.
- Docstrings of `mask_args()` and `_mask_value()` updated to state the content scrub.
- `mask_args` signature, key-based logic (`"***"` replacement), `build_preview`, `check_approval`
  and `tool_approval.py` unchanged (REQ-005 / AC-5).

## Assumptions

- Verified 20261102: `_mask_value` (`tool_result_formatter.py:42-56`) handles only `dict` and
  `list` and returns every other value as-is; `mask_args` (:58-64) is its only entry; the module
  has no `agent.*` import today, and `agent/secrets_masker.py` imports only `re` — no cycle, no
  layer-contract change.
- `mask_args` consumers — `tool_runner.py:317`, `tool_audit.py:60,178`, `tool_approval.py` —
  already call `mask_args` with `ctx.cfg.tool.masked_fields`; they inherit the scrub with no edit
  (reference files).
- secmask001 lands first (Plan UNK-01): the masker's colon patterns must exist before AC-1's
  `export API_KEY=abcd` / colon expectations are written; diagmask001's later extensions just
  widen coverage.
- UNK-02 recorded default: approval preview stays raw (existing documented rationale in
  `docs/23_agent/agent_08_03_configuration-tools-memory.md:32`), pending owner confirmation.

## Design decisions

- Scrub at `_mask_value`'s leaf (Plan Decision 1a): one choke point covers audit
  (`args_preview`), plan-blocked notice and runner logging while keeping the dict-in/dict-out
  shape `_extract_resource_scope` and `_bounded_preview` rely on. Scrubbing serialized JSON inside
  `_bounded_preview` (1b) would cover only the audit sink; a wrapper (1c) adds a layer.
- Key-based masking precedence is structural: the parent dict replaces a `masked_fields` key with
  `"***"` before recursion, so the leaf scrub never sees those values (REQ-002); `"***"` is not
  secret-shaped and the masker is idempotent on it (secmask001 AC-5).
- Reuse `secrets_masker._mask_secrets` as-is despite the underscore (Plan Decision 2): it is the
  only masking entry point and already imported across modules; no rename here.

## Alternatives considered

- Public-name import (mask_secrets alias) — rejected: renaming is a separate change (Plan Decision
  2); cross-module underscore import matches existing precedent.

## Implementation
### Target file
`scripts/agent/tool_result_formatter.py`

### Procedure
Add the import; insert the string branch between the `list` branch and the final `return value` in
`_mask_value()`; update both docstrings.

### Method
```python
from agent.secrets_masker import _mask_secrets
```
```python
    if isinstance(value, list):
        return [_mask_value(item, masked_fields) for item in value]
    if isinstance(value, str):
        return _mask_secrets(value)
    return value
```

### Details
- Non-string leaves (int, bool, None) and dict keys stay untouched; no mutation of `args` (the
  recursion already builds new containers).
- Performance: bounded regexes per string leaf; large strings under unlisted keys cost linear time
  — pinned by row 02's large-input test (Plan Design, Performance note).

## Compatibility considerations

- Persisted `args_preview` values that contain secret-shaped substrings change from raw to masked
  (expected fix); dict structure and the `truncated` envelope unchanged.
- All pre-existing tests in `tests/agent/test_tool_result_formatter.py`, `test_tool_audit.py`,
  `test_tool_runner.py`, `test_audit_log_format.py`, `test_tool_approval_paths.py`,
  `test_tool_output.py` pass unchanged (AC-6); the approval-preview tests must still show raw
  previews (AC-5).

## Security considerations

- Closes the Issue's leak: secrets embedded in free-form values (shell `command`, URLs) under
  unlisted keys reach persisted audit rows and logs today; they do not after this change.
- Approval preview stays raw by recorded decision (UNK-02) — the one deliberate exception, kept
  documented.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py` — green only after row 02's tests land
  (Plan Phase 1 red-first); `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_runner.py`.
- Regression: `uv run pytest tests/agent/test_audit_log_format.py tests/agent/test_tool_approval_paths.py
  tests/agent/test_tool_output.py` unchanged.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`,
  `uv run python tools/check_module_size.py`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`,
  `uv run lint-imports`.

## Completion criteria

- `mask_args({"command": "export API_KEY=abcd && run"}, [])` output contains no `abcd`;
  `masked_fields` values are still exactly `"***"`; inputs unmutated; idempotent; approval-preview
  sinks unchanged in `git diff`.

## Out of Scope

- Sink-side changes (tests only: rows 02-04); approval preview scrub (REQ-005); docs (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `_mask_secrets` import and the string branch in `_mask_value` | Completed | 20261102-175940 | 20261102-180004 | After secmask001 and rows 02-04's red tests land landed in batch 20261102-132615; red-first verified, all targets green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261102-180004 | full suite 11348 passed/8 skipped; diff-cover 100%; ruff/mypy/bandit/lint-imports/check_module_size green; docs checkers green |

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
- **Requirement ID**: REQ-001 (content scrub at any depth), REQ-002 (key-based precedence), REQ-005 (approval preview unchanged)
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: scripts/agent/tool_result_formatter.py