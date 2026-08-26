## Goal

Add a descriptive docstring to `ConfigReloadOutcome.startup_only` matching the detail level of the existing `skipped` docstring, clarifying its meaning to operators and developers reading `/reload` output.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py:ConfigReloadOutcome.startup_only` — add docstring only.

**Out-of-Scope**:
- Changes to classification logic (`skipped`/`startup_only`/`needs_restart`).
- Changes to `/reload` command renderer (`scripts/agent/commands/cmd_config.py`) — confirmed it already labels all 3 fields distinctly (see Problem section).

## Assumptions

- `startup_only` contains fields that exist in the reload payload and differ from running values but require restart to take effect — distinct from `skipped` (ignored for non-restart reasons) and `needs_restart` (MCP server definition changes only).
- No new tests needed — this is a documentation-only change with no behavior impact.

## Design decisions

- Follow the existing `skipped` docstring format: multi-line, explains purpose and distinction from related fields.
- Place docstring immediately after the field declaration, indented at same level as the field line.

## Alternatives considered

- Single-line docstring: rejected because `skipped` uses multi-line format and consistency across fields is preferred.
- Inline comment on field: rejected because Python convention is to use docstrings on dataclass fields when they need explanation.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

#### Phase 1: Preparation

```python
# Verify: grep -n "startup.only\|STARTUP-ONLY" scripts/agent/commands/cmd_config.py
# Expected: confirms renderer already distinguishes 3 fields (confirmed above)
```

#### Phase 2: Core Logic

**Step A: Add docstring to `startup_only` field**

Current code (lines 84–85):
```python
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)
```

After change:
```python
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)
    """Fields present in the reload payload and differing from the running
    value but requiring a restart to take effect. Distinct from `skipped`,
    which ignores fields for reasons unrelated to restart requirement, and
    `needs_restart`, which is reserved exclusively for MCP server definition
    changes."""
```

#### Phase 3: Deployment & Verification

- Manual review: confirm `/reload` output still shows 3 distinct labels (already verified above).
- No `deploy.sh` impact — no config or schema changes.

### Details

- **Docstring content**: Matches REQ-001 specification exactly — clarifies that `startup_only` means "fields present in payload, different from running value, but requiring restart".
- **Distinction from `skipped`**: `skipped` = ignored for non-restart reasons (e.g., unrecognized keys); `startup_only` = specifically requires restart.
- **Distinction from `needs_restart`**: `needs_restart` = MCP server definition changes only; `startup_only` = broader category of restart-required config fields.
- **Indentation**: Docstring must be indented at column 4 (same as field declaration), consistent with PEP 257 conventions for inline docstrings on variable declarations.

## Compatibility considerations

- No API changes — docstring addition is invisible to runtime behavior.
- No config schema changes.
- No breaking changes to any consumers of `ConfigReloadOutcome`.

## Security considerations

- None — documentation-only change.

## Rollback considerations

- Revert: restore original field without docstring.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Manual review | Code review | `startup_only` docstring matches `skipped` clarity level |

## Completion criteria

- [ ] `startup_only` has a multi-line docstring explaining its meaning.
- [ ] Docstring clarifies distinction from both `skipped` and `needs_restart`.
- [ ] Docstring follows same formatting style as `skipped` docstring (multi-line, indented at column 4).
- [ ] No behavioral changes confirmed via manual `/reload` output inspection.

## Out of scope

- Changes to `validate_*` function contents.
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc.
- Adding new validation rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260825_cfgreload_outcome_skipped_startup_only_docs_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142349_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
