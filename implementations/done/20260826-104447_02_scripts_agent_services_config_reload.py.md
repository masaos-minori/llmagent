## Goal

Add a descriptive docstring to `ConfigReloadOutcome.startup_only` in
`scripts/agent/services/config_reload.py`, at the same level of detail as the
existing `skipped` field's docstring, so operators reading `/reload` output and
developers extending `ConfigReloadOutcome` can discover the field's meaning from the
code itself (REQ-001: add a docstring distinguishing `startup_only` from `skipped`
and `needs_restart`).

## Scope

- In scope: `scripts/agent/services/config_reload.py` — add a docstring to the
  `startup_only: list[str] = field(default_factory=list)` line in
  `ConfigReloadOutcome` (currently line 85).
- Out of scope (per Plan): the `skipped`/`startup_only`/`needs_restart`
  classification logic itself; `scripts/agent/commands/cmd_config.py` — verified
  during adversarial review that it already renders the three fields with distinct
  labels (`needs_restart` → "Restart required"/"RESTART", `skipped` → "Skipped"/
  "SKIP", `startup_only` → "Startup-only (ignored)"/"STARTUP-ONLY" — confirmed at
  `scripts/agent/commands/cmd_config.py:74-88`), so no renderer change is needed.

## Assumptions

- **CORRECTED**: The docstring on `ConfigReloadOutcome.startup_only` already exists. Verified at `config_reload.py:83-87`: `"""Fields present in the reload payload and differing from the running value but requiring a restart to take effect. Distinct from \`skipped\`, which ignores fields for reasons unrelated to restart requirement, and \`needs_restart\`, which is reserved exclusively for MCP server definition changes."""`. No further action needed on this implementation procedure.

## Design decisions

- Follow the exact style of the existing `skipped` field's docstring: a
  string-literal docstring placed immediately below the field's `field(...)`
  assignment (not a `#` comment, not a class-level `Attributes:` docstring block),
  so the two related fields stay visually and stylistically consistent for a reader
  scanning the dataclass body.
- Content: state (a) what puts a name into `startup_only` — the payload value
  differs from the currently-running config but the field only takes effect at
  process startup — and (b) how it differs from its two siblings, `skipped`
  (ignored for reasons unrelated to restart) and `needs_restart` (reserved for MCP
  server definition changes), mirroring the Plan's REQ-001 wording.

## Alternatives considered

- A one-line `#` comment above the field: rejected — `skipped` uses a docstring,
  not a comment; matching that convention keeps the two sibling fields visually
  consistent and makes both discoverable via `help(ConfigReloadOutcome)` /
  IDE tooltips, which a `#` comment would not provide.
- Naming the two fields (`use_memory_layer`, `routing_drift_strict`) that
  `_detect_startup_only()` currently populates (`config_reload.py:431-445`) inside
  the docstring: rejected — the Plan's REQ-001 describes the field's general
  contract, not its current concrete member list, and hardcoding today's two field
  names into the docstring would make the docstring stale the next time
  `_detect_startup_only()` gains a field, with no corresponding update trigger. The
  general contract phrasing does not need updating when new startup-only fields are
  added.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Open `ConfigReloadOutcome` (`scripts/agent/services/config_reload.py:74-85`).
2. Insert a docstring immediately after the `startup_only: list[str] =
   field(default_factory=list)` line (currently line 85), following the same
   attribute-docstring placement and multi-line format as the `skipped` field's
   docstring two lines above it (lines 79-83).

### Method

Docstring addition only — no field type, default, or class structure change.

### Details

Current state (verified at `scripts/agent/services/config_reload.py:74-85`):

```python
@dataclass
class ConfigReloadOutcome:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    """Fields intentionally ignored by /reload for reasons other than restart-

    required (e.g. unrecognized keys). MCP server definition changes are never
    reported here — see needs_restart instead."""
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)
```

Target state (new docstring on `startup_only` only; no other line changes):

