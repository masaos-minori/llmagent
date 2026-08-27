## Goal

Convert the advisory watchdog-removal note in
`docs/04_mcp_06_16_pre-production-fail-open-checklist.md` into an explicit,
mode-differentiated checklist requirement (REQ-003), per
`plans/20260826-114325_plan.md`.

## Scope

- In scope: the single checklist bullet noting the MCP watchdog removal (verified at
  line 28 as of 2026-08-27).
- Out of scope: any other checklist item in this document; any code change; creating
  actual systemd unit files (this Plan documents the requirement, does not ship a
  supervisor — see the Plan's own Out-of-Scope).

## Assumptions

- The MCP watchdog was removed 2026-07-16; recovery for subprocess-mode servers is
  reactive (`ensure_ready()` on next tool dispatch); persistent-mode servers get zero
  automatic recovery — all re-verified 2026-08-27 (see the sibling REQ-001/REQ-002
  implementation procedures in this same pass).
- The illustrative restart-policy example is systemd-style `Restart=`/`RestartSec=`,
  per this Plan's own Assumptions — naming a pattern, not mandating systemd
  specifically; operators may substitute an equivalent external process supervisor.

## Design decisions

- Rewrite the bullet from an informal "Note:" into an explicit checklist requirement
  differentiated by startup mode: REQUIRED for persistent-mode MCP servers (no
  fallback recovery exists at all) and RECOMMENDED as defense-in-depth for
  subprocess-mode servers (covers the idle-crash window before the next tool call
  triggers `ensure_ready()`).
- Include one concrete illustrative restart-policy example (systemd `Restart=`/
  `RestartSec=`) without mandating a specific tool — state the requirement is the
  *outcome* (an explicit restart policy exists), not the tool.
- This checklist remains advisory in character, same as every other item in the same
  document (a pre-production review list, not a runtime-enforced gate) — do not word
  it as a blocking/enforced check.

## Alternatives considered

- Splitting this into two separate checklist bullets (one for persistent-mode, one
  for subprocess-mode) was considered — either a single bullet with an internal
  REQUIRED/RECOMMENDED distinction or two separate bullets both satisfy REQ-003's
  Acceptance Criteria; keep as one bullet unless the surrounding checklist's existing
  item granularity (mostly single-line bullets per config key) makes a single
  combined bullet unusually long — check line length/readability against neighboring
  items before finalizing.

## Implementation
### Target file
`docs/04_mcp_06_16_pre-production-fail-open-checklist.md`

### Procedure
1. Locate the watchdog-removal note bullet (verified at line 28 as of 2026-08-27).
2. Rewrite it into an explicit checklist requirement per Method/Details.
3. Run `uv run python tools/check_docs_quality.py` and
   `uv run python tools/check_docs_structure.py
   docs/04_mcp_06_16_pre-production-fail-open-checklist.md`.

### Method
Direct text edit (Edit tool) on one checklist bullet; no restructuring of the
surrounding checklist.

### Details
Current bullet (verified 2026-08-27, line 28):
```
- [ ] Note: The MCP watchdog (automatic health polling + automatic restart loop)
      was removed on 2026-07-16. Recovery for crashed subprocess-mode MCP servers is
      limited to retry attempts via `ensure_ready()` during the next tool dispatch or
      manual restart of the agent process itself. Ensure external process monitoring
      (e.g., systemd) is set up for liveness monitoring and restarts.
```
Rewrite to state, as a checklist requirement (not a "Note:"): external process
supervision with a defined restart policy is REQUIRED for persistent-mode MCP
servers (no automatic recovery exists at all — see
`04_mcp_06_09_mcp-failure-diagnosis.md`'s `ensure_ready` section) and RECOMMENDED as
defense-in-depth for subprocess-mode servers (covers the idle-crash window before the
next tool call triggers `ensure_ready()`'s reactive recovery). Include one concrete
example, e.g. "a systemd unit with `Restart=on-failure` and `RestartSec=<N>`", while
stating the requirement is the outcome (an explicit restart policy), not a mandate
to use systemd specifically.

## Compatibility considerations

- Documentation-only; no code, config, or deployment artifact is created — this
  Plan explicitly excludes shipping actual systemd unit files.
- This checklist has always been advisory; the wording change to "REQUIRED"/
  "RECOMMENDED" does not introduce a new enforced gate — no code change accompanies
  this Plan.

## Security considerations

- N/A: this strengthens an existing operational-hygiene recommendation; it does not
  change or claim to change any enforced security control.

## Rollback considerations

- Single-bullet text revert via `git diff`/`git checkout -- <path>`; no other
  document or code depends on this exact wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` | Doc quality check | `uv run python tools/check_docs_quality.py` | Passes |
| `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` | Doc structure check | `uv run python tools/check_docs_structure.py docs/04_mcp_06_16_pre-production-fail-open-checklist.md` | Passes |

## Completion criteria

- The checklist item is phrased as a requirement, not an informal note.
- It states persistent-mode supervision is REQUIRED and subprocess-mode supervision
  is RECOMMENDED.
- It includes one concrete illustrative restart-policy example.

## Out of scope

- Any other checklist item in this document.
- Any code change.
- Creating actual systemd unit files or other service-unit definitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the watchdog-removal note into an explicit checklist requirement | Pending | — | — | |
| 2 | Run `check_docs_quality.py` and `check_docs_structure.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20260821_04_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-114325_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110529
- **Related target files**: `docs/04_mcp_06_16_pre-production-fail-open-checklist.md`