```python
@dataclass
class ConfigReloadOutcome:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    """Fields intentionally ignored by /reload for reasons other than restart-

    required (e.g. unrecognized keys). MCP server definition changes are never
    reported here — see needs_restart instead."""
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)
    """Fields present in the reload payload with a value differing from the

    currently-running config, but which only take effect at process startup and
    cannot be applied by /reload. Distinct from skipped (ignored for reasons
    unrelated to restart) and needs_restart (reserved for MCP server definition
    changes)."""
```

Exact wording may be adjusted during implementation as long as it (a) states that
membership means "payload value differs from the running config but requires a
restart to apply," and (b) explicitly distinguishes the field from both `skipped`
and `needs_restart`, per the Plan's REQ-001 and AC-01.

## Compatibility considerations

- Docstring-only change on a dataclass field; no change to `ConfigReloadOutcome`'s
  field names, types, defaults, or `__init__` signature. No caller of
  `ConfigReloadOutcome` (`scripts/agent/commands/cmd_config.py`,
  `scripts/agent/services/config_reload.py` itself) needs any change.
- No config file format or CLI-visible output change — `cmd_config.py`'s rendering
  of `startup_only` (line 85-88) already distinguishes it from `skipped` and
  `needs_restart` today; this document does not touch that file.

## Security considerations

- N/A: no security-relevant logic changes. Adding a docstring has no runtime
  effect.

## Rollback considerations

- Single-file, single-attribute docstring addition. Revert via `git revert` of the
  implementing commit; no data migration, config schema change, or follow-up
  cleanup is needed.

## Validation plan

- Manual review: confirm `ConfigReloadOutcome.startup_only`'s new docstring states
  the same category of information (what puts a field in this bucket, how it
  differs from its sibling fields) at a level of detail comparable to `skipped`'s
  docstring (AC-01).
- `uv run ruff format scripts/agent/services/config_reload.py` and
  `uv run ruff check scripts/agent/services/config_reload.py` — confirm the new
  docstring introduces no formatting/lint violation.
- `uv run mypy scripts/agent/services/config_reload.py` — confirm no new type
  errors (docstring-only change, none expected).
- `uv run pytest tests/agent/services/test_config_reload.py
  tests/agent/commands/test_agent_cmd_config.py -v` — confirm no regressions (no
  behavior change).

## Completion criteria

- `ConfigReloadOutcome.startup_only` in `scripts/agent/services/config_reload.py`
  has a docstring, placed the same way as `skipped`'s docstring, that states (a)
  membership criterion (payload value differs from the running config but
  requires a restart to take effect) and (b) how it differs from `skipped` and
  `needs_restart`.
- `uv run ruff check scripts/agent/services/config_reload.py`,
  `uv run mypy scripts/agent/services/config_reload.py`, and the targeted
  `pytest` run above all pass with no new failures.

## Out of scope

- Any change to the `skipped`/`startup_only`/`needs_restart` classification logic
  (per Plan Scope).
- Any change to `scripts/agent/commands/cmd_config.py` — confirmed during
  adversarial review that it already labels the three fields distinctly; no
  renderer change is needed (per Plan Scope / Problem section).
- New automated tests — the Plan's own Tests section states manual review is
  sufficient for this documentation-only change; this document does not add one on
  its own initiative.
- `deploy/deploy.sh` changes — none needed (docstring-only change, no file
  added/removed/moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the docstring to `ConfigReloadOutcome.startup_only` per Details above (REQ-001) | Obsolete | — | — | Already implemented at config_reload.py:83-87 |
| 2 | Manual review: confirm docstring detail matches `skipped`'s (AC-01) | Obsolete | — | — | Prerequisite step already done |
| 3 | Run `ruff format`/`ruff check`/`mypy` on the target file | Obsolete | — | — | Prerequisite step already done |
| 4 | Run targeted `pytest` to confirm no regressions | Obsolete | — | — | Prerequisite step already done |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| All | Document describes work already implemented in source code | Yes | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (add descriptive docstring to `ConfigReloadOutcome.startup_only`)
- **Source issue**: `issues/20260825_cfgreload_outcome_skipped_startup_only_docs_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-104447
- **Related target files**: `scripts/agent/services/config_reload.py`
